from Agents.scanAgent import ScanAgent
from Agents.explainAgent import ExplainAgent
import os

def clear_directory(directory_path):
    if not os.path.exists(directory_path):
        print(f"[!] Directory does not exist: {directory_path}")
        return

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"[+] Deleted: {file_path}")
        except Exception as e:
            print(f"[!] Failed to delete {file_path}: {e}")

clear_directory("Reports")

url = "https://juice-shop.herokuapp.com/#/"
url=None
code_path = "/home/pola-k/Downloads/ai-hackathon-creed-master/Vulnerable Files/"      

print("\n=== Step 1: Running Scans ===")
scanner = ScanAgent(url=url, code_path=code_path)
scan_results = scanner.run_all()

print("\n=== Step 2: Explaining Vulnerabilities ===")
explainer = ExplainAgent()
combined_report = explainer.create_combined_report()

print("\n=== Done ===")
print(f"Total Web Issues Found: {combined_report['summary']['total_web_issues']}")
print(f"Total Code Issues Found: {combined_report['summary']['total_code_issues']}")
print("Combined report saved to 'reports/combined_report.json'")