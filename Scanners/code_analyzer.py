import json
import subprocess
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.0-flash")

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".java", ".go", ".c", ".cpp", ".rb", ".php"
}

def get_supported_files(code_path):
    files = []
    for root, _, filenames in os.walk(code_path):
        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext in SUPPORTED_EXTENSIONS:
                files.append(os.path.join(root, filename))
    return files

def analyze_code_with_semgrep(code_path):
    files_to_scan = get_supported_files(code_path)
    if not files_to_scan:
        print("[!] No supported source code files found.")
        return {}

    try:
        result = subprocess.run([
            "semgrep", "--config", "p/default", "--json", *files_to_scan
        ], capture_output=True, text=True)

        semgrep_output = json.loads(result.stdout)

        for issue in semgrep_output.get("results", []):
            issue["vulnerable_line"] = issue.get("start", {}).get("line", None)
            issue["code_snippet"] = issue.get("extra", {}).get("lines", "").strip()
            file_path = issue.get("path", "")
            start_offset = issue.get("start", {}).get("offset", None)
            end_offset = issue.get("end", {}).get("offset", None)

            if start_offset is not None and end_offset is not None and os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        full_content = f.read()
                        exact_snippet = full_content[start_offset:end_offset].strip()
                        issue["exact_snippet"] = exact_snippet
                except Exception as e:
                    print(f"[!] Failed to extract exact snippet from {file_path}: {e}")
                    issue["exact_snippet"] = issue["code_snippet"]
            else:
                issue["exact_snippet"] = issue["code_snippet"]

        print(f"[+] Semgrep scan completed. {len(semgrep_output.get('results', []))} issues found.")
        return semgrep_output

    except Exception as e:
        print("[!] Semgrep scan failed:", e)
        return {}


def enhance_with_gemini(issues):
    enhanced = []
    for issue in issues:
        file = issue.get("path", "Unknown")
        line = issue.get("start", {}).get("line", "Unknown")
        message = issue.get("extra", {}).get("message", "")
        snippet = issue.get("extra", {}).get("lines", "")

        prompt = (
            "You are a cybersecurity analyst. Analyze and explain the vulnerability "
            "in the following source code. Do not use markdown or bullet points. "
            "Only respond in plain text.\n\n"
            f"File: {file}\n"
            f"Line: {line}\n"
            f"Code Snippet:\n{snippet}\n\n"
            f"Message: {message}\n\n"
            "Explain the vulnerability and how to fix it."
        )

        try:
            response = model.generate_content(prompt)
            explanation = response.text.strip()
        except Exception as e:
            explanation = "Model failed to analyze this vulnerability."
            print("[!] Model error:", e)

        issue["explanation"] = explanation
        enhanced.append(issue)

    return enhanced