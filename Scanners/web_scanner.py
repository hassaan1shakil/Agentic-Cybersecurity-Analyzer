import time
import subprocess
import os
from zapv2 import ZAPv2
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ZAP_API_KEY")
ZAP_PROXY = 'http://localhost:8080'
ZAP_PATH = os.getenv("ZAP_PATH")

def start_zap_daemon():
    try:
        subprocess.Popen([
            f"{ZAP_PATH}/zap.sh",
            "-daemon",
            "-port", "8080",
            f"-config", f"api.key={API_KEY}"
        ])
        print("[+] Starting ZAP in daemon mode...")
        time.sleep(15)
    except Exception as e:
        print(f"[!] Failed to start ZAP daemon: {e}")

zap = ZAPv2(apikey=API_KEY, proxies={'http': ZAP_PROXY, 'https': ZAP_PROXY})

def zap_scan(url, auth=None, enable_ajax_spider=True, api_spec=True):
    start_zap_daemon()
    zap.urlopen(url)

    if api_spec:
        print("[+] Importing API spec")
        zap.openapi.import_url("https://api.example.com/swagger.json")  

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
    return alerts