import requests
import pandas as pd

url = "http://opendata.cbs.nl/ODataApi/odata/82610ENG/EnergySourcesTechniques"
print(f"Fetching metadata from {url}...")
try:
    r = requests.get(url, timeout=30)
    data = r.json()
    if 'value' in data:
        df = pd.DataFrame(data['value'])
        print(df[['Key', 'Title']])
    else:
        print("No value in response")
except Exception as e:
    print(f"Failed: {e}")
