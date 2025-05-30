import json
import os

class ExplainAgent:
    def __init__(self, web_report_path="reports/web_report.json", code_report_path="reports/code_report.json"):
        self.web_report_path = web_report_path
        self.code_report_path = code_report_path

    def load_report(self, path):
        if not os.path.exists(path):
            print(f"[!] Report not found: {path}. Skipping...")
            return {}
        try:
            with open(path, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"[!] Failed to load report from {path}: {e}")
            return {}

    def format_web_vulnerabilities(self, web_alerts):
        formatted = []
        for alert in web_alerts:
            formatted.append({
                "type": alert.get("alert", "Unknown"),
                "risk": alert.get("risk", "N/A"),
                "description": alert.get("description", ""),
                "url": alert.get("url", ""),
                "evidence": alert.get("evidence", ""),
                "solution": alert.get("solution", "")
            })
        return formatted

    def format_code_vulnerabilities(self, semgrep_report):
        formatted = []
        for issue in semgrep_report.get("results", []):
            formatted.append({
                "check_id": issue.get("check_id", ""),
                "file": issue.get("path", ""),
                "line": issue.get("start", {}).get("line", ""),
                "message": issue.get("extra", {}).get("message", ""),
                "code": issue.get("extra", {}).get("lines", ""),
                "severity": issue.get("extra", {}).get("severity", ""),
                "explanation": issue.get("explanation", "")
            })
        return formatted

    def create_combined_report(self):
        print("[+] Generating combined vulnerability report...")
        web_data = self.load_report(self.web_report_path)
        code_data = self.load_report(self.code_report_path)

        formatted_web = self.format_web_vulnerabilities(web_data) if web_data else []
        formatted_code = self.format_code_vulnerabilities(code_data) if code_data else []

        combined = {
            "web_vulnerabilities": formatted_web,
            "code_vulnerabilities": formatted_code,
            "summary": {
                "total_web_issues": len(formatted_web),
                "total_code_issues": len(formatted_code)
            }
        }

        with open("reports/combined_report.json", "w") as f:
            json.dump(combined, f, indent=4)

        return combined
