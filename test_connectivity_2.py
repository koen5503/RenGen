import requests
import cbsodata
import sys

# Test HTTP
url_http = "http://opendata.cbs.nl/ODataApi/odata/82610ENG"
print(f"Testing HTTP URL: {url_http}")
try:
    r = requests.get(url_http, timeout=10)
    print(f"HTTP Status Code: {r.status_code}")
except Exception as e:
    print(f"HTTP Requests failed: {e}")

# Test Catalog
url_catalog = "https://opendata.cbs.nl/ODataCatalog/Tables?$top=1"
print(f"Testing Catalog URL: {url_catalog}")
try:
    r = requests.get(url_catalog, timeout=10)
    print(f"Catalog Status Code: {r.status_code}")
except Exception as e:
    print(f"Catalog Requests failed: {e}")

# Test another dataset
# 83765NED is 'Key figures'
print("Testing cbsodata with 83765NED")
try:
    info = cbsodata.get_info('83765NED')
    print("cbsodata 83765NED success!")
except Exception as e:
    print(f"cbsodata 83765NED failed: {e}")
