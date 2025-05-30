import time
from zapv2 import ZAPv2
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("ZAP_API_KEY")
ZAP_PROXY = 'http://localhost:8080'

zap = ZAPv2(apikey=API_KEY, proxies={'http': ZAP_PROXY, 'https': ZAP_PROXY})

def zap_scan(url, auth=None):
    zap.urlopen(url)

    if auth:
        zap.context.new_context("default")
        context_id = zap.context.context("default")['id']

        zap.authentication.set_authentication_method(context_id, "formBasedAuthentication", auth['auth_method'])
        zap.authentication.set_logged_in_indicator(context_id, auth['logged_in_indicator'])
        zap.users.new_user(context_id, "test_user")
        zap.users.set_authentication_credentials(context_id, 0, auth['credentials'])
        zap.users.set_user_enabled(context_id, 0, True)
        zap.ascan.scan_as_user(url, context_id, 0)
    else:
        zap.ascan.scan(url)

    while int(zap.ascan.status()) < 100:
        print(f"[ZAP] Scan progress: {zap.ascan.status()}%")
        time.sleep(5)
    return zap.core.alerts()