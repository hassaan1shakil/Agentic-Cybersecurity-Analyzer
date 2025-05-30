import json
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class ExplainAgent:
    def __init__(self, web_report_path="Reports/web_report.json", code_report_path="Reports/code_report.json"):
        self.web_report_path = web_report_path
        self.code_report_path = code_report_path
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash")
            print("[+] Gemini AI initialized successfully")
        else:
            print("[!] GEMINI_API_KEY not found. AI explanations will be disabled.")
            self.model = None

    def load_report(self, path):
        if not os.path.exists(path):
            print(f"[!] Report not found: {path}. Skipping...")
            return []
        try:
            with open(path, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"[!] Failed to load report from {path}: {e}")
            return []

    def enhance_web_vulnerability_with_gemini(self, vulnerability):
        if not self.model:
            return vulnerability
            
        prompt = f"""
        You are a cybersecurity expert specializing in web application vulnerabilities.
        
        Analyze this web vulnerability and provide:
        1. A clear explanation of what this vulnerability means
        2. The potential impact and risks
        3. Step-by-step remediation guidance
        4. Best practices to prevent this in the future
        
        Vulnerability Details:
        {json.dumps(vulnerability, indent=2)}
        
        Please provide a comprehensive but concise analysis in markdown format.
        """
        
        try:
            response = self.model.generate_content(prompt)
            vulnerability["ai_explanation"] = response.text
            print(f"[+] Enhanced web vulnerability: {vulnerability.get('alert', 'Unknown')}")
        except Exception as e:
            vulnerability["ai_explanation"] = f"AI explanation failed to generate. Error: {str(e)}"
            print(f"[!] Gemini Error for web vulnerability: {e}")
        
        return vulnerability

    def enhance_code_vulnerability_with_gemini(self, vulnerability):
        if not self.model:
            return vulnerability
            
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
        
        Please provide actionable security guidance in markdown format.
        """
        
        try:
            response = self.model.generate_content(prompt)
            vulnerability["ai_explanation"] = response.text
            print(f"[+] Enhanced code vulnerability: {vulnerability.get('check_id', 'Unknown')}")
        except Exception as e:
            vulnerability["ai_explanation"] = f"AI explanation failed to generate. Error: {str(e)}"
            print(f"[!] Gemini Error for code vulnerability: {e}")
        
        return vulnerability

    def format_web_vulnerabilities(self, web_alerts):
        formatted = []
        for alert in web_alerts:
            vulnerability = dict(alert)
            
            if "ai_explanation" not in vulnerability:
                vulnerability["ai_explanation"] = ""

            vulnerability = self.enhance_web_vulnerability_with_gemini(vulnerability)
            formatted.append(vulnerability)
        
        return formatted

    def format_code_vulnerabilities(self, semgrep_report):
        formatted = []
        for issue in semgrep_report.get("results", []):
            vulnerability = {
                **issue,
                "ai_explanation": ""
            }

            vulnerability = self.enhance_code_vulnerability_with_gemini(vulnerability)
            formatted.append(vulnerability)
        
        return formatted

    def create_combined_report(self):
        print("[+] Generating AI-enhanced vulnerability report...")

        web_data = self.load_report(self.web_report_path)
        code_data = self.load_report(self.code_report_path)

        print("[+] Processing web vulnerabilities...")
        formatted_web = self.format_web_vulnerabilities(web_data) if web_data else []
        
        print("[+] Processing code vulnerabilities...")
        formatted_code = self.format_code_vulnerabilities(code_data) if code_data else []

        combined = {
            "web_vulnerabilities": formatted_web,
            "code_vulnerabilities": formatted_code,
            "summary": {
                "total_web_issues": len(formatted_web),
                "total_code_issues": len(formatted_code)
            }
        }

        with open("Reports/combined_report.json", "w") as f:
            json.dump(combined, f, indent=4)

        print(f"[+] Enhanced report saved with {len(formatted_web)} web and {len(formatted_code)} code vulnerabilities")
        return combined