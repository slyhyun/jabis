"""
Mock JB 상품 데이터 삽입 스크립트
실행: python data/scripts/seed_products.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.db.session import SessionLocal
from backend.app.db.models import Product

MOCK_PRODUCTS = [
    # ==================== 예금 상품 ====================
    {
        "product_id": "JB-DEP-001",
        "product_name": "JB 정기예금",
        "product_type": "예금",
        "spec": {
            "interest_rate": 3.5,
            "period": "12개월",
            "min_amount": 100000,
            "max_amount": 100000000,
        },
        "description": "안정적인 확정금리를 제공하는 JB 대표 정기예금 상품",
    },
    {
        "product_id": "JB-DEP-002",
        "product_name": "JB 자유적금",
        "product_type": "예금",
        "spec": {
            "interest_rate": 4.0,
            "period": "24개월",
            "min_amount": 10000,
            "max_amount": 3000000,
        },
        "description": "매월 자유롭게 납입 가능한 적금 상품",
    },
    {
        "product_id": "JB-DEP-003",
        "product_name": "JB 주거래 우대예금",
        "product_type": "예금",
        "spec": {
            "interest_rate": 3.0,
            "period": "6개월",
            "min_amount": 100000,
            "max_amount": 50000000,
            "condition": "JB 주거래 고객 우대금리 제공",
        },
        "description": "주거래 고객에게 우대금리를 제공하는 단기 예금 상품",
    },
    {
        "product_id": "JB-DEP-004",
        "product_name": "JB 비대면 정기예금",
        "product_type": "예금",
        "spec": {
            "interest_rate": 3.8,
            "period": "12개월",
            "min_amount": 100000,
            "max_amount": 100000000,
            "channel": "비대면 전용",
        },
        "description": "앱/인터넷뱅킹 전용 우대금리 정기예금",
    },
    {
        "product_id": "JB-DEP-005",
        "product_name": "JB 청년 희망적금",
        "product_type": "예금",
        "spec": {
            "interest_rate": 5.0,
            "period": "24개월",
            "min_amount": 10000,
            "max_amount": 500000,
            "condition": "만 19~34세 가입 가능",
        },
        "description": "청년층을 위한 고금리 우대 적금 상품",
    },

    # ==================== 대출 상품 ====================
    {
        "product_id": "JB-LOAN-001",
        "product_name": "JB 주택담보대출",
        "product_type": "대출",
        "spec": {
            "interest_rate_min": 4.5,
            "interest_rate_max": 7.5,
            "max_limit": 500000000,
            "period": "최대 30년",
            "ltv": "최대 70%",
        },
        "description": "주택 구입 및 생활 안정 자금을 위한 담보대출",
    },
    {
        "product_id": "JB-LOAN-002",
        "product_name": "JB 신용대출",
        "product_type": "대출",
        "spec": {
            "interest_rate_min": 6.0,
            "interest_rate_max": 15.0,
            "max_limit": 100000000,
            "period": "최대 5년",
            "condition": "신용등급 1~6등급",
        },
        "description": "담보 없이 신용으로 이용 가능한 개인 신용대출",
    },
    {
        "product_id": "JB-LOAN-003",
        "product_name": "JB 전세자금대출",
        "product_type": "대출",
        "spec": {
            "interest_rate_min": 3.8,
            "interest_rate_max": 6.5,
            "max_limit": 300000000,
            "period": "최대 2년 (갱신 가능)",
            "ltv": "전세금의 최대 80%",
        },
        "description": "전세 보증금 마련을 위한 전용 대출 상품",
    },
    {
        "product_id": "JB-LOAN-004",
        "product_name": "JB 사업자대출",
        "product_type": "대출",
        "spec": {
            "interest_rate_min": 5.5,
            "interest_rate_max": 12.0,
            "max_limit": 500000000,
            "period": "최대 5년",
            "condition": "사업자등록 1년 이상",
        },
        "description": "중소기업 및 소상공인을 위한 운전자금 대출",
    },
    {
        "product_id": "JB-LOAN-005",
        "product_name": "JB 직장인 마이너스통장",
        "product_type": "대출",
        "spec": {
            "interest_rate_min": 7.0,
            "interest_rate_max": 12.0,
            "max_limit": 50000000,
            "period": "1년 (매년 갱신)",
            "condition": "재직 기간 6개월 이상 직장인",
        },
        "description": "필요할 때 자유롭게 사용하는 직장인 전용 한도대출",
    },

    # ==================== 펀드 상품 ====================
    {
        "product_id": "JB-FUND-001",
        "product_name": "JB 국내주식형펀드",
        "product_type": "펀드",
        "spec": {
            "risk_level": "높음",
            "fee": 1.5,
            "min_amount": 100000,
            "benchmark": "KOSPI200",
        },
        "description": "국내 우량 주식에 투자하는 성장형 펀드 (원금 비보장)",
    },
    {
        "product_id": "JB-FUND-002",
        "product_name": "JB 채권형펀드",
        "product_type": "펀드",
        "spec": {
            "risk_level": "낮음",
            "fee": 0.8,
            "min_amount": 100000,
            "benchmark": "KTB 3년",
        },
        "description": "국공채 중심의 안정적인 채권형 펀드 (원금 비보장)",
    },
    {
        "product_id": "JB-FUND-003",
        "product_name": "JB 혼합형펀드",
        "product_type": "펀드",
        "spec": {
            "risk_level": "중간",
            "fee": 1.2,
            "min_amount": 100000,
            "stock_ratio": "50%",
            "bond_ratio": "50%",
        },
        "description": "주식과 채권을 균형 있게 투자하는 혼합형 펀드 (원금 비보장)",
    },

    # ==================== 카드 상품 ====================
    {
        "product_id": "JB-CARD-001",
        "product_name": "JB 주거래 체크카드",
        "product_type": "카드",
        "spec": {
            "annual_fee": 0,
            "cashback_rate": 0.2,
            "benefits": ["편의점 5% 할인", "대중교통 10% 할인"],
        },
        "description": "연회비 없는 JB 주거래 체크카드",
    },
    {
        "product_id": "JB-CARD-002",
        "product_name": "JB 프리미엄 신용카드",
        "product_type": "카드",
        "spec": {
            "annual_fee": 150000,
            "cashback_rate": 1.0,
            "benefits": ["해외 결제 1.5% 적립", "공항 라운지 무료", "주유 리터당 100원 할인"],
            "condition": "전월 실적 50만원 이상",
        },
        "description": "다양한 프리미엄 혜택을 제공하는 JB 신용카드",
    },
]


def seed():
    db = SessionLocal()
    try:
        existing = db.query(Product).count()
        if existing > 0:
            print(f"이미 {existing}개의 상품이 존재합니다. 스킵합니다.")
            return

        for data in MOCK_PRODUCTS:
            product = Product(**data)
            db.add(product)

        db.commit()
        print(f"Mock 상품 {len(MOCK_PRODUCTS)}개 삽입 완료")

    except Exception as e:
        db.rollback()
        print(f"에러 발생: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
