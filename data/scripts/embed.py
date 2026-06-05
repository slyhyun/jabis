"""
임베딩 및 Chroma Vector DB 인덱싱 스크립트
- 모델: jhgan/ko-sroberta-multitask (한국어 특화)
- 입력: data/processed/chunks.json
- 저장: data/chroma_db/
실행: python data/scripts/embed.py
"""
import json
import os
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

CHUNKS_PATH = "data/processed/chunks.json"
CHROMA_DIR = "data/chroma_db"
COLLECTION_NAME = "jabis_regulations"
MODEL_NAME = "jhgan/ko-sroberta-multitask"
BATCH_SIZE = 64  # 한 번에 임베딩할 청크 수


def load_chunks(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def embed_and_index():
    # 1. 청크 로드
    print(f"청크 로드 중: {CHUNKS_PATH}")
    chunks = load_chunks(CHUNKS_PATH)
    print(f"총 {len(chunks)}개 청크 로드 완료\n")

    # 2. 임베딩 모델 로드
    print(f"임베딩 모델 로드 중: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("모델 로드 완료\n")

    # 3. Chroma 클라이언트 초기화
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # 기존 컬렉션 있으면 삭제 후 재생성
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
        print(f"기존 컬렉션 '{COLLECTION_NAME}' 삭제\n")

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # 4. 배치 단위로 임베딩 + 인덱싱
    print("임베딩 및 인덱싱 시작...")
    total = len(chunks)

    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        metadatas = [c["metadata"] for c in batch]
        ids = [f"chunk_{i + j}" for j in range(len(batch))]

        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        print(f"  진행: {min(i + BATCH_SIZE, total)}/{total}개 완료")

    print(f"\n인덱싱 완료! 총 {collection.count()}개 저장됨")
    print(f"저장 위치: {CHROMA_DIR}")


def test_search(query: str = "금융 광고 의무 표시 사항"):
    """RAG 검색 테스트"""
    print(f"\n=== 검색 테스트: '{query}' ===")

    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(COLLECTION_NAME)

    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=3,
    )

    for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
        print(f"\n[{i+1}] {meta.get('law_name', meta.get('source', ''))} "
              f"{meta.get('article_no', '')}조")
        print(f"    {doc[:100]}...")


if __name__ == "__main__":
    embed_and_index()
    test_search()
