"""
RAG 품질 테스트 스크립트
- 시연 카피 4개로 Agent 1 RAG 검색 정확도 확인
- 검색된 청크의 관련성 점수 및 출처 출력
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sentence_transformers import SentenceTransformer
import chromadb

CHROMA_DIR = "./data/chroma_db"
COLLECTION_NAME = "jabis_regulations"
MODEL_NAME = "jhgan/ko-sroberta-multitask"
DEMO_PATH = "./data/demo/test_copies.json"

TOP_K_LIST = [3, 5, 10]  # 튜닝할 top_k 후보


def load_demo_copies():
    with open(DEMO_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def run_rag_test(query: str, model, collection, top_k: int) -> list:
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
        score = round(1 - distance, 4)
        if meta.get("source_type") == "law":
            source = f"{meta.get('law_name', '')} 제{meta.get('article_no', '')}조"
        else:
            source = meta.get("source", meta.get("source_file", ""))
        chunks.append({"score": score, "source": source, "text": doc[:120]})
    return chunks


def evaluate(chunks: list, top_k: int) -> dict:
    """간단한 품질 지표"""
    avg_score = round(sum(c["score"] for c in chunks) / len(chunks), 4) if chunks else 0
    high_relevance = sum(1 for c in chunks if c["score"] >= 0.7)
    sources = list({c["source"] for c in chunks})
    return {
        "top_k": top_k,
        "avg_score": avg_score,
        "high_relevance_count": high_relevance,
        "unique_sources": len(sources),
    }


def main():
    print("RAG 모델 로딩 중...")
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(COLLECTION_NAME)
    print(f"컬렉션 문서 수: {collection.count()}\n")

    demos = load_demo_copies()

    for demo in demos:
        print(f"{'='*60}")
        print(f"[{demo['id']}] {demo['label']}")
        print(f"카피: {demo['ad_copy']}\n")

        query = f"{demo['product_type']} 광고 {demo['ad_copy']}"

        best_top_k = None
        best_avg = 0

        for top_k in TOP_K_LIST:
            chunks = run_rag_test(query, model, collection, top_k)
            metrics = evaluate(chunks, top_k)

            print(f"  [top_k={top_k}] 평균 점수: {metrics['avg_score']} | "
                  f"고관련(≥0.7): {metrics['high_relevance_count']}건 | "
                  f"출처 다양성: {metrics['unique_sources']}개")

            if metrics["avg_score"] > best_avg:
                best_avg = metrics["avg_score"]
                best_top_k = top_k
                best_chunks = chunks

        print(f"\n  ★ 최적 top_k: {best_top_k} (평균 점수: {best_avg})")
        print(f"  상위 3개 청크:")
        for i, c in enumerate(best_chunks[:3], 1):
            print(f"    {i}. [{c['score']}] {c['source']}")
            print(f"       {c['text']}...")
        print()

    print("RAG 품질 테스트 완료")


if __name__ == "__main__":
    main()
