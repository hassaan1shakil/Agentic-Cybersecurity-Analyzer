import json
import re
import os
import time
from collections import defaultdict
from google import generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# Configure Gemini API from environment variable
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError(
        "GEMINI_API_KEY environment variable not found. Please set it with: export GEMINI_API_KEY='your_api_key'"
    )

genai.configure(api_key=api_key)

# Configuration
INPUT_JSON = "vulnerabilities.json"
OUTPUT_JSON = "vulnerabilities_enriched.json"
VECTOR_STORE_DIR = "vectorstore"
MODEL_NAME = "gemini-2.0-flash-exp"
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"  # Upgraded model
TOP_K_RETRIEVED = 5  # Number of relevant chunks to retrieve


class RAGComplianceEnricher:
    def __init__(self):
        print("🔄 Loading vector store and embeddings...")
        # Load the same embeddings model used to create the vector store
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

        # Load the FAISS vector store
        self.vector_store = FAISS.load_local(
            VECTOR_STORE_DIR, self.embeddings, allow_dangerous_deserialization=True
        )

        # Initialize Gemini model
        self.model = genai.GenerativeModel(MODEL_NAME)
        print("✅ RAG system initialized successfully!")

    def retrieve_relevant_context(self, query: str) -> tuple[str, list]:
        """
        Retrieve relevant compliance documentation chunks based on vulnerability description
        Returns both context string and merged source information
        """
        try:
            # Perform similarity search to get relevant chunks
            relevant_docs = self.vector_store.similarity_search(
                query, k=TOP_K_RETRIEVED
            )

            # Group sources by file to merge chunk IDs
            sources_by_file = defaultdict(
                lambda: {"file_type": "unknown",
                         "chunk_ids": [], "previews": []}
            )

            context_parts = []

            for i, doc in enumerate(relevant_docs):
                # Get filename from metadata
                source_file = doc.metadata.get("source_file", "Unknown")
                file_type = doc.metadata.get("file_type", "unknown")
                chunk_id = doc.metadata.get("chunk_id", i)

                # Build context with source attribution
                context_part = f"Relevant Compliance Context {
                    i + 1} (from {source_file}):\n{doc.page_content}"
                context_parts.append(context_part)

                # Group by source file
                sources_by_file[source_file]["file_type"] = file_type
                sources_by_file[source_file]["chunk_ids"].append(chunk_id)

                # Add preview (keep only unique previews per file)
                preview = (
                    doc.page_content[:100] + "..."
                    if len(doc.page_content) > 100
                    else doc.page_content
                )
                if preview not in sources_by_file[source_file]["previews"]:
                    sources_by_file[source_file]["previews"].append(preview)

            # Convert grouped sources to final format
            merged_sources = []
            for source_file, info in sources_by_file.items():
                merged_sources.append(
                    {
                        "source_file": source_file,
                        "file_type": info["file_type"],
                        "chunk_ids": sorted(
                            list(set(info["chunk_ids"]))
                        ),  # Remove duplicates and sort
                        "previews": info["previews"],
                    }
                )

            context = "\n\n".join(context_parts)
            return context, merged_sources

        except Exception as e:
            print(f"⚠️ Error retrieving context: {e}")
            return "", []

    def get_top_compliance_violations(self, name: str, description: str) -> dict:
        """
        Use RAG to find compliance violations by retrieving relevant context first
        Returns both violations and merged source information
        """
        # Create search query from vulnerability info
        search_query = f"{name} {description}".strip()

        if not search_query:
            return {
                "violations": [
                    {
                        "regulation": "Unknown",
                        "reason": "No vulnerability information provided",
                    }
                ],
                "sources": [],
            }

        # Step 1: Retrieve relevant compliance context
        print(f"  🔍 Retrieving relevant compliance context...")
        context, sources = self.retrieve_relevant_context(search_query)

        # Display source files used with chunk counts
        if sources:
            source_info = []
            for source in sources:
                chunk_count = len(source["chunk_ids"])
                source_info.append(
                    f"{source['source_file']} ({chunk_count} chunks)")
            print(f"  📄 Found context in: {', '.join(source_info)}")

        # Step 2: Create enhanced prompt with retrieved context
        prompt = self._create_rag_prompt(name, description, context)

        # Step 3: Generate response using Gemini with retry logic
        return self._call_gemini_with_retry(prompt, sources)

    def _call_gemini_with_retry(
        self, prompt: str, sources: list, max_retries: int = 3
    ) -> dict:
        """
        Call Gemini API with retry logic for rate limit handling
        """
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                content = response.text

                # Try to extract JSON array from response
                match = re.search(r"\[\s*\{.*?\}\s*\]", content, re.DOTALL)
                if match:
                    try:
                        violations = json.loads(match.group())
                        return {"violations": violations, "sources": sources}
                    except json.JSONDecodeError:
                        pass

                # Fallback: wrap full reply
                return {
                    "violations": [
                        {"regulation": "Retrieved Context",
                            "reason": content.strip()}
                    ],
                    "sources": sources,
                }

            except Exception as e:
                error_msg = str(e)

                # Check if it's a rate limit error (429)
                if (
                    "429" in error_msg
                    or "quota" in error_msg.lower()
                    or "rate limit" in error_msg.lower()
                ):
                    # Extract retry delay from error message
                    retry_delay = self._extract_retry_delay(error_msg)

                    if attempt < max_retries - 1:  # Don't wait on the last attempt
                        print(
                            f"  ⏳ Rate limit hit (attempt {
                                attempt + 1}/{max_retries}). Waiting {retry_delay} seconds..."
                        )
                        time.sleep(retry_delay)
                        continue
                    else:
                        print(f"  ❌ Rate limit exceeded after {
                              max_retries} attempts")
                        return {
                            "violations": [
                                {
                                    "regulation": "Rate Limit Error",
                                    "reason": f"API rate limit exceeded after {max_retries} attempts",
                                }
                            ],
                            "sources": sources,
                        }
                else:
                    # Non-rate-limit error, don't retry
                    print(f"  ❌ Error calling Gemini API: {e}")
                    return {
                        "violations": [
                            {
                                "regulation": "Error",
                                "reason": f"API call failed: {str(e)}",
                            }
                        ],
                        "sources": sources,
                    }

        # This shouldn't be reached, but just in case
        return {
            "violations": [{"regulation": "Error", "reason": "Max retries exceeded"}],
            "sources": sources,
        }

    def _extract_retry_delay(self, error_msg: str) -> int:
        """
        Extract retry delay from Gemini API error message
        """
        try:
            # Look for retry_delay { seconds: X } pattern
            match = re.search(
                r"retry_delay\s*\{\s*seconds:\s*(\d+)", error_msg)
            if match:
                delay = int(match.group(1))
                # Add 2 second buffer, max 60 seconds
                return min(delay + 2, 60)

            # Look for other common patterns
            match = re.search(r"retry after (\d+) seconds",
                              error_msg, re.IGNORECASE)
            if match:
                return int(match.group(1)) + 2

        except (ValueError, AttributeError):
            pass

        # Default fallback delays based on attempt
        return 30  # Default 30 seconds for rate limits

    def _create_rag_prompt(self, name: str, description: str, context: str) -> str:
        """
        Create a RAG-enhanced prompt with retrieved compliance context
        """
        prompt = f"""You are a cybersecurity compliance expert. Based on the retrieved compliance documentation context below, analyze the given vulnerability and identify the top {TOP_K_RETRIEVED} compliance regulations or standards that this vulnerability most likely violates.

RETRIEVED COMPLIANCE CONTEXT:
{context}

VULNERABILITY TO ANALYZE:
Name: {name}
Description: {description}

INSTRUCTIONS:
1. Use the retrieved compliance context above to identify relevant regulations
2. Focus on the most specific and applicable compliance requirements
3. Consider standards like OWASP ASVS, NIST 800-53, CIS Benchmarks, PCI DSS, etc.
4. Return your answer as a JSON array of objects with keys 'regulation' and 'reason'
5. Make sure the 'reason' explains how the vulnerability specifically violates the regulation

Example format:
[
    {{"regulation": "OWASP ASVS V5.1.1",
        "reason": "Fails input validation requirements..."}},
    {{"regulation": "NIST 800-53 SI-10",
        "reason": "Does not implement proper information input validation..."}},
    {{"regulation": "CIS Control 16.1",
        "reason": "Lacks application software security controls..."}}
]

JSON Response:"""

        return prompt


def enrich_vulnerabilities(data: dict, rag_enricher: RAGComplianceEnricher) -> dict:
    """
    Enrich vulnerability data using RAG-based compliance analysis
    """
    total_vulnerabilities = 0
    processed = 0

    for section in ("web_vulnerabilities", "code_vulnerabilities"):
        if section not in data:
            continue

        vulnerabilities = data.get(section, [])
        total_vulnerabilities += len(vulnerabilities)

        for vuln in vulnerabilities:
            identifier = vuln.get("name") or vuln.get("check_id", "<unnamed>")
            print(
                f"→ [{processed + 1}/{total_vulnerabilities}] Enriching {identifier!r}..."
            )

            name = vuln.get("name", "")
            desc = vuln.get("description", "") or vuln.get("extra", {}).get(
                "message", ""
            )

            # Skip if no meaningful content
            if not name and not desc:
                print(f"  ⚠️ Skipping - no name or description")
                vuln["top_compliance_violations"] = []
                processed += 1
                continue

            # Use RAG to get compliance violations
            result = rag_enricher.get_top_compliance_violations(name, desc)
            violations = result["violations"]
            sources = result["sources"]

            # Store both violations and merged source information
            vuln["top_compliance_violations"] = violations

            # Create the merged compliance_sources format you requested
            compliance_sources = []
            for source in sources:
                source_entry = {
                    "source_file": source["source_file"],
                    "file_type": source["file_type"],
                    "chunk_ids": source["chunk_ids"],
                }
                compliance_sources.append(source_entry)

            vuln["compliance_sources"] = compliance_sources

            processed += 1

            # Enhanced logging with chunk information
            total_chunks = sum(len(source["chunk_ids"]) for source in sources)
            unique_files = len(set(source["source_file"]
                               for source in sources))
            print(
                f"  ✅ Added {len(violations)} compliance violations from {
                    unique_files} source files ({total_chunks} total chunks)"
            )

    return data


def main():
    try:
        # Initialize RAG system
        rag_enricher = RAGComplianceEnricher()

        print("⏳ Loading input JSON...")
        with open(INPUT_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        print("🤖 Using RAG to enrich vulnerabilities with compliance context...")
        enriched = enrich_vulnerabilities(data, rag_enricher)

        print(f"💾 Writing enriched data to {OUTPUT_JSON}...")
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(enriched, f, indent=4, ensure_ascii=False)

        print("✅ RAG-enhanced vulnerability enrichment completed!")

    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
        print("Make sure you have:")
        print(f"  - {INPUT_JSON} (vulnerability data)")
        print(f"  - {VECTOR_STORE_DIR}/ (FAISS vector store)")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
