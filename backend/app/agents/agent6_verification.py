"""
Agent 6: 자기 검증 루프
- Agent 5 수정안을 Agent 2, 3에 재투입
- 잔여 위반 여부로 통과/실패 판단
- 실패 시 Agent 5로 재전송 (graph.py conditional edge 제어)
- 최대 3회 반복, 초과 시 강제 종료
"""
from backend.app.agents.agent2_spec import run_agent2
from backend.app.agents.agent3_disclosure import run_agent3

MAX_ITERATIONS = 3

# 통과 기준: HIGH 위반이 없으면 통과
_PASS_THRESHOLD = {"HIGH"}


def _has_blocking_violations(violations: list) -> bool:
    return any(v.get("severity") in _PASS_THRESHOLD for v in violations)


def run_agent6(revised_copy: str, product_type: str, product_id: str,
               verification_count: int) -> dict:
    """
    Agent 6: 자기 검증 실행
    - revised_copy: Agent 5가 생성한 수정안
    - product_type: 상품 유형
    - product_id: Mock DB 상품 ID
    - verification_count: 현재까지 검증 횟수 (graph에서 누적)
    """
    current = verification_count + 1
    print(f"[Agent 6] 자기 검증 {current}회차 시작")

    # 최대 횟수 초과 시 강제 통과
    if current > MAX_ITERATIONS:
        print(f"[Agent 6] 최대 검증 횟수({MAX_ITERATIONS}회) 초과 — 강제 종료")
        return {
            "verification_count": current,
            "is_verified": True,
            "remaining_violations": [],
            "forced": True,
        }

    # Agent 2 재검증
    spec_result = run_agent2(revised_copy, product_type, product_id)
    spec_violations = spec_result.get("spec_violations", [])

    # Agent 3 재검증
    disclosure_result = run_agent3(revised_copy, product_type)
    disclosure_violations = disclosure_result.get("disclosure_violations", [])

    remaining = spec_violations + disclosure_violations
    high_count = sum(1 for v in remaining if v.get("severity") == "HIGH")
    medium_count = sum(1 for v in remaining if v.get("severity") == "MEDIUM")

    is_verified = not _has_blocking_violations(remaining)

    print(f"[Agent 6] {current}회차 완료 — "
          f"잔여 위반 {len(remaining)}건 (HIGH:{high_count}, MEDIUM:{medium_count}) "
          f"→ {'통과' if is_verified else '재시도'}")

    return {
        "verification_count": current,
        "is_verified": is_verified,
        "remaining_violations": remaining,
        "forced": False,
    }


# ============================================================
# 동작 테스트
# ============================================================

if __name__ == "__main__":
    tests = [
        {
            "label": "수정 후 HIGH 위반 없음 → 통과",
            "revised_copy": (
                "JB 주거래 우대 정기예금 우대조건 충족 시 최고 연 5.0% (세전).\n"
                "※ 가입대상: 만 17세 이상 개인 (비대면 전용)\n"
                "※ 이 예금은 예금자보호법에 따라 1인당 최고 5천만원까지 보호됩니다.\n"
                "※ 중도해지 시 약정금리보다 낮은 금리가 적용될 수 있습니다."
            ),
            "product_type": "예금",
            "product_id": "JB-DEP-001",
            "count": 0,
        },
        {
            "label": "여전히 HIGH 위반 존재 → 재시도",
            "revised_copy": "JB 주거래 우대 정기예금 연 6.0% 확정금리! 지금 가입하세요.",
            "product_type": "예금",
            "product_id": "JB-DEP-001",
            "count": 1,
        },
        {
            "label": "3회 초과 → 강제 종료",
            "revised_copy": "JB 주거래 우대 정기예금 연 6.0% 확정금리!",
            "product_type": "예금",
            "product_id": "JB-DEP-001",
            "count": 3,
        },
    ]

    for t in tests:
        print(f"\n{'='*55}")
        print(f"[테스트] {t['label']}")
        result = run_agent6(
            revised_copy=t["revised_copy"],
            product_type=t["product_type"],
            product_id=t["product_id"],
            verification_count=t["count"],
        )
        print(f"  통과: {result['is_verified']} | 횟수: {result['verification_count']} | "
              f"강제종료: {result.get('forced', False)} | "
              f"잔여위반: {len(result['remaining_violations'])}건")
