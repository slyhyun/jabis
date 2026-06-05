"""
MCP #1 — 국가법령정보센터 MCP 서버
FastAPI 엔드포인트로 법령 검색/상세 조회 제공
"""
from fastapi import FastAPI, HTTPException
from .client import search_law, get_law_detail

app = FastAPI(
    title="JABIS Law MCP",
    description="MCP #1 — 국가법령정보센터 법령 검색/상세 조회 API",
    version="0.1.0",
)


@app.get("/laws/search")
def search(query: str, display: int = 5):
    """법령 검색"""
    if not query:
        raise HTTPException(status_code=400, detail="검색어를 입력해주세요.")
    return search_law(query, display)


@app.get("/laws/{law_id}")
def get_detail(law_id: str):
    """법령 상세 조회"""
    result = get_law_detail(law_id)
    if not result.get("detail") and not result.get("fallback"):
        raise HTTPException(status_code=404, detail=f"법령을 찾을 수 없습니다: {law_id}")
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
