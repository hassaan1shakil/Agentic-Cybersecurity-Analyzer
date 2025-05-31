import os
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# === Configuration ===
FILE_PATH = "input/scan_result.json"
MODIFIED_FILE_PATH = "output/modified.json"
OVERALL_REPORT_PATH = "output/completeOverviewReport.txt"
ALL_REPORTS_DIR = "output"
GEMINI_MODEL = "gemini-2.0-flash"

# === Load environment and configure Gemini ===
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# === Function to simplify instances ===


def simplify_instances(json_input_path, json_output_path):
    with open(json_input_path, "r", encoding="utf-8") as infile:
        data = json.load(infile)

    for vulnerability in data:
        if "instances" in vulnerability:
            count = len(vulnerability["instances"])
            vulnerability["instances"] = f"{count} instance(s) affected"

    with open(json_output_path, "w", encoding="utf-8") as outfile:
        json.dump(data, outfile, indent=4, ensure_ascii=False)
    return data


# === Function to build single vulnerability prompt ===


def build_prompt_for_vulnerability(vuln):
    name = vuln.get("name", "Unknown Vulnerability")
    risk = vuln.get("risk", "N/A")
    description = vuln.get("description", "")
    solution = vuln.get("solution", "")
    references = vuln.get("references", [])
    tags = vuln.get("tags", {})
    common = vuln.get("common", {})
    instances = vuln.get("instances", [])

    reference_text = (
        "\n".join([f"- {ref}" for ref in references])
        if references
        else "No references provided."
    )
    tags_text = (
        "\n".join([f"{key}: {value}" for key, value in tags.items()])
        if tags
        else "No tags provided."
    )
    common_text = (
        "\n".join([f"{key}: {value}" for key, value in common.items()])
        if common
        else "No common metadata."
    )
    if isinstance(instances, list):
        if all(isinstance(i, dict) for i in instances):
            instance_list = "\n".join(
                [json.dumps(i, ensure_ascii=False) for i in instances]
            )
        else:
            instance_list = "\n".join(str(i) for i in instances)
    else:
        instance_list = str(instances)

    # instance_list = "\n".join(instances) if isinstance(
    #     instances, list) else str(instances)

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


# === Function to generate detailed reports for each vulnerability ===


def generate_vulnerability_insight_reports(json_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    with open(json_path, "r", encoding="utf-8") as f:
        vulnerabilities = json.load(f)

    model = genai.GenerativeModel(GEMINI_MODEL)

    for vuln in vulnerabilities:
        name = (
            vuln.get("name", "Unnamed_Vulnerability")
            .replace("/", "-")
            .replace("\\", "-")
        )
        prompt = build_prompt_for_vulnerability(vuln)

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.0,
                "top_p": 1.0,
                "top_k": 1,
                "max_output_tokens": 2048,
            },
        )

        clean_name = "".join(
            c for c in name if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        filename = os.path.join(output_dir, f"{clean_name}.txt")
        with open(filename, "w", encoding="utf-8") as outfile:
            outfile.write(response.text.strip())

        print(f"✔ Report created: {filename}")


# === Function to generate the overall summary ===


def generate_overall_summary(modified_data, output_path):
    model = genai.GenerativeModel(GEMINI_MODEL)

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

{json.dumps(modified_data, indent=2, ensure_ascii=False)}
"""
    response = model.generate_content(prompt)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response.text.strip())
    print(f"✔ Overall report created: {output_path}")


# === Run full process ===
if __name__ == "__main__":
    modified_data = simplify_instances(FILE_PATH, MODIFIED_FILE_PATH)
    generate_overall_summary(modified_data, OVERALL_REPORT_PATH)
    generate_vulnerability_insight_reports(FILE_PATH, ALL_REPORTS_DIR)
