import fitz
import os
import json

PDF_PATH = "data/raw/guidelines/금융광고규제가이드라인.pdf"
SAVE_PATH = "data/raw/guidelines/financial_ad_guideline.json"

os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

doc = fitz.open(PDF_PATH)

pages = []

for i, page in enumerate(doc):
    text = page.get_text()

    pages.append({
        "page": i + 1,
        "text": text
    })

result = {
    "source": "금융광고규제가이드라인",
    "total_pages": len(pages),
    "pages": pages
}

with open(SAVE_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("저장 완료:", SAVE_PATH)