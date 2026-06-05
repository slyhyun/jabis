"""
국가법령정보 API - 법령 데이터 JSON 수집 스크립트
저장 위치: data/raw/laws/
"""

import requests
import json
import os
from dotenv import load_dotenv
import ssl
import urllib3
import xmltodict
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import time

load_dotenv()

API_KEY = os.getenv("LAW_API_OC")
BASE_URL = "https://www.law.go.kr/DRF/lawService.do"
SAVE_DIR = "data/raw/laws"

SEARCH_URL = "https://www.law.go.kr/DRF/lawSearch.do"
DETAIL_URL = "https://www.law.go.kr/DRF/lawService.do"

os.makedirs(SAVE_DIR, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

# 수집 대상 법령 목록
TARGET_LAWS = [
    {
        "name": "금융소비자보호법",
        "query": "금융소비자보호법",
        "filename": "financial_consumer_protection.json"
    },
    {
        "name": "시행령",
        "query": "금융소비자보호법 시행령",
        "filename": "financial_consumer_protection_enforcement.json"
    },
    {
        "name": "표시광고법",
        "query": "표시·광고의 공정화에 관한 법률",
        "filename": "fair_display_advertising.json"
    },
    {
        "name": "자본시장법",
        "query": "자본시장과 금융투자업",
        "filename": "capital_markets.json"
    },
]


def search_law(query: str) :
    """법령명으로 검색해서 법령 ID(MST) 반환(XML)"""
    params = {
        "OC": API_KEY,
        "target": "law",
        "type": "XML",
        "query": query,
    }
    
    res = requests.get(SEARCH_URL, params=params, verify = False, headers = headers, timeout = 30)
    
    print("\n===== Request URL ====")
    print(res.url)
    print("==================\n")

    print("\n===== RAW =====")
    print(res.text[:1500])
    print("==============\n")

    #res.encoding = "utf-8"
    #data = res.json()

    try:
        data = xmltodict.parse(res.text)
        laws = data.get("LawSearch", {}).get("law")

        if not laws:
            print("검색 결과 없음")
            return None
        
        if isinstance(laws, list):
            law = laws[0]
        else:
            law = laws

        mst = law.get("법령ID")
        name = law.get("법령명한글")

        print(f"검색 성공 : {name} (ID : {mst})")
        
        return mst
    
    except Exception as e:
         print("XML 피싱 실패 : ", e)
         return None
    '''
    try:
        lawsearch = data.get("LawSearch", {})
        laws = lawsearch.get("law")

        if not laws:
            print("검색 결과 없음")
            return None
        if isinstance(laws,list):
            law = laws[0] if laws else None
        elif isinstance(laws, dict):
            law = laws
        else:
            print("알 수 없는 law 구조")
            return None
        
        if not law:
            return None

        mst = law.get("법령ID")

        print(f"검색 성공 :",law.get("법령명한글"), mst)
        return mst
    
    except Exception as e:
        print("검색 피싱 실패 : ", e)
        return None


    print("\n===== 응답 확인 =====")
    print(res.url)
    print(res.text[:2000])
    print("=====================\n")
    

    try:
        laws = data["LawSearch"]["law"]
        # 결과가 여러 개면 리스트, 하나면 딕셔너리
        if isinstance(laws, list):
            law = laws[0]
        else:
            law = laws
        mst = law["법령ID"]
        print(f"  검색 성공: {law['법령명칭']} (ID: {mst})")
        return mst
    except (KeyError, TypeError):
        print(f"  검색 실패: {query}")
        return None
        '''


def fetch_law_detail(mst: str) :
    """법령 ID로 본문 전체 조문 가져오기"""
    params = {
        "OC": API_KEY,
        "target": "law",
        "type": "XML",
        "ID": mst,
    }
    res = requests.get(BASE_URL, params=params, verify=False)
    #res.encoding = "utf-8"
    #data = res.json()

    data = xmltodict.parse(res.text)
    return data
  
    '''
    try:
        return data["LawService"]["법령"]
    except Exception:
        print("본문 구조 이상 / MST : ", mst)
        return None
    '''

def parse_articles(law_data: dict) -> list[dict]:
    """조문 단위로 파싱해서 리스트 반환"""
    articles = []

    try:
        # 조문 단위 파싱
        jo_list = law_data.get("법령", {}).get("조문", {}).get("조문단위")
        
        if not jo_list:
            return []
        if isinstance(jo_list, dict):
            jo_list = [jo_list]

        for jo in jo_list:
            article = {
                "조문번호": jo.get("조문번호", ""),
                "조문제목": jo.get("조문제목", ""),
                "조문내용": jo.get("조문내용", ""),
                "항": []
            }

            # 항 파싱
            hang_list = jo.get("항")

            if isinstance(hang_list, dict):
                hang_list = [hang_list]
            elif hang_list is None:
                hang_list = []

            for hang in hang_list:
                article["항"].append({
                    "항번호": hang.get("항번호"),
                    "항내용": hang.get("항내용"),
                })

            articles.append(article)

    except Exception as e:
        print(f"조문 파싱 오류: {e}")

    return articles


def collect_law(law_info: dict):
    """법령 하나 수집 → JSON 저장"""
    print(f"\n[수집 시작] {law_info['name']}")

    # 1. 법령 검색
    mst = search_law(law_info["query"])
    if not mst:
        return

    time.sleep(1.5)

    # 2. 본문 조회
    law_data = fetch_law_detail(mst)
  
    if not law_data:
        return

    print(json.dumps(law_data, indent=2, ensure_ascii=False)[:3000])

    time.sleep(1.5)

    # 3. 조문 파싱
    articles = parse_articles(law_data)

    # 4. 저장할 JSON 구조
    result = {
        "법령명": law_info["name"],
        "검색어": law_info["query"],
        "법령ID": mst,
        "조문수": len(articles),
        "조문목록": articles,
        # 원본 데이터도 보관
        "원본": law_data,
    }

    # 5. JSON 저장
    save_path = os.path.join(SAVE_DIR, law_info["filename"])

    with open(save_path, "w", encoding="utf-8") as f:
        print("DEBUG SAVE PATH:",save_path)
        print("DEBUG ARTICLES COUNT : ", len(articles))
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  저장 완료: {save_path} ({len(articles)}개 조문)")


def main():
    if not API_KEY:
        print("오류: .env 파일에 LAW_API_KEY가 설정되어 있지 않습니다.")
        return

    print("=" * 50)
    print("법령 데이터 수집 시작")
    print("=" * 50)

    for law_info in TARGET_LAWS:
        collect_law(law_info)

    print("\n" + "=" * 50)
    print("수집 완료!")
    print(f"저장 위치: {SAVE_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    main()
