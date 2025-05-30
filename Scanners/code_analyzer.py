import json
import subprocess
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.0-flash")

def analyze_code_with_semgrep(code_path):
    try:
        result = subprocess.run([
            "semgrep", "--config", "p/default", code_path, "--json"
        ], capture_output=True, text=True)
        return json.loads(result.stdout)
    except Exception as e:
        print("[!] Semgrep scan failed:", e)
        return {}

def enhance_with_gemini(semgrep_report):
    for issue in semgrep_report.get("results", []):
        message = issue["extra"].get("message", "")
        code_snippet = issue.get("extra", {}).get("lines", "")
        file_path = issue.get("path", "")

        prompt = f"""
        You are an application security expert.
        Analyze the following code snippet and explain the security vulnerability:

        File: {file_path}
        Code:
        {code_snippet}

        Message:
        {message}
        """

        try:
            response = model.generate_content(prompt)
            explanation = response.text
        except Exception as e:
            explanation = "Gemini explanation failed."
            print("[!] Gemini Error:", e)

        issue["explanation"] = explanation
    return semgrep_report
