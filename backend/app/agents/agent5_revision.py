"""
Agent 5: 수정안 생성
- 원본 카피 + 위반 항목 입력
- 의무표시 자동 삽입 (rule-based)
- LLM으로 수정 카피 생성 (마케팅 의도 보존)
"""
import os
from openai import OpenAI

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
    return _client


# ============================================================
# 의무표시 자동 삽입 (rule-based)
# ============================================================

# 상품 유형별 기본 의무 문구 템플릿
_MANDATORY_TEMPLATES = {
    "예금": {
        "DEP-M-001": "※ 가입대상: {eligible}",
        "DEP-M-004": "※ 이 예금은 예금자보호법에 따라 1인당 최고 5천만원까지 보호됩니다.",
        "DEP-M-003": "※ 중도해지 시 약정금리보다 낮은 금리가 적용될 수 있습니다.",
        "DEP-M-006": "※ 표시 금리는 세전 기준이며, 이자소득세(15.4%) 적용 시 실수령액이 다를 수 있습니다.",
    },
    "대출": {
        "LOAN-M-001": "※ 대출자격: {eligible}",
        "LOAN-M-002": "※ 대출금리: 연 {min_rate}%~{max_rate}% (연체이자율 최고 연 {overdue_rate}%)",
        "LOAN-M-005": "※ 중도상환수수료: 잔여원금의 {prepayment_fee_rate}% (대출 후 {prepayment_fee_period_months}개월 이내)",
        "LOAN-M-008": "※ 개인신용평점에 따라 대출 가능 여부 및 금리가 달라질 수 있습니다.",
    },
    "펀드": {
        "FUND-M-001": "※ 이 상품은 원금 손실이 발생할 수 있습니다.",
        "FUND-M-003": "※ 총보수: 연 {total_fee_rate}%",
        "FUND-M-004": "※ 위험등급: {risk_grade}등급 ({risk_label})",
        "FUND-M-005": "※ 투자 전 상품설명서 및 약관을 반드시 확인하세요.",
    },
    "카드": {
        "CARD-M-001": "※ 연회비: {annual_fee_domestic}원",
        "CARD-M-002": "※ 혜택 적용 조건: 전월 실적 {min_monthly_spend}원 이상, 월 한도 {monthly_limit}원",
        "CARD-M-005": "※ 연체이자율: 최고 연 {overdue_rate}%",
    },
}


def _build_mandatory_hints(disclosure_violations: list, product_type: str, product: dict) -> list[str]:
    """의무표시 누락 위반 항목에 대한 삽입 문구 생성"""
    templates = _MANDATORY_TEMPLATES.get(product_type, {})
    hints = []
    seen = set()

    for v in disclosure_violations:
        vid = v.get("id", "")
        if vid in seen or vid not in templates:
            continue
        seen.add(vid)
        try:
            hint = templates[vid].format(**product)
            hints.append(hint)
        except KeyError:
            hints.append(templates[vid].split("{")[0].rstrip(": "))

    return hints


# ============================================================
# LLM 프롬프트 구성
# ============================================================

def _build_prompt(ad_copy: str, product_type: str,
                  violations: list, mandatory_hints: list[str],
                  risk_level: str) -> str:

    # 위반 항목 분류
    forbidden = [v for v in violations if v.get("source") == "disclosure"
                 and "금지" in v.get("item", "")]
    spec_issues = [v for v in violations if v.get("source") == "spec"]
    missing = [v for v in violations if v.get("source") == "disclosure"
               and "금지" not in v.get("item", "")]

    def fmt(items):
        return "\n".join(f"  - [{v['id']}] {v['message']}" for v in items) or "  없음"

    hints_text = "\n".join(f"  {h}" for h in mandatory_hints) if mandatory_hints else "  없음"

    return f"""당신은 금융 광고 카피라이터 겸 준법 전문가입니다.
아래 광고 카피를 금융 규제에 맞게 수정하되, 마케팅 의도와 핵심 메시지를 최대한 보존하세요.

[원본 광고 카피]
{ad_copy}

[상품 유형]
{product_type}

[종합 위험도]
{risk_level}

[수정 필요 사항]

1. 금지표현 제거 또는 완화:
{fmt(forbidden)}

2. 스펙 불일치 수정:
{fmt(spec_issues)}

3. 의무표시 누락 — 아래 문구를 반드시 포함:
{hints_text}

[수정 지침]
- 원본의 마케팅 의도(혜택 강조, 브랜드 톤)를 유지하세요
- 금지표현은 사실에 기반한 표현으로 대체하세요
  예) "확정금리" → "우대조건 충족 시 연 X%" / "무조건" → "조건 충족 시"
- 의무표시 문구는 광고 하단에 작은 글씨 형태(※)로 추가하세요
- 수정된 카피만 출력하고, 설명이나 주석은 포함하지 마세요
- 자연스러운 한국어로 작성하세요"""


# ============================================================
# Agent 5 메인 함수
# ============================================================

def run_agent5(ad_copy: str, product_type: str,
               all_violations: list, risk_level: str,
               product: dict = None) -> dict:
    """
    Agent 5: 수정안 생성
    - ad_copy: 원본 광고 카피
    - product_type: 상품 유형
    - all_violations: Agent 4에서 통합된 위반 목록
    - risk_level: 위험도
    - product: Mock DB 상품 정보 (의무표시 문구 채우기용)
    """
    print(f"[Agent 5] 수정안 생성 시작 — 위반 {len(all_violations)}건")

    disclosure_violations = [v for v in all_violations if v.get("source") == "disclosure"]
    mandatory_hints = _build_mandatory_hints(
        disclosure_violations, product_type, product or {}
    )

    prompt = _build_prompt(ad_copy, product_type, all_violations, mandatory_hints, risk_level)

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gemini-2.0-flash"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=800,
        )
        revised_copy = response.choices[0].message.content.strip()
        print(f"[Agent 5] LLM 수정안 생성 완료")
    except Exception as e:
        print(f"[Agent 5] LLM 오류: {e}")
        revised_copy = _fallback_revision(ad_copy, mandatory_hints)

    return {"revised_copy": revised_copy}


def _fallback_revision(ad_copy: str, mandatory_hints: list[str]) -> str:
    """LLM 실패 시 의무표시만 원본 하단에 추가"""
    if not mandatory_hints:
        return ad_copy
    hints_text = "\n".join(mandatory_hints)
    return f"{ad_copy}\n\n{hints_text}"


# ============================================================
# 동작 테스트
# ============================================================

if __name__ == "__main__":
    mock_violations = [
        {"id": "SPEC-DEP-001", "severity": "HIGH", "source": "spec",
         "message": "광고 금리(6.0%)가 실제 최고금리(5.0%)를 초과합니다.", "item": "max_rate"},
        {"id": "DEP-M-001", "severity": "HIGH", "source": "disclosure",
         "message": "가입조건을 반드시 표시해야 합니다.", "item": "가입조건"},
        {"id": "DEP-M-004", "severity": "HIGH", "source": "disclosure",
         "message": "예금자보호 한도(5천만원)를 반드시 명시해야 합니다.", "item": "예금자보호_부보내용"},
        {"id": "FW-001", "severity": "HIGH", "source": "disclosure",
         "message": "확정적으로 표시하는 행위는 금지됩니다.", "item": "확정적_단정적_표현"},
    ]

    mock_product = {
        "eligible": "만 17세 이상 개인 (비대면 전용)",
        "max_rate": 5.0,
        "base_rate": 3.0,
    }

    result = run_agent5(
        ad_copy="JB 주거래 우대 정기예금 연 6.0% 확정금리! 지금 바로 가입하세요.",
        product_type="예금",
        all_violations=mock_violations,
        risk_level="HIGH",
        product=mock_product,
    )

    print(f"\n=== 수정안 ===")
    print(result["revised_copy"])
