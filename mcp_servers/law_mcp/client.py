"""
MCP #1 — 국가법령정보센터 API 클라이언트
검색, 상세 조회, 에러 처리, fallback 포함
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

LAW_API_OC = os.getenv("LAW_API_OC", "jabis2026")
LAW_API_BASE_URL = os.getenv("LAW_API_BASE_URL", "https://www.law.go.kr/DRF")

# fallback: API 호출 실패 시 반환할 기본 법령 목록
FALLBACK_LAWS = [
    {"법령명한글": "금융소비자 보호에 관한 법률", "법령구분명": "법률", "법령ID": ""},
    {"법령명한글": "표시·광고의 공정화에 관한 법률", "법령구분명": "법률", "법령ID": ""},
    {"법령명한글": "자본시장과 금융투자업에 관한 법률", "법령구분명": "법률", "법령ID": ""},
]


def search_law(query: str, display: int = 5) -> dict:
    """
    법령 검색
    - query: 검색어
    - display: 결과 수 (기본 5개)
    - 실패 시 fallback 반환
    """
    url = f"{LAW_API_BASE_URL}/lawSearch.do"
    params = {
        "OC": LAW_API_OC,
        "target": "law",
        "type": "JSON",
        "query": query,
        "display": display,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        laws = data.get("LawSearch", {}).get("law", [])
        if not laws:
            return {"source": "api", "query": query, "laws": [], "fallback": False}

        return {
            "source": "api",
            "query": query,
            "laws": laws,
            "fallback": False,
        }

    except requests.exceptions.Timeout:
        print(f"[Law MCP] 타임아웃 발생 — fallback 반환 (query: {query})")
        return _fallback_response(query, reason="timeout")

    except requests.exceptions.ConnectionError:
        print(f"[Law MCP] 연결 오류 — fallback 반환 (query: {query})")
        return _fallback_response(query, reason="connection_error")

    except requests.exceptions.HTTPError as e:
        print(f"[Law MCP] HTTP 오류 {e.response.status_code} — fallback 반환")
        return _fallback_response(query, reason=f"http_error_{e.response.status_code}")

    except Exception as e:
        print(f"[Law MCP] 알 수 없는 오류 — fallback 반환: {e}")
        return _fallback_response(query, reason="unknown_error")


def get_law_detail(law_id: str) -> dict:
    """
    법령 상세 조회 (법령 ID로 본문 조회)
    - law_id: 법령 MST ID
    - 실패 시 fallback 반환
    """
    url = f"{LAW_API_BASE_URL}/lawService.do"
    params = {
        "OC": LAW_API_OC,
        "target": "law",
        "type": "JSON",
        "ID": law_id,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        law_info = data.get("법령", {})
        if not law_info:
            return {"source": "api", "law_id": law_id, "detail": None, "fallback": False}

        return {
            "source": "api",
            "law_id": law_id,
            "detail": {
                "법령명": law_info.get("기본정보", {}).get("법령명_한글", ""),
                "공포일자": law_info.get("기본정보", {}).get("공포일자", ""),
                "시행일자": law_info.get("기본정보", {}).get("시행일자", ""),
                "조문": law_info.get("조문", {}).get("조문단위", []),
            },
            "fallback": False,
        }

    except requests.exceptions.Timeout:
        print(f"[Law MCP] 상세 조회 타임아웃 — fallback 반환 (ID: {law_id})")
        return _fallback_detail_response(law_id, reason="timeout")

    except requests.exceptions.ConnectionError:
        print(f"[Law MCP] 상세 조회 연결 오류 — fallback 반환 (ID: {law_id})")
        return _fallback_detail_response(law_id, reason="connection_error")

    except requests.exceptions.HTTPError as e:
        print(f"[Law MCP] 상세 조회 HTTP 오류 {e.response.status_code} — fallback 반환")
        return _fallback_detail_response(law_id, reason=f"http_error_{e.response.status_code}")

    except Exception as e:
        print(f"[Law MCP] 상세 조회 알 수 없는 오류 — fallback 반환: {e}")
        return _fallback_detail_response(law_id, reason="unknown_error")


# ============================================================
# Fallback 헬퍼
# ============================================================

def _fallback_response(query: str, reason: str) -> dict:
    """검색 실패 시 기본 법령 목록 반환"""
    return {
        "source": "fallback",
        "query": query,
        "laws": FALLBACK_LAWS,
        "fallback": True,
        "reason": reason,
    }


def _fallback_detail_response(law_id: str, reason: str) -> dict:
    """상세 조회 실패 시 빈 응답 반환"""
    return {
        "source": "fallback",
        "law_id": law_id,
        "detail": None,
        "fallback": True,
        "reason": reason,
    }


# ============================================================
# 동작 테스트
# ============================================================

if __name__ == "__main__":
    print("=== 검색 테스트 ===")
    result = search_law("금융소비자보호법")
    laws = result.get("laws", [])
    print(f"검색 결과 {len(laws)}건 (fallback: {result.get('fallback')})")
    for law in laws:
        print(f"  - {law.get('법령명한글')} ({law.get('법령구분명')})")

    if laws and not result.get("fallback"):
        law_id = laws[0].get("법령ID") or laws[0].get("법령MST번호", "")
        if law_id:
            print(f"\n=== 상세 조회 테스트 (ID: {law_id}) ===")
            detail = get_law_detail(law_id)
            print(f"법령명: {detail.get('detail', {}).get('법령명', '') if detail.get('detail') else '조회 실패'}")
            print(f"fallback: {detail.get('fallback')}")
