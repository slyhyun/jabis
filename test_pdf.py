import fitz

pdf_path = "data/raw/guidelines/금융광고규제가이드라인.pdf"

doc = fitz.open(pdf_path)

print("페이지 수:", len(doc))

for i, page in enumerate(doc):
    text = page.get_text()
    print(f"\n=== PAGE {i+1} ===")
    print(text[:500])

print(text[:1000])