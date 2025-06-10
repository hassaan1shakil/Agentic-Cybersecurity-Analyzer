import os
import json
import time
import random
import socket
import docker
import subprocess
from zapv2 import ZAPv2
from dotenv import load_dotenv

load_dotenv()

# both of these need to be checked and updated
ZAP_HOST = 'http://127.0.0.1'
ZAP_PATH = os.getenv("ZAP_PATH")

def get_free_port(start=8081, end=9000):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port available")


def start_zap_daemon(zap_path="/usr/local/bin", base_port=8081, api_key=None):
    port = get_free_port(base_port)
    api_key = api_key or f"key_{random.randint(100000, 999999)}"

    try:
        client = docker.from_env()

        container = client.containers.run(
            image="ghcr.io/zaproxy/zaproxy",
            command=[
                "zap.sh", "-daemon",
                "-host", "0.0.0.0",
                "-port", "8080",
                "-config", f"api.key={api_key}",
                "-config", "api.addrs.addr.name=.*",
                "-config", "api.addrs.addr.regex=true"
            ],
            ports={"8080/tcp": port},
            volumes={"/tmp/zap": {"bind": "/zap/wrk", "mode": "rw"}},
            detach=True,
            remove=True
        )
    
        print(f"[+] Starting ZAP on port {port} with API key {api_key}...")
        time.sleep(200)  # Wait for ZAP to start

        return {
            "container_id": container.id,
            "port": port,
            "api_key": api_key
        }

    except Exception as e:
        print(f"[!] Failed to start ZAP daemon: {e}")
        return {
            "status": "failure",
            "error": f"Failed to start ZAP daemon: {e}"
        }


def zap_scan(url, auth=None, enable_ajax_spider=True, api_spec=True):
    
    try:
        zap_instance = start_zap_daemon(ZAP_PATH, 8081)
        zap_proxy = f"{ZAP_HOST}:{zap_instance['port']}"
        print("Zap Proxy:", zap_proxy)
        
        zap = ZAPv2(apikey=zap_instance['api_key'], proxies={'http': zap_proxy, 'https': zap_proxy})
        
        print("Opening URL")
        zap.core.access_url(url)
        print("URL Opened")
        
        if api_spec:
            print("[+] Importing API spec")
            zap.openapi.import_url("https://api.example.com/swagger.json")  
            print("API Spec Imported")

        print("Starting ZAP Spider")
        scan_id = zap.spider.scan(url)
        while int(zap.spider.status(scan_id)) < 100:
            print(f"[ZAP Spider] Progress: {zap.spider.status(scan_id)}%")
            time.sleep(2)
        
        if enable_ajax_spider:
            print("[+] Starting AJAX Spider...")
            zap.ajaxSpider.scan(url)
            while zap.ajaxSpider.status == 'running':
                print(f"[ZAP AJAX Spider] Progress: {zap.ajaxSpider.number_of_results} URLs found")
                time.sleep(5)

        if auth:
            zap.context.new_context("default")
            context_id = zap.context.context("default")['id']
            zap.authentication.set_authentication_method(context_id, "formBasedAuthentication", auth['auth_method'])
            zap.users.new_user(context_id, "test_user")
            zap.users.set_authentication_credentials(context_id, 0, auth['credentials'])
            zap.users.set_user_enabled(context_id, 0, True)
            zap.ascan.scan_as_user(url, context_id, 0)
        else:
            zap.ascan.scan(url)

        while int(zap.ascan.status()) < 100:
            print(f"[ZAP Active Scan] Progress: {zap.ascan.status()}%")
            time.sleep(5)

        alerts = zap.core.alerts()
        zap.core.shutdown()
        print("Shutting Down ZAP...")
        print("[+] ZAP scan completed.")
        print(f"[+] Found {len(alerts)} alerts.")
        
        return {
            "status": "success",
            "results": alerts
        }
        
    except Exception as e:
        print(e)
        return {
            "status": "failure",
            "error": f"Web Scan Could not be completed. {e}"
        }

    finally:
        if 'zap_instance' in locals() and 'container_id' in zap_instance:
            subprocess.run(["docker", "stop", zap_instance['container_id']], check=True)



def format_web_scan_results(raw_data):
    if not raw_data:
        return {
            "status": "success",
            "results": []
        }
    
    grouped = {}
    risk_priority = {
        "High": 1,
        "Medium": 2,
        "Low": 3,
        "Informational": 4
    }

    for item in raw_data:
        name = item["name"]

        if name not in grouped:
            grouped[name] = {
                "name": name,
                "risk": item.get("risk", ""),
                "description": item.get("description", ""),
                "solution": item.get("solution", ""),
                "references": item.get("reference", "").split("\n") if "reference" in item else [],
                "tags": item.get("tags", {}),
                "common": {
                    "pluginId": item.get("pluginId", ""),
                    "cweid": item.get("cweid", ""),
                    "wascid": item.get("wascid", ""),
                    "confidence": item.get("confidence", ""),
                    "sourceid": item.get("sourceid", ""),
                    "alertRef": item.get("alertRef", ""),
                },
                "instances": []
            }

        instance = {
            "url": item.get("url", ""),
            "param": item.get("param", ""),
            "method": item.get("method", ""),
            "evidence": item.get("evidence", ""),
            "messageId": item.get("messageId", ""),
            "sourceMessageId": item.get("sourceMessageId", "")
        }

        grouped[name]["instances"].append(instance)
    
    grouped_list = list(grouped.values())
    grouped_list.sort(key=lambda x: risk_priority.get(x["risk"], 5))

    return {
        "status": "success",
        "results": grouped_list
    }

def web_scanner(web_url: str):
    if not web_url:
        print("[!] No URL provided. Skipping web scan.")
        return {
            "status": "failure",
            "error": "No URL provided"
        }
    
    print("[+] Running ZAP Web Scan...")
    report = zap_scan(web_url)
    
    if "status" in report and report["status"] == "failure":
        return report
        
    report = format_web_scan_results(report.get('results'))
    return report
    

def web_scanner_handler(git_repo_url: str):
    
    results = web_scanner(git_repo_url)
    
    if results.get("status") == "failure":
        return {
            "status": "failure",
            "message": results.get("error", "An error occurred during the code scan.")
        }
    
    reports_dir = "scan_reports"
    os.makedirs(reports_dir, exist_ok=True)
    filename = os.path.join(reports_dir, f"web_scan_results_{int(time.time())}.json")
    with open(filename, "w") as f:
        json.dump(results, f, indent=4)
        
    return {
        "status": results.get("status"),
        "message": f"Code scan completed. Results saved to {filename}"
    }

if __name__ == "__main__":
    web_url = "https://hassaanshakil.com"
    scan_output = web_scanner_handler(web_url)
    print("Web Scan Output:\n")
    print(scan_output)