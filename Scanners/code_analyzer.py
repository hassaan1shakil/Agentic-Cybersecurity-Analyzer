import json
import subprocess
import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_code_with_semgrep(code_path):
    try:
        result = subprocess.run([
            "semgrep", "--config", "p/default", code_path, "--json"
        ], capture_output=True, text=True)
        return json.loads(result.stdout)
    except Exception as e:
        print("[!] Semgrep scan failed:", e)
        return {}

def enhance_with_gpt(semgrep_report):
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
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a secure code expert."},
                    {"role": "user", "content": prompt}
                ]
            )
            explanation = response["choices"][0]["message"]["content"]
        except Exception as e:
            explanation = "GPT explanation failed."
            print("[!] GPT Error:", e)

        issue["explanation"] = explanation
    return semgrep_report
