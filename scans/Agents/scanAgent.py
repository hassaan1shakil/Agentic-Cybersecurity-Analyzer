import os
import json
from Scanners.web_scanner import zap_scan, format_web_scan_results
from Scanners.code_analyzer import analyze_code_with_semgrep, enhance_with_gemini

class ScanAgent:
    def __init__(self, url=None, code_path=None, web_file = "Reports/web_report.json", code_file = "Reports/code_report.json"):
        self.url = url
        self.code_path = code_path
        self.web_file = web_file
        self.code_file = code_file

    def run_web_scan(self):
        if not self.url:
            print("[!] No URL provided. Skipping web scan.")
            return None
        print("[+] Running ZAP Web Scan...")
        report = zap_scan(self.url)
        report = format_web_scan_results(report)
        with open(self.output_file, "w") as f:
            json.dump(report, f, indent=4)
        return report

    def run_code_scan(self):
        if not self.code_path:
            print("[!] No code path provided. Skipping code scan.")
            return None
        print("[+] Running Semgrep Code Analysis...")
        raw_report = analyze_code_with_semgrep(self.code_path)
        enhanced_results = enhance_with_gemini(raw_report.get("results", []))
        
        enhanced_report = {
            "results": enhanced_results,
            "errors": raw_report.get("errors", []),
            "paths": raw_report.get("paths", {}),
            "version": raw_report.get("version", "")
        }
        
        with open(self.code_file, "w") as f:
            json.dump(enhanced_report, f, indent=4)
        return enhanced_report

    def run_all(self):
        return {
            "web": self.run_web_scan(),
            "code": self.run_code_scan()
        }
