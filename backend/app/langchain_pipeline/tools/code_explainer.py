import os
import json
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client()


def explain_code_vulnerability(vulnerability):
        
    prompt = f"""
    You are an application security expert specializing in static code analysis.

    Analyze this code vulnerability and provide:
    1. A detailed explanation of the security issue
    2. Why this code pattern is dangerous
    3. Potential attack scenarios
    4. Secure coding alternatives
    5. Prevention strategies

    Vulnerability Details:
    {json.dumps(vulnerability, indent=2)}

    Please provide actionable security guidance in plain text only. Do not use markdown formatting.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        vulnerability["ai_explanation"] = response.text
        print(f"[+] Enhanced code vulnerability: {vulnerability.get('check_id', 'Unknown')}")
        return {
            "status": "success",
            "vulnerability": vulnerability
        }
        
    except Exception as e:
        error_msg = f"AI explanation failed to generate. Error: {str(e)}"
        print(f"[!] Gemini Error for code vulnerability: {e}")
        return {
            "status": "failure",
            "error": error_msg,
            "vulnerability": {**vulnerability, "ai_explanation": error_msg}
        }

def format_code_vulnerabilities(semgrep_report):
    if not semgrep_report or "results" not in semgrep_report:
        return {
            "status": "failure",
            "error": "Invalid or empty Semgrep report",
            "formatted": []
        }

    formatted = []
    try:
        for issue in semgrep_report.get("results", []):
            vulnerability = {**issue, "ai_explanation": ""}
            
            result = explain_code_vulnerability(vulnerability)
            formatted.append(result["vulnerability"])
                
        return {
            "status": "success",
            "formatted": formatted
        }
    except Exception as e:
        return {
            "status": "failure",
            "error": f"Failed to format vulnerabilities: {str(e)}",
            "formatted": formatted
        }

def code_explainer(semgrep_report):
    format_result = format_code_vulnerabilities(semgrep_report)
    
    if format_result["status"] == "failure":
        return {
            "status": "failure",
            "error": format_result["error"],
            "code_vulnerabilities": format_result["formatted"],
            "summary": {
                "total_code_issues": 0
            }
        }
    
    formatted_code = format_result["formatted"]
    return {
        "status": "success",
        "code_vulnerabilities": formatted_code,
        "summary": {
            "total_code_issues": len(formatted_code)
        }
    }
  
    
def code_explainer_handler(code_scan_path: str):
    
    # get semgrep report from the provided path
    
    if not os.path.exists(code_scan_path):
        return {
            "status": "failure",
            "message": f"Code scan file not found at {code_scan_path}"
        }
        
    with open(code_scan_path, "r") as f:
        try:
            code_scan_data = json.load(f)
        except json.JSONDecodeError as e:
            return {
                "status": "failure",
                "message": f"Invalid JSON format in code scan file: {str(e)}"
            }
            
    if not isinstance(code_scan_data, dict):
        return {
            "status": "failure",
            "message": "Code scan data is not in the expected dictionary format."
        }
    
    # Run the code explainer
    
    results = code_explainer(code_scan_data)
    
    if results.get("status") == "failure":
        return {
            "status": "failure",
            "message": results.get("error", "An error occurred during the code explanation.")
        }
    
    reports_dir = "explain_reports"
    os.makedirs(reports_dir, exist_ok=True)
    filename = os.path.join(reports_dir, f"code_explain_results_{int(time.time())}.json")
    with open(filename, "w") as f:
        json.dump(results, f, indent=4)
        
    return {
        "status": results.get("status"),
        "message": f"Code Exaplanation completed. Results saved to {filename}"
    }