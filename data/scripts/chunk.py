"""
규제 데이터 청킹 스크립트
- 법령 JSON → 조항 단위 청킹
- 가이드라인 JSON → 의미 단위 청킹 (500자, overlap 100자)
실행: python data/scripts/chunk.py
"""
import json
import os

RAW_LAWS_DIR = "data/raw/laws"
RAW_GUIDELINES_DIR = "data/raw/guidelines"
OUTPUT_DIR = "data/processed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

CHUNK_SIZE = 500    # 의미 단위 청킹 최대 글자 수
OVERLAP = 100       # 청크 간 겹치는 글자 수


# ============================================================
# 공통 유틸
# ============================================================

def split_by_size(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list:
    """텍스트를 chunk_size 단위로 분할 (overlap 포함)"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


# ============================================================
# 1. 법령 JSON → 조항 단위 청킹
# ============================================================

def chunk_law(filepath: str) -> list:
    """법령 JSON을 조항 단위로 청킹"""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    law_name = data.get("법령명", "")
    chunks = []

    for article in data.get("조문목록", []):
        article_no = article.get("조문번호", "")
        article_title = article.get("조문제목", "")
        article_content = article.get("조문내용", "")

        # 항(sub-articles) 내용 합치기
        sub_contents = [h.get("항내용") or "" for h in article.get("항", [])]
        full_text = article_content + "\n" + "\n".join(sub_contents)
        full_text = full_text.strip()

        if not full_text:
            continue

        chunks.append({
            "text": full_text,
            "metadata": {
                "source_type": "law",
                "law_name": law_name,
                "article_no": article_no,
                "article_title": article_title,
                "source_file": os.path.basename(filepath),
            }
        })

    return chunks


# ============================================================
# 2. 가이드라인 JSON → 의미 단위 청킹
# ============================================================

def chunk_guideline(filepath: str) -> list:
    """가이드라인 JSON을 의미 단위로 청킹"""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    source = data.get("source", "")
    chunks = []

    # ad_violation_cases.json은 documents 구조
    if "documents" in data:
        for doc in data.get("documents", []):
            doc_title = doc.get("title", "")
            for page in doc.get("pages", []):
                text = page.get("text", "").strip()
                page_no = page.get("page", 0)
                if not text:
                    continue
                for i, chunk_text in enumerate(split_by_size(text)):
                    chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            "source_type": "guideline",
                            "source": source,
                            "doc_title": doc_title,
                            "page": page_no,
                            "chunk_index": i,
                            "source_file": os.path.basename(filepath),
                        }
                    })
    # 일반 페이지 구조
    else:
        for page in data.get("pages", []):
            text = page.get("text", "").strip()
            page_no = page.get("page", 0)
            if not text:
                continue
            for i, chunk_text in enumerate(split_by_size(text)):
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "source_type": "guideline",
                        "source": source,
                        "page": page_no,
                        "chunk_index": i,
                        "source_file": os.path.basename(filepath),
                    }
                })

    return chunks


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":
    all_chunks = []

    # 법령 청킹
    print("=== 법령 조항 단위 청킹 ===")
    for filename in os.listdir(RAW_LAWS_DIR):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(RAW_LAWS_DIR, filename)
        chunks = chunk_law(filepath)
        all_chunks.extend(chunks)
        print(f"  ✅ {filename}: {len(chunks)}개 청크")

    # 가이드라인 청킹
    print("\n=== 가이드라인 의미 단위 청킹 ===")
    for filename in os.listdir(RAW_GUIDELINES_DIR):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(RAW_GUIDELINES_DIR, filename)
        chunks = chunk_guideline(filepath)
        all_chunks.extend(chunks)
        print(f"  ✅ {filename}: {len(chunks)}개 청크")

    # 결과 저장
    output_path = os.path.join(OUTPUT_DIR, "chunks.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\n총 {len(all_chunks)}개 청크 저장 완료: {output_path}")
