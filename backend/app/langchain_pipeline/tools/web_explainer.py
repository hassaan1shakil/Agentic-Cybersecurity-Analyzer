import os
import json
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client()

def explain_web_vulnerability(vulnerability):
    prompt = f"""
    You are a cybersecurity expert specializing in web application vulnerabilities.
    
    Analyze this web vulnerability and provide:
    1. A clear explanation of what this vulnerability means
    2. The potential impact and risks
    3. Step-by-step remediation guidance
    4. Best practices to prevent this in the future
    
    Vulnerability Details:
    {json.dumps(vulnerability, indent=2)}
    
    
    Please provide the output in plain text. Do not use any markdown formatting.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        vulnerability["ai_explanation"] = response.text
        print(f"[+] Enhanced web vulnerability: {vulnerability.get('name', 'Unknown')}")
        return {
            "status": "success",
            "vulnerability": vulnerability
        }
        
    except Exception as e:
        error_msg = f"AI explanation failed to generate. Error: {str(e)}"
        print(f"[!] Gemini Error for web vulnerability: {e}")
        return {
            "status": "failure",
            "error": error_msg,
            "vulnerability": {**vulnerability, "ai_explanation": error_msg}
        }

def format_web_vulnerabilities(zap_report):
    if not zap_report or "results" not in zap_report:
        return {
            "status": "failure",
            "error": "Invalid or empty ZAP report",
            "formatted": []
        }

    formatted = []
    try:
        for alert in zap_report.get("results", []):
            vulnerability = dict(alert)
            if "ai_explanation" not in vulnerability:
                vulnerability["ai_explanation"] = ""

            result = explain_web_vulnerability(vulnerability)
            formatted.append(result["vulnerability"])
        
        return {
            "status": "success",
            "formatted": formatted
        }
    
    except Exception as e:
        return {
            "status": "failure",
            "error": f"Failed to format web vulnerabilities: {str(e)}",
            "formatted": formatted
        }

def web_explainer(zap_report):
    
    format_result = format_web_vulnerabilities(zap_report)
    
    if format_result["status"] == "failure":
        return {
            "status": "failure",
            "error": format_result["error"],
            "web_vulnerabilities": format_result["formatted"],
            "summary": {
                "total_web_issues": 0
            }
        }
    
    formatted_web = format_result["formatted"]
    return {
        "status": "success",
        "web_vulnerabilities": formatted_web,
        "summary": {
            "total_web_issues": len(formatted_web)
        }
    }

def web_explainer_handler(web_scan_path: str):
    
    # Check if file exists
    
    if not os.path.exists(web_scan_path):
        return {
            "status": "failure",
            "message": f"Web scan file not found at {web_scan_path}"
        }
    
    try:
        with open(web_scan_path, "r") as f:
            web_scan_data = json.load(f)
    except json.JSONDecodeError as e:
        return {
            "status": "failure",
            "message": f"Invalid JSON format in web scan file: {str(e)}"
        }
    
    if not isinstance(web_scan_data, dict):
        return {
            "status": "failure",
            "message": "Web scan data is not in the expected dictionary format."
        }
    
    # Run the web explainer
    results = web_explainer(web_scan_data)
    
    if results.get("status") == "failure":
        return {
            "status": "failure",
            "message": results.get("error", "An error occurred during the web vulnerability explanation.")
        }
    
    reports_dir = "explain_reports"
    os.makedirs(reports_dir, exist_ok=True)
    filename = os.path.join(reports_dir, f"web_explain_results_{int(time.time())}.json")
    
    with open(filename, "w") as f:
        json.dump(results, f, indent=4)
    
    return {
        "status": "success",
        "message": f"Web Vulnerability Explanation completed. Results saved to {filename}"
    }