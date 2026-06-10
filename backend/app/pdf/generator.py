"""
PDF 심의서 생성 모듈 (ReportLab)
- 표지
- 위반 항목 목록
- 근거 조항
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os
import datetime

# ============================================================
# 한글 폰트 등록
# ============================================================

_FONT_REGISTERED = False
_FONT_NAME = "NanumGothic"
_FONT_BOLD_NAME = "NanumGothicBold"

def _register_fonts():
    global _FONT_REGISTERED, _FONT_NAME, _FONT_BOLD_NAME
    if _FONT_REGISTERED:
        return
    font_dir = os.path.join(os.path.dirname(__file__), "fonts")
    regular = os.path.join(font_dir, "NanumGothic.ttf")
    bold = os.path.join(font_dir, "NanumGothicBold.ttf")
    if os.path.exists(regular):
        pdfmetrics.registerFont(TTFont(_FONT_NAME, regular))
    else:
        _FONT_NAME = "Helvetica"
        _FONT_BOLD_NAME = "Helvetica-Bold"
        _FONT_REGISTERED = True
        return
    if os.path.exists(bold):
        pdfmetrics.registerFont(TTFont(_FONT_BOLD_NAME, bold))
    else:
        _FONT_BOLD_NAME = _FONT_NAME
    _FONT_REGISTERED = True


# ============================================================
# 스타일 정의
# ============================================================

_JABIS_BLUE = colors.HexColor("#003087")   # JB금융 블루
_JABIS_RED  = colors.HexColor("#C8102E")   # HIGH 위험도 레드
_JABIS_GRAY = colors.HexColor("#6C757D")

def _get_styles():
    _register_fonts()
    base = getSampleStyleSheet()

    styles = {
        "cover_title": ParagraphStyle(
            "cover_title",
            fontName=_FONT_BOLD_NAME,
            fontSize=24,
            textColor=_JABIS_BLUE,
            spaceAfter=6,
            leading=32,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            fontName=_FONT_NAME,
            fontSize=13,
            textColor=_JABIS_GRAY,
            spaceAfter=4,
        ),
        "section_header": ParagraphStyle(
            "section_header",
            fontName=_FONT_BOLD_NAME,
            fontSize=13,
            textColor=_JABIS_BLUE,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body",
            fontName=_FONT_NAME,
            fontSize=10,
            leading=16,
            spaceAfter=4,
        ),
        "body_bold": ParagraphStyle(
            "body_bold",
            fontName=_FONT_BOLD_NAME,
            fontSize=10,
            leading=16,
            spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "small",
            fontName=_FONT_NAME,
            fontSize=8,
            textColor=_JABIS_GRAY,
            leading=12,
        ),
        "risk_high": ParagraphStyle(
            "risk_high",
            fontName=_FONT_BOLD_NAME,
            fontSize=14,
            textColor=_JABIS_RED,
        ),
        "risk_medium": ParagraphStyle(
            "risk_medium",
            fontName=_FONT_BOLD_NAME,
            fontSize=14,
            textColor=colors.HexColor("#FFA500"),
        ),
        "risk_low": ParagraphStyle(
            "risk_low",
            fontName=_FONT_BOLD_NAME,
            fontSize=14,
            textColor=colors.HexColor("#28A745"),
        ),
    }
    return styles


# ============================================================
# 헬퍼
# ============================================================

_SEVERITY_KO = {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}
_STATUS_KO   = {"APPROVED": "승인", "REJECTED": "반려", "PENDING": "보류"}
_PRODUCT_KO  = {"예금": "예금", "대출": "대출", "펀드": "펀드·ETF", "카드": "카드"}


def _severity_color(severity: str) -> colors.Color:
    return {
        "HIGH": _JABIS_RED,
        "MEDIUM": colors.HexColor("#FFA500"),
        "LOW": colors.HexColor("#28A745"),
    }.get(severity, colors.black)


# ============================================================
# 섹션 빌더
# ============================================================

def _build_cover(record, styles: dict) -> list:
    """표지"""
    _register_fonts()
    now = datetime.datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    status_ko = _STATUS_KO.get(record.review_status or "PENDING", "보류")
    risk_ko   = _SEVERITY_KO.get(record.risk_level or "LOW", "낮음")
    risk_style_key = {"HIGH": "risk_high", "MEDIUM": "risk_medium", "LOW": "risk_low"}.get(
        record.risk_level or "LOW", "risk_low"
    )

    elements = [
        Spacer(1, 30 * mm),
        Paragraph("JABIS", styles["cover_title"]),
        Paragraph("금융 광고 카피 자동 심의 리포트", styles["cover_sub"]),
        HRFlowable(width="100%", thickness=2, color=_JABIS_BLUE, spaceAfter=10),
        Spacer(1, 10 * mm),
        Paragraph(f"심의 번호: #{record.id}", styles["body_bold"]),
        Paragraph(f"상품 유형: {_PRODUCT_KO.get(record.product_type or '', record.product_type or '')}", styles["body"]),
        Paragraph(f"심의 일시: {now}", styles["body"]),
        Paragraph(f"심의 상태: {status_ko}", styles["body"]),
        Spacer(1, 8 * mm),
        Paragraph("종합 위험도", styles["section_header"]),
        Paragraph(risk_ko, styles[risk_style_key]),
        Spacer(1, 4 * mm),
        Paragraph(record.risk_summary or "", styles["body"]),
        Spacer(1, 10 * mm),
        Paragraph("심의 대상 광고 카피", styles["section_header"]),
        Paragraph(record.ad_copy or "", styles["body"]),
        PageBreak(),
    ]
    return elements


def _build_violations(record, styles: dict) -> list:
    """위반 항목 + 근거 조항"""
    violations = record.violations or []
    elements = [
        Paragraph("위반 항목 및 근거 조항", styles["section_header"]),
        HRFlowable(width="100%", thickness=1, color=_JABIS_BLUE, spaceAfter=6),
    ]

    if not violations:
        elements.append(Paragraph("감지된 위반 항목이 없습니다.", styles["body"]))
        return elements

    # 심각도 순 정렬
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    sorted_v = sorted(violations, key=lambda v: order.get(v.get("severity", "LOW"), 2))

    table_data = [["심각도", "항목 코드", "구분", "위반 내용"]]
    for v in sorted_v:
        severity = v.get("severity", "")
        vid      = v.get("id", "")
        source   = "스펙 불일치" if v.get("source") == "spec" else "의무표시/금지표현"
        message  = v.get("message", "")
        table_data.append([severity, vid, source, message])

    col_widths = [22 * mm, 35 * mm, 35 * mm, None]
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        ("BACKGROUND",   (0, 0), (-1, 0),  _JABIS_BLUE),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  _FONT_BOLD_NAME),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("FONTNAME",     (0, 1), (-1, -1), _FONT_NAME),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]

    # HIGH 항목 행 강조
    for i, v in enumerate(sorted_v, start=1):
        if v.get("severity") == "HIGH":
            style_cmds.append(("TEXTCOLOR", (0, i), (0, i), _JABIS_RED))
            style_cmds.append(("FONTNAME",  (0, i), (0, i), _FONT_BOLD_NAME))

    tbl.setStyle(TableStyle(style_cmds))
    elements.append(tbl)
    elements.append(Spacer(1, 6 * mm))
    return elements


# ============================================================
# 메인 생성 함수 (표지 + 위반 항목까지)
# ============================================================

def generate_pdf(record) -> bytes:
    """
    PDF 심의서 생성 (표지 + 위반 항목 + 근거 조항)
    record: ReviewHistory ORM 객체 또는 동일한 필드를 가진 객체
    """
    _register_fonts()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = _get_styles()
    elements = []
    elements += _build_cover(record, styles)
    elements += _build_violations(record, styles)

    doc.build(elements)
    return buf.getvalue()


# ============================================================
# 동작 테스트
# ============================================================

if __name__ == "__main__":
    class MockRecord:
        id = 1
        ad_copy = "JB 주거래 우대 정기예금 연 6.0% 확정금리! 지금 바로 가입하세요."
        product_type = "예금"
        product_id = "JB-DEP-001"
        risk_level = "HIGH"
        risk_summary = (
            "광고 금리가 실제 상품 최고금리를 초과하며, 가입조건 및 예금자보호 한도 표시가 누락되었습니다. "
            "확정금리 표현은 금융소비자보호법 제22조 위반에 해당합니다."
        )
        revised_copy = (
            "JB 주거래 우대 정기예금 우대조건 충족 시 최고 연 5.0% (세전).\n"
            "※ 가입대상: 만 17세 이상 개인 (비대면 전용)\n"
            "※ 예금자보호법에 따라 1인당 최고 5천만원까지 보호됩니다."
        )
        review_status = "PENDING"
        violations = [
            {"id": "SPEC-DEP-001", "severity": "HIGH", "source": "spec",
             "item": "max_rate", "message": "광고 금리(6.0%)가 실제 최고금리(5.0%)를 초과합니다."},
            {"id": "DEP-M-001", "severity": "HIGH", "source": "disclosure",
             "item": "가입조건", "message": "가입조건을 반드시 표시해야 합니다."},
            {"id": "FW-001", "severity": "HIGH", "source": "disclosure",
             "item": "확정적_단정적_표현", "message": "불확실한 사항을 확정적으로 표시하는 행위는 금지됩니다."},
            {"id": "DEP-M-003", "severity": "MEDIUM", "source": "disclosure",
             "item": "이자_지급시기", "message": "이자 지급 시기 및 중도해지 제한 사항을 표시해야 합니다."},
        ]
        multilingual = {}

    record = MockRecord()
    pdf_bytes = generate_pdf(record)

    out_path = "/tmp/jabis_test_review.pdf"
    with open(out_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"PDF 생성 완료: {out_path} ({len(pdf_bytes):,} bytes)")
