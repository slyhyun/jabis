"""
Agent 1: 규제 검색
- RAG (Chroma Vector DB) 호출
- MCP #1 (국가법령정보센터) 호출
- 두 결과 통합 + 출처 표시
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from sentence_transformers import SentenceTransformer
import chromadb
from mcp_servers.law_mcp.client import search_law

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
COLLECTION_NAME = "jabis_regulations"
MODEL_NAME = "jhgan/ko-sroberta-multitask"
RAG_TOP_K = 5      # RAG에서 가져올 상위 결과 수
MCP_DISPLAY = 3    # MCP에서 가져올 법령 수

# 모델/클라이언트는 최초 1회만 로드
_model = None
_collection = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


# ============================================================
# RAG 검색
# ============================================================

def search_rag(query: str, top_k: int = RAG_TOP_K) -> list:
    """Chroma에서 관련 규제 청크 검색"""
    model = _get_model()
    collection = _get_collection()

    embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=embedding,
        n_results=top_k,
    )

    chunks = []
    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        # 출처 표시 로직
        if meta.get("source_type") == "law":
            source = f"{meta.get('law_name', '')} 제{meta.get('article_no', '')}조 {meta.get('article_title', '')}".strip()
        else:
            source = meta.get("source", meta.get("source_file", ""))

        chunks.append({
            "text": doc,
            "source": source,
            "source_type": meta.get("source_type", ""),
            "metadata": meta,
            "score": round(1 - distance, 4),  # cosine similarity
        })

    return chunks


# ============================================================
# MCP #1 검색
# ============================================================

def search_mcp(query: str, display: int = MCP_DISPLAY) -> list:
    """국가법령정보센터 API에서 관련 법령 검색"""
    result = search_law(query, display=display)
    laws = result.get("laws", [])
    is_fallback = result.get("fallback", False)

    items = []
    for law in laws:
        items.append({
            "law_name": law.get("법령명한글", ""),
            "law_type": law.get("법령구분명", ""),
            "law_id": law.get("법령ID", ""),
            "source": f"{law.get('법령명한글', '')} ({law.get('법령구분명', '')})",
            "is_fallback": is_fallback,
        })

    return items


# ============================================================
# Agent 1 메인 함수
# ============================================================

def run_agent1(ad_copy: str, product_type: str = "") -> dict:
    """
    Agent 1: 규제 검색 실행
    - ad_copy: 심의 대상 광고 카피
    - product_type: 상품 유형 (예금, 대출 등)
    """
    print(f"[Agent 1] 규제 검색 시작")

    # 검색 쿼리 구성
    query = ad_copy
    if product_type:
        query = f"{product_type} 광고 {ad_copy}"

    # RAG 검색
    print(f"[Agent 1] RAG 검색 중...")
    rag_results = search_rag(query)

    # MCP #1 검색 - 상품 유형별 관련 법령 고정 검색
    PRODUCT_LAW_MAP = {
        "예금": ["금융소비자보호법", "예금자보호법"],
        "적금": ["금융소비자보호법", "예금자보호법"],
        "대출": ["금융소비자보호법"],
        "펀드": ["금융소비자보호법", "자본시장과 금융투자업"],
        "카드": ["금융소비자보호법"],
        "보험": ["금융소비자보호법"],
    }
    law_queries = PRODUCT_LAW_MAP.get(product_type, ["금융소비자보호법"])
    print(f"[Agent 1] MCP #1 법령 검색 중... (laws: {law_queries})")
    mcp_results = []
    for law_query in law_queries:
        mcp_results.extend(search_mcp(law_query, display=2))

    # 결과 통합
    regulation_results = {
        "query": query,
        "rag": rag_results,
        "mcp": mcp_results,
        "sources": list(set(
            [r["source"] for r in rag_results] +
            [r["source"] for r in mcp_results]
        )),
    }

    print(f"[Agent 1] 완료 — RAG {len(rag_results)}건, MCP {len(mcp_results)}건")
    return regulation_results


# ============================================================
# 동작 테스트
# ============================================================

if __name__ == "__main__":
    test_copy = "JB금융 정기예금 연 5.0% 확정금리! 원금 보장, 지금 바로 가입하세요."
    result = run_agent1(test_copy, product_type="예금")

    print("\n=== RAG 검색 결과 ===")
    for r in result["rag"]:
        print(f"  [{r['score']}] {r['source']}")
        print(f"    {r['text'][:80]}...")

    print("\n=== MCP 법령 검색 결과 ===")
    for r in result["mcp"]:
        print(f"  {r['source']}")

    print("\n=== 출처 목록 ===")
    for s in result["sources"]:
        print(f"  - {s}")
