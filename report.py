import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# === Urdu Translation Class ===


class UrduReportTranslator:
    def __init__(self, model, input_dir, output_dir):
        self.model = model
        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def translate_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            english_text = f.read()

        # Gemini prompt
        prompt = f"""
Translate the following text into very simple and easy-to-understand Urdu.

Instructions:
- Do not include links, references, or vulnerability names.
- Just convert the explanation part into natural, simplified Urdu.
- Avoid technical jargon and keep the tone friendly and easy for non-experts.

Text to translate:
{english_text}
"""
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def translate_all_reports(self):
        for filename in os.listdir(self.input_dir):
            if filename.endswith(".txt") and filename != "completeOverviewReport.txt":
                input_path = os.path.join(self.input_dir, filename)
                translated_text = self.translate_file(input_path)

                output_path = os.path.join(
                    self.output_dir, f"urdu_{filename}")
                with open(output_path, "w", encoding='utf-8') as f:
                    f.write(translated_text)
                print(f"✔ Urdu translation created: {output_path}")


class VulnerabilityReportAgent:
    def __init__(self, input_path, output_dir, model_name="gemini-2.0-flash"):
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment.")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

        self.input_path = input_path
        self.output_dir = Path(output_dir)
        self.modified_json_path = self.output_dir / "modified.json"
        self.overview_path = self.output_dir / "completeOverviewReport.txt"

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def simplify_instances(self):
        with open(self.input_path, 'r', encoding='utf-8') as infile:
            data = json.load(infile)

        for vuln in data:
            if 'instances' in vuln:
                count = len(vuln['instances'])
                vuln['instances'] = f"{count} instance(s) affected"

        with open(self.modified_json_path, 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, indent=4, ensure_ascii=False)
        return data

    def generate_summary_report(self, simplified_data):
        prompt = f"""
You are a cybersecurity analyst specializing in summarizing structured scan data for voice-based reporting.

Your task is to convert a list of vulnerabilities, provided in JSON format, into clear, concise paragraphs. These paragraphs must be easy to transcribe with a text-to-speech engine and free from technical clutter or unnecessary storytelling.

Guidelines:
- Use complete sentences.
- Each vulnerability must be summarized in a single paragraph.
- Begin with the vulnerability's name and risk level.
- Briefly explain the issue using the \"description\".
- If a solution exists, include it clearly.
- Summarize relevant tags, like CWE or OWASP IDs, as part of the explanation.
- Mention how many instances were affected using the instance count.
- Adapt to missing fields gracefully — some sources may lack certain tags or structure.
- Do not output markdown, code blocks, quotes, symbols, or lists — output should be plain readable text only.

Here is the vulnerability data to summarize:

{json.dumps(simplified_data, indent=2, ensure_ascii=False)}
"""
        response = self.model.generate_content(prompt)
        with open(self.overview_path, "w", encoding='utf-8') as f:
            f.write(response.text.strip())
        print(f"✔ Overall report created: {self.overview_path}")

    def generate_detailed_reports(self):
        with open(self.input_path, 'r', encoding='utf-8') as f:
            vulnerabilities = json.load(f)

        for vuln in vulnerabilities:
            name = vuln.get("name", "Unnamed_Vulnerability").replace(
                "/", "-").replace("\\", "-")
            prompt = self._build_vulnerability_prompt(vuln)

            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "top_k": 1,
                    "max_output_tokens": 2048
                }
            )

            clean_name = "".join(c for c in name if c.isalnum()
                                 or c in (' ', '-', '_')).rstrip()
            filename = self.output_dir / f"{clean_name}.txt"
            with open(filename, "w", encoding="utf-8") as outfile:
                outfile.write(response.text.strip())

            print(f"✔ Report created: {filename}")

    def _build_vulnerability_prompt(self, vuln):
        name = vuln.get("name", "Unknown Vulnerability")
        risk = vuln.get("risk", "N/A")
        description = vuln.get("description", "")
        solution = vuln.get("solution", "")
        references = vuln.get("references", [])
        tags = vuln.get("tags", {})
        common = vuln.get("common", {})
        instances = vuln.get("instances", [])

        reference_text = "\n".join(
            f"- {ref}" for ref in references) if references else "No references provided."
        tags_text = "\n".join(f"{key}: {value}" for key, value in tags.items(
        )) if tags else "No tags provided."
        common_text = "\n".join(f"{key}: {value}" for key, value in common.items(
        )) if common else "No common metadata."

        if isinstance(instances, list):
            if all(isinstance(i, dict) for i in instances):
                instance_list = "\n".join(json.dumps(
                    i, ensure_ascii=False) for i in instances)
            else:
                instance_list = "\n".join(str(i) for i in instances)
        else:
            instance_list = str(instances)

        prompt = f"""
IMPORTANT INSTRUCTION:
Do NOT use any markdown formatting, symbols, or characters (e.g., *, #, -, `, [], (), etc.).
Write everything in plain, natural language. Do not include bullet points, numbered lists, or code blocks.
Your output will be spoken using a Text-to-Speech engine.

You are a cybersecurity analyst writing an explanatory report for the following vulnerability.

Explain this in well-structured paragraphs using all the data provided. You must:
- Describe the risk level, real-world impact, and current scenario relevance.
- Include and explain every tag and field provided.
- Elaborate on how each reference is useful.
- List all the exact instance paths/URLs where this issue occurred.
- Use plain language and avoid repeating the vulnerability name excessively.

Vulnerability Name: {name}
Risk Level: {risk}
Description: {description}
Suggested Fix: {solution}

References:
{reference_text}

Tags:
{tags_text}

Common Metadata:
{common_text}

Instances Found:
{instance_list}

Write the analysis now.
"""
        return prompt


if __name__ == "__main__":
    agent = VulnerabilityReportAgent(
        input_path="../report/scan_result.json",
        output_dir="output",
        model_name="gemini-2.0-flash"
    )

    simplified_data = agent.simplify_instances()
    agent.generate_summary_report(simplified_data)
    agent.generate_detailed_reports()
    translator = UrduReportTranslator(
        genai.GenerativeModel("gemini-2.0-flash"),
        input_dir="output",
        output_dir=os.path.join("output", "urdu_reports")
    )
    translator.translate_all_reports()
