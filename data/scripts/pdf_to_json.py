"""
PDF → JSON 변환 스크립트
- 단일 PDF 변환 (금융광고규제가이드라인)
- 보도자료 4개 병합 → 광고_위반사례집.json
- 은행 광고심의 기준 → 은행_광고심의_기준.json
실행: python data/scripts/pdf_to_json.py
"""
import fitz
import os
import json

# ============================================================
# 공통 유틸
# ============================================================

def pdf_to_pages(pdf_path: str) -> list:
    """PDF 파일을 페이지별 텍스트 리스트로 변환"""
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text().strip()
        if text:
            pages.append({"page": i + 1, "text": text})
    return pages


# ============================================================
# 1. 단일 PDF 변환 (팀원 원본 유지)
# ============================================================

def convert_single():
    PDF_PATH = "data/raw/guidelines/금융광고규제가이드라인.pdf"
    SAVE_PATH = "data/raw/guidelines/financial_ad_guideline.json"

    if not os.path.exists(PDF_PATH):
        print(f"[경고] 파일 없음: {PDF_PATH}")
        return

    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    pages = pdf_to_pages(PDF_PATH)

    result = {
        "source": "금융광고규제가이드라인",
        "total_pages": len(pages),
        "pages": pages,
    }

    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"저장 완료: {SAVE_PATH}")


# ============================================================
# 2. 보도자료 4개 병합 → 광고_위반사례집.json
# ============================================================

VIOLATION_PDFS = [
    {
        "filename": "250131_(보도자료) 주요 금융상품 광고 점검결과 조치 및 유의사항 안내(대출상품 온라인 광고편).pdf",
        "title": "대출상품 온라인 광고 점검결과 및 유의사항",
    },
    {
        "filename": "250207_(보도자료) 주요 금융상품 광고 점검결과 조치 및 유의사항 안내(② ETF 광고 편).pdf",
        "title": "ETF 광고 점검결과 및 유의사항",
    },
    {
        "filename": "250217_(보도자료) 주요 금융상품 광고 점검결과 유의사항 등 안내(③ 보험상품 온라인 광고 편).pdf",
        "title": "보험상품 온라인 광고 점검결과 및 유의사항",
    },
    {
        "filename": "260305_(보도자료) ETF 광고 및 관련 SNS 컨텐츠를 볼때 투자위험, 총보수 등 5가지 체크포인트를 항상 기억하세요..pdf",
        "title": "ETF 광고 및 SNS 컨텐츠 5가지 체크포인트",
    },
]


def convert_violations():
    PDF_DIR = "data/raw/pdfs"
    OUTPUT_DIR = "data/raw/guidelines"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=== 보도자료 4개 병합 변환 시작 ===")
    documents = []
    for item in VIOLATION_PDFS:
        path = os.path.join(PDF_DIR, item["filename"])
        if not os.path.exists(path):
            print(f"  [경고] 파일 없음: {item['filename']}")
            continue
        pages = pdf_to_pages(path)
        documents.append({
            "title": item["title"],
            "source": item["filename"],
            "pages": pages,
        })
        print(f"  ✅ {item['title']} ({len(pages)}페이지)")

    result = {
        "source": "금융감독원 금융상품 광고 점검결과 보도자료 모음",
        "total_documents": len(documents),
        "documents": documents,
    }

    save_path = os.path.join(OUTPUT_DIR, "ad_violation_cases.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"저장 완료: {save_path}\n")


# ============================================================
# 3. 은행 광고심의 기준 → 은행_광고심의_기준.json
# ============================================================

def convert_bank_standard():
    PDF_DIR = "data/raw/pdfs"
    OUTPUT_DIR = "data/raw/guidelines"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    BANK_PDF = "은행_광고심의_기준_및_은행_광고심의_기준_세칙_1부.pdf"
    bank_path = os.path.join(PDF_DIR, BANK_PDF)

    print("=== 은행 광고심의 기준 변환 시작 ===")
    if not os.path.exists(bank_path):
        print(f"  [경고] 파일 없음: {BANK_PDF}")
        return

    pages = pdf_to_pages(bank_path)
    result = {
        "source": "은행연합회 은행 광고심의 기준 및 세칙",
        "total_pages": len(pages),
        "pages": pages,
    }

    save_path = os.path.join(OUTPUT_DIR, "bank_ad_review_standard.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 은행 광고심의 기준 ({len(pages)}페이지)")
    print(f"저장 완료: {save_path}")


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":
    convert_single()
    print()
    convert_violations()
    convert_bank_standard()
    print("\n전체 변환 완료!")
