import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

# Paths
SOURCE_DIR = "docs"
VECTOR_STORE_DIR = "vectorstore"

# 1. Load all documents with enhanced metadata
def load_documents(source_dir):
    documents = []
    for file in os.listdir(source_dir):
        file_path = os.path.join(source_dir, file)
        filename = file  # Store original filename
        
        if file.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file.endswith(".txt"):
            loader = TextLoader(file_path)
        else:
            continue
        
        # Load documents from this file
        file_docs = loader.load()
        
        # Add filename metadata to each document from this file
        for doc in file_docs:
            # Enhance metadata with filename and file info
            doc.metadata.update({
                'source_file': filename,
                'file_path': file_path,
                'file_type': file.split('.')[-1].lower(),
                'original_source': doc.metadata.get('source', file_path)  # Keep existing source if present
            })
        
        documents.extend(file_docs)
        print(f"✅ Loaded {len(file_docs)} pages from {filename}")
    
    return documents

# 2. Split into chunks while preserving metadata
def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, 
        chunk_overlap=100,
        # This ensures metadata is preserved during splitting
        add_start_index=True
    )
    
    chunks = splitter.split_documents(documents)
    
    # Add chunk-specific metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata.update({
            'chunk_id': i,
            'chunk_size': len(chunk.page_content)
        })
    
    return chunks

# 3. Embed and store in FAISS with metadata
def store_embeddings(chunks):
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5")
    
    # Create FAISS vector store - metadata is automatically preserved
    db = FAISS.from_documents(chunks, embeddings)
    
    # Save the vector store
    db.save_local(VECTOR_STORE_DIR)
    
    # Optional: Print some metadata samples
    print(f"\n📋 Sample metadata from chunks:")
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        print(f"Chunk {i}: {chunk.metadata}")

# 4. Utility function to inspect stored metadata
def inspect_vector_store():
    """Load and inspect the vector store metadata"""
    try:
        embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5")
        db = FAISS.load_local(
            VECTOR_STORE_DIR, 
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        # Test search to see metadata
        test_results = db.similarity_search("security", k=3)
        
        print("\n🔍 Sample search results with metadata:")
        for i, doc in enumerate(test_results):
            print(f"\nResult {i+1}:")
            print(f"Source File: {doc.metadata.get('source_file', 'Unknown')}")
            print(f"File Type: {doc.metadata.get('file_type', 'Unknown')}")
            print(f"Chunk ID: {doc.metadata.get('chunk_id', 'Unknown')}")
            print(f"Content Preview: {doc.page_content[:100]}...")
            
    except Exception as e:
        print(f"❌ Error inspecting vector store: {e}")

if __name__ == "__main__":
    print("📁 Loading documents with filename metadata...")
    docs = load_documents(SOURCE_DIR)
    print(f"📄 Loaded {len(docs)} total document pages.")
    
    print("\n✂️ Splitting into chunks...")
    chunks = split_documents(docs)
    print(f"🧩 Generated {len(chunks)} chunks.")
    
    print("\n🔢 Storing embeddings in FAISS with metadata...")
    store_embeddings(chunks)
    print(f"💾 Vector store saved to '{VECTOR_STORE_DIR}'")
    
    print("\n🔍 Inspecting stored metadata...")
    inspect_vector_store()
    
    print("\n✅ Complete! Your vector store now includes filename metadata.")