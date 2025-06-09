import json
import subprocess
import os
import tempfile
import shutil

SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".java", ".go", ".c", ".cpp", ".rb", ".php", ".jsx", ".tsx", ".cs", ".swift", ".kt", ".scala", ".rs", ".m", ".sh", ".pl", ".lua", ".dart", ".html", ".xml", ".json", ".yml", ".yaml"}

def get_supported_files(code_path):
    files = []
    for root, _, filenames in os.walk(code_path):
        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext in SUPPORTED_EXTENSIONS:
                files.append(os.path.join(root, filename))
    return files

def analyze_code_with_semgrep(code_path):
    files_to_scan = get_supported_files(code_path)
    if not files_to_scan:
        print("[!] No supported source code files found.")
        return { "error": "No supported source code files found." }

    try:
        result = subprocess.run([
            "semgrep", "--config", "p/default", "--json", *files_to_scan
        ], capture_output=True, text=True)

        semgrep_output = json.loads(result.stdout)

        for issue in semgrep_output.get("results", []):
            issue["vulnerable_line"] = issue.get("start", {}).get("line", None)
            issue["code_snippet"] = issue.get("extra", {}).get("lines", "").strip()
            file_path = issue.get("path", "")
            start_offset = issue.get("start", {}).get("offset", None)
            end_offset = issue.get("end", {}).get("offset", None)

            if start_offset is not None and end_offset is not None and os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        full_content = f.read()
                        exact_snippet = full_content[start_offset:end_offset].strip()
                        issue["exact_snippet"] = exact_snippet
                except Exception as e:
                    print(f"[!] Failed to extract exact snippet from {file_path}: {e}")
                    issue["exact_snippet"] = issue["code_snippet"]
            else:
                issue["exact_snippet"] = issue["code_snippet"]

        print(f"[+] Semgrep scan completed. {len(semgrep_output.get('results', []))} issues found.")
        # print(json.dumps(semgrep_output, indent=4))
        return semgrep_output

    except Exception as e:
        print("[!] Semgrep scan failed:", e)
        return { "error": f"Semgrep scan failed: {str(e)}" }


def code_scanner(git_repo_url: str):
    if not git_repo_url or not git_repo_url.endswith(".git"):
        print("[!] Invalid Git repo URL.")
        return { "error": "Invalid Git repository URL." }

    print("[+] Cloning GitHub repository...")
    temp_dir = tempfile.mkdtemp()
    
    try:
        subprocess.run(["git", "clone", git_repo_url, temp_dir], check=True)

        print("[+] Running Semgrep Code Analysis...")
        raw_report = analyze_code_with_semgrep(temp_dir)
        
        if not raw_report:
            return { "error": "Semgrep scan failed." }
        
        elif not raw_report.get("results"):
            return { "error": "No vulnerabilities found in the code." }

        final_report = {
            "results": raw_report.get("results", []),
            "errors": raw_report.get("errors", []),
            "paths": raw_report.get("paths", {}),
            "version": raw_report.get("version", "")
        }

        return final_report

    except subprocess.CalledProcessError as e:
        print("[!] Failed to clone repository:", e)
        return { "error": f"Failed to clone repository: {str(e)}" }

    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    github_url = "https://github.com/hassaan1shakil/Agentic-Cybersecurity-Analyzer.git"
    scan_output = code_scanner(github_url)
    print(scan_output)