"""
Agent 4: 종합 위험도 판단
- Agent 1(규제검색), 2(스펙검증), 3(의무표시) 결과 통합
- Rule-based 위험도 산출 (HIGH / MEDIUM / LOW)
- 위반 항목 우선순위 정렬
- LLM으로 위험도 요약 생성
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
# 위반 통합 및 정렬
# ============================================================

_SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def _aggregate_violations(spec_violations: list, disclosure_violations: list) -> list:
    """Agent 2, 3 위반 항목에 출처 태그 추가 후 통합"""
    result = []
    for v in spec_violations:
        result.append({**v, "source": "spec"})
    for v in disclosure_violations:
        result.append({**v, "source": "disclosure"})
    return result


def _sort_by_severity(violations: list) -> list:
    return sorted(violations, key=lambda v: _SEVERITY_ORDER.get(v.get("severity", "LOW"), 2))


def _calculate_risk_level(violations: list) -> str:
    severities = {v.get("severity", "LOW") for v in violations}
    if "HIGH" in severities:
        return "HIGH"
    if "MEDIUM" in severities:
        return "MEDIUM"
    return "LOW"


# ============================================================
# LLM 요약 생성
# ============================================================

def _build_prompt(ad_copy: str, product_type: str,
                  violations: list, risk_level: str,
                  regulation_results) -> str:
    risk_label = {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}.get(risk_level, risk_level)

    violation_lines = []
    for v in violations:
        src = "스펙 불일치" if v.get("source") == "spec" else "의무표시 누락/금지표현"
        severity = v.get("severity", "")
        vid = v.get("id", "")
        msg = v.get("message", "")
        violation_lines.append(f"  - [{severity}][{vid}][{src}] {msg}")

    violations_text = "\n".join(violation_lines) if violation_lines else "  (위반 없음)"

    # Agent 1 규제 출처 목록
    sources_text = ""
    if isinstance(regulation_results, dict):
        sources = regulation_results.get("sources", [])
        if sources:
            sources_text = "\n관련 규제 출처:\n" + "\n".join(f"  - {s}" for s in sources[:5])

    return f"""당신은 금융 광고 심의 전문가입니다. 아래 광고 카피 심의 결과를 바탕으로 한국어로 간결하게 위험도 요약을 작성하세요.

[심의 대상 광고]
상품 유형: {product_type}
광고 카피: {ad_copy}

[종합 위험도]
{risk_label} ({risk_level})

[위반 항목 목록]
{violations_text}
{sources_text}

[작성 지침]
- 3~5문장으로 작성
- 위험도 판단 근거를 구체적으로 설명
- 가장 심각한 위반부터 언급
- 광고주가 이해하기 쉬운 표현 사용
- 규제 조항 인용 시 괄호로 표시"""


def _generate_summary(ad_copy: str, product_type: str,
                      violations: list, risk_level: str,
                      regulation_results) -> str:
    prompt = _build_prompt(ad_copy, product_type, violations, risk_level, regulation_results)
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gemini-2.0-flash"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Agent 4] LLM 오류: {e}")
        return _fallback_summary(violations, risk_level)


def _fallback_summary(violations: list, risk_level: str) -> str:
    """LLM 호출 실패 시 rule-based 요약"""
    risk_label = {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}.get(risk_level, risk_level)
    high = [v for v in violations if v.get("severity") == "HIGH"]
    medium = [v for v in violations if v.get("severity") == "MEDIUM"]

    parts = [f"종합 위험도: {risk_label}. 총 {len(violations)}건의 위반이 감지되었습니다."]
    if high:
        parts.append(f"HIGH 위반 {len(high)}건: " + ", ".join(v.get("id", "") for v in high[:3]))
    if medium:
        parts.append(f"MEDIUM 위반 {len(medium)}건: " + ", ".join(v.get("id", "") for v in medium[:3]))
    return " ".join(parts)


# ============================================================
# Agent 4 메인 함수
# ============================================================

def run_agent4(ad_copy: str, product_type: str,
               regulation_results, spec_violations: list,
               disclosure_violations: list) -> dict:
    """
    Agent 4: 종합 위험도 판단 실행
    - ad_copy: 심의 대상 광고 카피
    - product_type: 상품 유형
    - regulation_results: Agent 1 결과
    - spec_violations: Agent 2 결과
    - disclosure_violations: Agent 3 결과
    """
    print(f"[Agent 4] 종합 위험도 판단 시작")

    all_violations = _aggregate_violations(spec_violations, disclosure_violations)
    risk_level = _calculate_risk_level(all_violations)
    sorted_violations = _sort_by_severity(all_violations)

    print(f"[Agent 4] 위반 총 {len(sorted_violations)}건 — 위험도: {risk_level}")

    risk_summary = _generate_summary(
        ad_copy, product_type, sorted_violations, risk_level, regulation_results
    )

    print(f"[Agent 4] 완료")
    return {
        "risk_level": risk_level,
        "risk_summary": risk_summary,
        "all_violations": sorted_violations,
    }


# ============================================================
# 동작 테스트
# ============================================================

if __name__ == "__main__":
    # Agent 2, 3 결과 모의 데이터
    mock_spec = [
        {
            "id": "SPEC-DEP-001", "severity": "HIGH",
            "field": "max_rate", "product_id": "JB-DEP-001",
            "message": "광고 금리(6.0%)가 실제 상품 최고금리(5.0%)를 초과합니다.",
        }
    ]
    mock_disclosure = [
        {
            "id": "DEP-M-001", "severity": "HIGH",
            "item": "가입조건",
            "message": "예금성 상품 광고에는 가입조건을 반드시 표시해야 합니다.",
        },
        {
            "id": "DEP-M-004", "severity": "HIGH",
            "item": "예금자보호_부보내용",
            "message": "예금자보호 여부 및 1인당 보호 한도(5천만원)를 반드시 명시해야 합니다.",
        },
        {
            "id": "FW-001", "severity": "HIGH",
            "item": "확정적_단정적_표현",
            "message": "불확실한 사항을 확정적으로 표시하는 행위는 금지됩니다.",
        },
        {
            "id": "DEP-M-003", "severity": "MEDIUM",
            "item": "이자_지급시기",
            "message": "이자 지급 시기 및 중도해지 시 이자 제한 사항을 표시해야 합니다.",
        },
    ]

    result = run_agent4(
        ad_copy="JB 주거래 우대 정기예금 연 6.0% 확정금리! 지금 바로 가입하세요.",
        product_type="예금",
        regulation_results={"sources": ["금융소비자보호법 제22조", "은행 광고심의 기준 제17조"]},
        spec_violations=mock_spec,
        disclosure_violations=mock_disclosure,
    )

    print(f"\n=== Agent 4 결과 ===")
    print(f"위험도: {result['risk_level']}")
    print(f"요약:\n{result['risk_summary']}")
    print(f"\n정렬된 위반 항목:")
    for v in result["all_violations"]:
        print(f"  [{v['severity']}][{v['source']}] {v['id']} — {v['message'][:60]}")
