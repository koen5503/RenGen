import requests
import cbsodata

url = "https://opendata.cbs.nl/ODataApi/odata/82610ENG"

print(f"Testing URL: {url}")

try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {r.status_code}")
    print(f"Content Start: {r.text[:200]}")
except Exception as e:
    print(f"Requests failed: {e}")

print("\nTesting cbsodata library directly...")
try:
    # cbsodata doesn't seem to allow passing headers easily in high level functions unless we patch or it uses default info
    # But maybe it's just the endpoint 82610ENG that is problematic?
    info = cbsodata.get_info('82610ENG')
    print("cbsodata success!")
    print(info)
except Exception as e:
    print(f"cbsodata failed: {e}")
