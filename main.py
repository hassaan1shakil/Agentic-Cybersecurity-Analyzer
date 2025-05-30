from Agents.scanAgent import ScanAgent
from Agents.explainAgent import ExplainAgent

url = "https://juice-shop.herokuapp.com/#/"
#code_path = "./your_code_directory"      

print("\n=== Step 1: Running Scans ===")
scanner = ScanAgent(url=url)
scan_results = scanner.run_all()

print("\n=== Step 2: Explaining Vulnerabilities ===")
explainer = ExplainAgent()
combined_report = explainer.create_combined_report()

print("\n=== Done ===")
print(f"Total Web Issues Found: {combined_report['summary']['total_web_issues']}")
print(f"Total Code Issues Found: {combined_report['summary']['total_code_issues']}")
print("Combined report saved to 'reports/combined_report.json'")