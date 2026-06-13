import httpx
from typing import Optional

BASE_URL = "http://localhost:8000"
TIMEOUT = 60.0


def _get(path: str, params: dict = None) -> dict:
    try:
        r = httpx.get(f"{BASE_URL}{path}", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return {"ok": True, "data": r.json()}
    except httpx.TimeoutException:
        return {"ok": False, "error": "요청 시간이 초과되었습니다 (60초)"}
    except httpx.HTTPStatusError as e:
        return {"ok": False, "error": f"서버 오류 ({e.response.status_code})"}
    except Exception as e:
        return {"ok": False, "error": f"연결 실패: {str(e)}"}


def _post(path: str, body: dict) -> dict:
    try:
        r = httpx.post(f"{BASE_URL}{path}", json=body, timeout=TIMEOUT)
        r.raise_for_status()
        return {"ok": True, "data": r.json()}
    except httpx.TimeoutException:
        return {"ok": False, "error": "요청 시간이 초과되었습니다 (60초)"}
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.json().get("detail", "")
        except Exception:
            pass
        return {"ok": False, "error": f"서버 오류 ({e.response.status_code}): {detail}"}
    except Exception as e:
        return {"ok": False, "error": f"연결 실패: {str(e)}"}


def health_check() -> bool:
    r = _get("/health")
    return r["ok"]


def create_review(ad_copy: str, product_type: str, product_id: str) -> dict:
    return _post("/api/review", {
        "ad_copy": ad_copy,
        "product_type": product_type,
        "product_id": product_id,
    })


def get_review(review_id: int) -> dict:
    return _get(f"/api/review/{review_id}")


def get_history(skip: int = 0, limit: int = 20) -> dict:
    return _get("/api/review/history", params={"skip": skip, "limit": limit})


def set_decision(review_id: int, decision: str, comment: Optional[str] = None) -> dict:
    body = {"decision": decision}
    if comment:
        body["comment"] = comment
    return _post(f"/api/review/{review_id}/decision", body)


def translate_review(review_id: int) -> dict:
    return _post(f"/api/review/{review_id}/translate", {})


def get_pdf_url(review_id: int) -> str:
    return f"{BASE_URL}/api/review/{review_id}/pdf"
