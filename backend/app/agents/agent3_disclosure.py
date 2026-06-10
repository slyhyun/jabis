"""
Agent 3: 의무표시 체크
- 상품 유형별 Rule Engine JSON 로딩
- mandatory_disclosures: 키워드 미포함 시 위반
- forbidden_expressions: 키워드 포함 시 위반
- forbidden_words: applies_to 필터 후 키워드 포함 시 위반
- conditional 항목: condition_trigger 감지 시에만 체크
"""
import re
import json
import os
from typing import Optional

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_THIS_DIR, "..", "..", ".."))
_RULES_DIR = os.path.join(_PROJECT_ROOT, "data", "rules")

_PRODUCT_TYPE_TO_FILE = {
    "예금": "deposit_rules.json",
    "대출": "loan_rules.json",
    "펀드": "fund_rules.json",
    "카드": "card_rules.json",
}

_rule_cache: dict = {}
_forbidden_words_cache: Optional[dict] = None


# ============================================================
# Rule Engine 로더
# ============================================================

def _load_product_rules(product_type: str) -> Optional[dict]:
    if product_type in _rule_cache:
        return _rule_cache[product_type]
    filename = _PRODUCT_TYPE_TO_FILE.get(product_type)
    if not filename:
        return None
    path = os.path.join(_RULES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _rule_cache[product_type] = data
    return data


def _load_forbidden_words() -> dict:
    global _forbidden_words_cache
    if _forbidden_words_cache is None:
        path = os.path.join(_RULES_DIR, "forbidden_words.json")
        with open(path, "r", encoding="utf-8") as f:
            _forbidden_words_cache = json.load(f)
    return _forbidden_words_cache


# ============================================================
# 위반 항목 생성 헬퍼
# ============================================================

def _make_violation(vid: str, severity: str, item: str,
                    message: str, legal_basis: str = "") -> dict:
    return {
        "id": vid,
        "severity": severity,
        "source": "disclosure",
        "item": item,
        "message": message,
        "legal_basis": legal_basis,
    }


# ============================================================
# 체크 로직
# ============================================================

def _check_mandatory_disclosures(ad_copy: str, rules: dict) -> list[dict]:
    """의무표시 누락 체크: check_keywords 중 하나라도 없으면 위반"""
    violations = []
    for item in rules.get("mandatory_disclosures", []):
        # conditional 항목: condition_trigger 중 하나라도 없으면 스킵
        if item.get("conditional"):
            triggered = any(
                trigger in ad_copy
                for trigger in item.get("condition_trigger", [])
            )
            if not triggered:
                continue

        keywords = item.get("check_keywords", [])
        if keywords and not any(kw in ad_copy for kw in keywords):
            violations.append(_make_violation(
                vid=item["id"],
                severity=item.get("severity", "MEDIUM"),
                item=item.get("item", ""),
                message=item.get("violation_message", "의무표시 누락"),
                legal_basis=item.get("legal_basis", ""),
            ))
    return violations


def _check_forbidden_expressions(ad_copy: str, rules: dict) -> list[dict]:
    """금지표현 체크: keywords/patterns 중 하나라도 있으면 위반"""
    violations = []
    for item in rules.get("forbidden_expressions", []):
        hit = False
        for kw in item.get("keywords", []):
            if kw in ad_copy:
                hit = True
                break

        if not hit:
            for pattern in item.get("patterns", []):
                try:
                    if re.search(pattern, ad_copy):
                        hit = True
                        break
                except re.error:
                    pass

        if hit:
            violations.append(_make_violation(
                vid=item["id"],
                severity=item.get("severity", "HIGH"),
                item=item.get("description", ""),
                message=item.get("violation_message", "금지표현 사용"),
                legal_basis=item.get("legal_basis", ""),
            ))
    return violations


def _check_forbidden_words(ad_copy: str, product_type: str) -> list[dict]:
    """금지어 체크: applies_to 필터 후 keywords/patterns 매칭"""
    fw = _load_forbidden_words()
    violations = []
    for cat in fw.get("categories", []):
        applies_to = cat.get("applies_to", ["전체"])
        if "전체" not in applies_to and product_type not in applies_to:
            continue

        hit = False
        for kw in cat.get("keywords", []):
            if kw in ad_copy:
                hit = True
                break

        if not hit:
            for pattern in cat.get("patterns", []):
                try:
                    if re.search(pattern, ad_copy):
                        hit = True
                        break
                except re.error:
                    pass

        if hit:
            violations.append(_make_violation(
                vid=cat["id"],
                severity=cat.get("severity", "HIGH"),
                item=cat.get("category", ""),
                message=cat.get("violation_message", "금지어 사용"),
                legal_basis=cat.get("legal_basis", ""),
            ))
    return violations


# ============================================================
# Agent 3 메인 함수
# ============================================================

def run_agent3(ad_copy: str, product_type: str) -> dict:
    """
    Agent 3: 의무표시 체크 실행
    - ad_copy: 심의 대상 광고 카피
    - product_type: 상품 유형 (예금, 대출, 펀드, 카드)
    """
    print(f"[Agent 3] 의무표시 체크 시작 — product_type={product_type}")

    rules = _load_product_rules(product_type)
    if rules is None:
        print(f"[Agent 3] 경고: '{product_type}'에 해당하는 Rule Engine 파일이 없습니다.")
        return {
            "disclosure_violations": [],
            "warning": f"No rule file for product_type '{product_type}'",
        }

    mandatory_violations = _check_mandatory_disclosures(ad_copy, rules)
    forbidden_expr_violations = _check_forbidden_expressions(ad_copy, rules)
    forbidden_word_violations = _check_forbidden_words(ad_copy, product_type)

    all_violations = mandatory_violations + forbidden_expr_violations + forbidden_word_violations

    print(f"[Agent 3] 완료 — 의무표시 누락 {len(mandatory_violations)}건 / "
          f"금지표현 {len(forbidden_expr_violations)}건 / "
          f"금지어 {len(forbidden_word_violations)}건")

    return {
        "disclosure_violations": all_violations,
        "detail": {
            "mandatory_missing": mandatory_violations,
            "forbidden_expressions": forbidden_expr_violations,
            "forbidden_words": forbidden_word_violations,
        },
    }


# ============================================================
# 동작 테스트
# ============================================================

if __name__ == "__main__":
    tests = [
        {
            "label": "예금 - 의무표시 누락 (가입조건, 예금자보호 없음)",
            "ad_copy": "JB 주거래 우대 정기예금 연 5.0% (세전). 지금 바로 가입하세요!",
            "product_type": "예금",
        },
        {
            "label": "대출 - 정상 카피",
            "ad_copy": (
                "JB 직장인 신용대출 연 4.5%~7.5% (연체이자율 최고 연 15%). "
                "재직기간 6개월 이상 직장인, 개인신용평점 700점 이상 (KCB 기준). "
                "중도상환수수료: 잔여원금의 1.2% (3년 이내). "
                "원리금균등 분할상환."
            ),
            "product_type": "대출",
        },
        {
            "label": "펀드 - 금지어(원금보장) + 의무표시 누락",
            "ad_copy": "JB KOSPI 200 ETF 총보수 연 0.05%. 위험등급 3등급. 원금 보장 상품!",
            "product_type": "펀드",
        },
        {
            "label": "카드 - 혜택만 강조, 조건 미표시",
            "ad_copy": "JB 클래식 신용카드 편의점 5% 할인! 연회비: 15,000원.",
            "product_type": "카드",
        },
    ]

    for t in tests:
        print(f"\n{'='*55}")
        print(f"[테스트] {t['label']}")
        result = run_agent3(t["ad_copy"], t["product_type"])
        violations = result["disclosure_violations"]
        if violations:
            for v in violations:
                print(f"  [{v['severity']}] [{v['id']}] {v['message']}")
        else:
            print("  위반 없음")
