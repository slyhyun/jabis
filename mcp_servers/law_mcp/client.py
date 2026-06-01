import requests
import os
from dotenv import load_dotenv

load_dotenv()

LAW_API_OC = os.getenv("LAW_API_OC", "jabis2026")
LAW_API_BASE_URL = os.getenv("LAW_API_BASE_URL", "https://www.law.go.kr/DRF")


def search_law(query: str, display: int = 5) -> dict:
    """국가법령정보센터 API로 법령 검색"""
    url = f"{LAW_API_BASE_URL}/lawSearch.do"
    params = {
        "OC": LAW_API_OC,
        "target": "law",
        "type": "JSON",
        "query": query,
        "display": display,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    print("금융소비자보호법 검색 테스트\n")
    result = search_law("금융소비자보호법")

    laws = result.get("LawSearch", {}).get("law", [])
    if laws:
        for law in laws:
            print(f"- {law.get('법령명한글')} ({law.get('법령구분명')})")
    else:
        print("검색 결과 없음")
        print("응답:", result)
