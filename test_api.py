import requests
from dotenv import load_dotenv
import os

load_dotenv()

OC = os.getenv("LAW_API_OC")

url = "https://www.law.go.kr/DRF/lawSearch.do"

params = {
    "OC": OC,
    "target": "law",
    "type": "JSON",
    "query": "금융소비자보호법"
}

res = requests.get(url, params=params)

print("URL:", res.url)
print("상태:", res.status_code)
print(res.text[:1000])