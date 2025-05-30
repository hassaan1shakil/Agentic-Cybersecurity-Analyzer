import os
import json
from Scanners.web_scanner import zap_scan
from Scanners.code_analyzer import analyze_code_with_semgrep, enhance_with_gemini

class ScanAgent:
    def __init__(self, url=None, code_path=None):
        self.url = url
        self.code_path = code_path

    def run_web_scan(self):
        if not self.url:
            print("[!] No URL provided. Skipping web scan.")
            return None
        print("[+] Running ZAP Web Scan...")
        report = zap_scan(self.url)
        with open("Reports/web_report.json", "w") as f:
            json.dump(report, f, indent=4)
        return report

    def run_code_scan(self):
        if not self.code_path:
            print("[!] No code path provided. Skipping code scan.")
            return None
        print("[+] Running Semgrep Code Analysis...")
        raw_report = analyze_code_with_semgrep(self.code_path)
        enhanced_report = enhance_with_gemini(raw_report)
        with open("Reports/code_report.json", "w") as f:
            json.dump(enhanced_report, f, indent=4)
        return enhanced_report

    def run_all(self):
        return {
            "web": self.run_web_scan(),
            "code": self.run_code_scan()
        }
