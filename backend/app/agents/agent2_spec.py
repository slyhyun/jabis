"""
Agent 2: 스펙 교차 검증
- 광고 카피에서 숫자/조건 추출 (정규식 기반)
- Mock 상품 DB와 비교하여 불일치 항목 반환
- LLM 미사용, 코드 위주
"""
import re
import json
import os
from typing import Optional

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_THIS_DIR, "..", "..", ".."))
MOCK_DB_PATH = os.getenv(
    "MOCK_DB_PATH",
    os.path.join(_PROJECT_ROOT, "data", "mock_db", "products.json"),
)

_mock_db: Optional[dict] = None


def _load_mock_db() -> dict:
    global _mock_db
    if _mock_db is None:
        with open(MOCK_DB_PATH, "r", encoding="utf-8") as f:
            _mock_db = json.load(f)
    return _mock_db


# ============================================================
# 추출 함수
# ============================================================

def extract_rates(text: str) -> list[float]:
    """광고 카피에서 단일 이자율(%) 추출. 예: '연 5.0%', '연5%', '금리 3.5%'"""
    patterns = [
        r'연\s*(\d+\.?\d*)\s*%',
        r'(\d+\.?\d*)\s*%\s*(?:금리|이자율|수익률)',
        r'(?:금리|이자율)\s*(\d+\.?\d*)\s*%',
    ]
    results = set()
    for p in patterns:
        for m in re.finditer(p, text):
            results.add(float(m.group(1)))
    return list(results)


def extract_rate_range(text: str) -> Optional[tuple[float, float]]:
    """범위 금리 추출. 예: '연 4.5%~7.5%', '4.5%∼7.5%'"""
    pattern = r'(?:연\s*)?(\d+\.?\d*)\s*%\s*[~～∼]\s*(\d+\.?\d*)\s*%'
    m = re.search(pattern, text)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None


def extract_overdue_rate(text: str) -> Optional[float]:
    """연체이자율 추출. 예: '연체이자율 최고 연 15%', '연체금리 연 12%'"""
    patterns = [
        r'연체[이자율금리]*\s*(?:최고)?\s*연\s*(\d+\.?\d*)\s*%',
        r'연체\s*(?:최고)?\s*(\d+\.?\d*)\s*%',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return float(m.group(1))
    return None


def extract_annual_fee(text: str) -> Optional[int]:
    """연회비 추출. 예: '연회비 15,000원', '연회비 1만5천원', '연회비 없음'"""
    if re.search(r'연회비\s*:?\s*(?:없음|무료|면제|0원)', text):
        return 0
    # X만원
    m = re.search(r'연회비\s*:?\s*(\d+)\s*만\s*원', text)
    if m:
        return int(m.group(1)) * 10000
    # X,XXX원 또는 XXXXX원
    m = re.search(r'연회비\s*:?\s*([\d,]+)\s*원', text)
    if m:
        return int(m.group(1).replace(",", ""))
    return None


def extract_total_fee(text: str) -> Optional[float]:
    """펀드 총보수 추출. 예: '총보수 연 0.05%', '운용보수 0.03%'"""
    patterns = [
        r'총보수\s*:?\s*연?\s*(\d+\.?\d*)\s*%',
        r'운용보수\s*(?:\+[^)]+)?\s*연?\s*(\d+\.?\d*)\s*%',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return float(m.group(1))
    return None


def extract_risk_grade(text: str) -> Optional[int]:
    """위험등급 추출. 예: '위험등급 2등급', '투자위험 3등급'"""
    m = re.search(r'위험등급\s*:?\s*(\d)\s*등급', text)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d)\s*등급\s*\((?:높은|다소|보통|낮은)', text)
    if m:
        return int(m.group(1))
    return None


def extract_deposit_protection_amount(text: str) -> Optional[int]:
    """예금자보호 한도 금액 추출. 예: '5천만원', '5,000만원'"""
    m = re.search(r'(\d+)\s*천만\s*원', text)
    if m:
        return int(m.group(1)) * 10000000
    m = re.search(r'([\d,]+)\s*만\s*원', text)
    if m:
        val = int(m.group(1).replace(",", "")) * 10000
        if val >= 10000000:  # 1천만원 이상일 때만 보호 한도로 간주
            return val
    return None


def extract_prepayment_fee_rate(text: str) -> Optional[float]:
    """중도상환수수료율 추출. 예: '잔여원금의 1.2%', '중도상환수수료 1.5%'"""
    patterns = [
        r'잔여원금의\s*(\d+\.?\d*)\s*%',
        r'중도상환수수료\s*:?\s*(\d+\.?\d*)\s*%',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return float(m.group(1))
    return None


# ============================================================
# 비교 함수
# ============================================================

def _make_violation(vid: str, severity: str, field: str,
                    advertised, allowed, message: str, product_id: str) -> dict:
    return {
        "id": vid,
        "severity": severity,
        "field": field,
        "advertised_value": advertised,
        "allowed_value": allowed,
        "message": message,
        "product_id": product_id,
    }


def verify_deposit(extracted: dict, product: dict) -> list[dict]:
    violations = []
    pid = product["product_id"]

    # 금리 범위 확인
    if "rate_range" in extracted:
        lo, hi = extracted["rate_range"]
        if hi > product["max_rate"]:
            violations.append(_make_violation(
                "SPEC-DEP-001", "HIGH", "max_rate",
                f"{hi}%", f"최고 {product['max_rate']}%",
                f"광고 최고금리({hi}%)가 실제 상품 최고금리({product['max_rate']}%)를 초과합니다.",
                pid,
            ))
    elif "rates" in extracted:
        for r in extracted["rates"]:
            if r > product["max_rate"]:
                violations.append(_make_violation(
                    "SPEC-DEP-001", "HIGH", "rate",
                    f"{r}%", f"최고 {product['max_rate']}%",
                    f"광고 금리({r}%)가 실제 상품 최고금리({product['max_rate']}%)를 초과합니다.",
                    pid,
                ))

    # 예금자보호 한도 확인
    if "deposit_protection_amount" in extracted:
        adv_limit = extracted["deposit_protection_amount"]
        real_limit = product.get("deposit_protection_limit", 50000000)
        if adv_limit != real_limit:
            violations.append(_make_violation(
                "SPEC-DEP-002", "HIGH", "deposit_protection_limit",
                f"{adv_limit // 10000}만원",
                f"{real_limit // 10000}만원",
                f"예금자보호 한도 표시({adv_limit // 10000}만원)가 실제 한도({real_limit // 10000}만원)와 다릅니다.",
                pid,
            ))

    return violations


def verify_loan(extracted: dict, product: dict) -> list[dict]:
    violations = []
    pid = product["product_id"]

    # 금리 범위 확인
    if "rate_range" in extracted:
        lo, hi = extracted["rate_range"]
        if lo < product["min_rate"]:
            violations.append(_make_violation(
                "SPEC-LOAN-001", "HIGH", "min_rate",
                f"{lo}%", f"최저 {product['min_rate']}%",
                f"광고 최저금리({lo}%)가 실제 상품 최저금리({product['min_rate']}%)보다 낮습니다.",
                pid,
            ))
        if hi > product["max_rate"]:
            violations.append(_make_violation(
                "SPEC-LOAN-002", "HIGH", "max_rate",
                f"{hi}%", f"최고 {product['max_rate']}%",
                f"광고 최고금리({hi}%)가 실제 상품 최고금리({product['max_rate']}%)를 초과합니다.",
                pid,
            ))
    elif "rates" in extracted:
        for r in extracted["rates"]:
            if not (product["min_rate"] <= r <= product["max_rate"]):
                violations.append(_make_violation(
                    "SPEC-LOAN-001", "HIGH", "rate",
                    f"{r}%",
                    f"{product['min_rate']}%~{product['max_rate']}%",
                    f"광고 금리({r}%)가 실제 상품 금리 범위({product['min_rate']}%~{product['max_rate']}%)를 벗어납니다.",
                    pid,
                ))

    # 연체이자율 확인
    if "overdue_rate" in extracted:
        adv = extracted["overdue_rate"]
        real = product.get("overdue_rate", 0)
        if adv < real:
            violations.append(_make_violation(
                "SPEC-LOAN-003", "HIGH", "overdue_rate",
                f"{adv}%", f"최고 {real}%",
                f"광고 연체이자율({adv}%)이 실제 최고 연체이자율({real}%)보다 낮게 표시됩니다.",
                pid,
            ))

    # 중도상환수수료율 확인
    if "prepayment_fee_rate" in extracted:
        adv = extracted["prepayment_fee_rate"]
        real = product.get("prepayment_fee_rate", 0)
        if abs(adv - real) > 0.01:
            violations.append(_make_violation(
                "SPEC-LOAN-004", "MEDIUM", "prepayment_fee_rate",
                f"{adv}%", f"{real}%",
                f"광고 중도상환수수료율({adv}%)이 실제 수수료율({real}%)과 다릅니다.",
                pid,
            ))

    return violations


def verify_fund(extracted: dict, product: dict) -> list[dict]:
    violations = []
    pid = product["product_id"]

    # 총보수 확인
    if "total_fee" in extracted:
        adv = extracted["total_fee"]
        real = product.get("total_fee_rate", 0)
        if abs(adv - real) > 0.001:
            violations.append(_make_violation(
                "SPEC-FUND-001", "HIGH", "total_fee_rate",
                f"{adv}%", f"{real}%",
                f"광고 총보수({adv}%)가 실제 총보수({real}%)와 다릅니다.",
                pid,
            ))

    # 위험등급 확인
    if "risk_grade" in extracted:
        adv = extracted["risk_grade"]
        real = product.get("risk_grade", 0)
        if adv != real:
            violations.append(_make_violation(
                "SPEC-FUND-002", "MEDIUM", "risk_grade",
                f"{adv}등급", f"{real}등급 ({product.get('risk_label', '')})",
                f"광고 위험등급({adv}등급)이 실제 위험등급({real}등급)과 다릅니다.",
                pid,
            ))

    # 원금보장 표현 확인 (펀드는 원금보장 불가)
    if "principal_guarantee_claimed" in extracted and extracted["principal_guarantee_claimed"]:
        violations.append(_make_violation(
            "SPEC-FUND-003", "HIGH", "principal_guarantee",
            "원금 보장 표현 사용", "원금 비보장 (투자성 상품)",
            "펀드·ETF 광고에서 원금 보장 표현은 사용할 수 없습니다. (자본시장법 제55조)",
            pid,
        ))

    return violations


def verify_card(extracted: dict, product: dict) -> list[dict]:
    violations = []
    pid = product["product_id"]

    # 연회비 확인
    if "annual_fee" in extracted:
        adv = extracted["annual_fee"]
        real_domestic = product.get("annual_fee_domestic", 0)
        if adv != real_domestic:
            violations.append(_make_violation(
                "SPEC-CARD-001", "HIGH", "annual_fee",
                f"{adv:,}원", f"{real_domestic:,}원",
                f"광고 연회비({adv:,}원)가 실제 연회비({real_domestic:,}원)와 다릅니다.",
                pid,
            ))

    # 연체이자율 확인
    if "overdue_rate" in extracted:
        adv = extracted["overdue_rate"]
        real = product.get("overdue_rate", 0)
        if adv < real:
            violations.append(_make_violation(
                "SPEC-CARD-002", "HIGH", "overdue_rate",
                f"{adv}%", f"최고 {real}%",
                f"광고 연체이자율({adv}%)이 실제 최고 연체이자율({real}%)보다 낮게 표시됩니다.",
                pid,
            ))

    return violations


# ============================================================
# 상품 타입별 추출 + 비교 디스패치
# ============================================================

VERIFY_MAP = {
    "예금": verify_deposit,
    "대출": verify_loan,
    "펀드": verify_fund,
    "카드": verify_card,
}


def extract_all(ad_copy: str, product_type: str) -> dict:
    """광고 카피에서 상품 타입에 맞는 스펙 값 일괄 추출"""
    extracted = {}

    rate_range = extract_rate_range(ad_copy)
    if rate_range:
        extracted["rate_range"] = rate_range
    else:
        rates = extract_rates(ad_copy)
        if rates:
            extracted["rates"] = rates

    overdue = extract_overdue_rate(ad_copy)
    if overdue is not None:
        extracted["overdue_rate"] = overdue

    if product_type == "예금":
        amt = extract_deposit_protection_amount(ad_copy)
        if amt is not None:
            extracted["deposit_protection_amount"] = amt

    if product_type == "대출":
        fee = extract_prepayment_fee_rate(ad_copy)
        if fee is not None:
            extracted["prepayment_fee_rate"] = fee

    if product_type == "펀드":
        total_fee = extract_total_fee(ad_copy)
        if total_fee is not None:
            extracted["total_fee"] = total_fee
        grade = extract_risk_grade(ad_copy)
        if grade is not None:
            extracted["risk_grade"] = grade
        # 원금보장 표현 감지
        if re.search(r'원금\s*보장|손실\s*없음|확정\s*수익', ad_copy):
            extracted["principal_guarantee_claimed"] = True

    if product_type == "카드":
        fee = extract_annual_fee(ad_copy)
        if fee is not None:
            extracted["annual_fee"] = fee

    return extracted


# ============================================================
# Agent 2 메인 함수
# ============================================================

def run_agent2(ad_copy: str, product_type: str, product_id: str) -> dict:
    """
    Agent 2: 스펙 교차 검증 실행
    - ad_copy: 심의 대상 광고 카피
    - product_type: 상품 유형 (예금, 대출, 펀드, 카드)
    - product_id: Mock DB 상품 ID
    """
    print(f"[Agent 2] 스펙 교차 검증 시작 — product_id={product_id}")

    db = _load_mock_db()
    product = db.get(product_id)

    if product is None:
        print(f"[Agent 2] 경고: product_id '{product_id}'를 Mock DB에서 찾을 수 없습니다.")
        return {
            "spec_violations": [],
            "extracted_specs": {},
            "product": None,
            "warning": f"product_id '{product_id}' not found in Mock DB",
        }

    # 스펙 추출
    extracted = extract_all(ad_copy, product_type)
    print(f"[Agent 2] 추출된 스펙: {extracted}")

    # 상품 타입별 비교
    verify_fn = VERIFY_MAP.get(product_type)
    violations = verify_fn(extracted, product) if verify_fn else []

    print(f"[Agent 2] 완료 — 위반 {len(violations)}건")
    return {
        "spec_violations": violations,
        "extracted_specs": extracted,
        "product": {
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "product_type": product["product_type"],
        },
    }


# ============================================================
# 동작 테스트
# ============================================================

if __name__ == "__main__":
    tests = [
        {
            "label": "예금 - 금리 초과",
            "ad_copy": "JB 주거래 우대 정기예금 연 6.0% 확정금리! 예금자보호 5천만원 적용.",
            "product_type": "예금",
            "product_id": "JB-DEP-001",
        },
        {
            "label": "대출 - 금리 범위 정상",
            "ad_copy": "JB 직장인 신용대출 연 4.5%~7.5% (연체이자율 최고 연 15%). 중도상환수수료: 잔여원금의 1.2% (3년 이내).",
            "product_type": "대출",
            "product_id": "JB-LOAN-001",
        },
        {
            "label": "펀드 - 원금보장 표현",
            "ad_copy": "JB KOSPI 200 ETF 총보수 연 0.05%. 위험등급 3등급. 원금 보장 상품입니다.",
            "product_type": "펀드",
            "product_id": "JB-FUND-002",
        },
        {
            "label": "카드 - 연회비 불일치",
            "ad_copy": "JB 클래식 신용카드 연회비: 없음. 편의점 5% 할인.",
            "product_type": "카드",
            "product_id": "JB-CARD-001",
        },
    ]

    for t in tests:
        print(f"\n{'='*50}")
        print(f"[테스트] {t['label']}")
        result = run_agent2(t["ad_copy"], t["product_type"], t["product_id"])
        if result["spec_violations"]:
            for v in result["spec_violations"]:
                print(f"  [{v['severity']}] {v['message']}")
        else:
            print("  위반 없음")
