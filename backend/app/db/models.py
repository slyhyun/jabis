from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Enum
from sqlalchemy.sql import func
from .session import Base
import enum


# ============================================================
# Enum 정의
# ============================================================

class RiskLevel(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ReviewStatus(str, enum.Enum):
    APPROVED = "APPROVED"      # 승인
    REJECTED = "REJECTED"      # 반려
    PENDING = "PENDING"        # 보류


class ProductType(str, enum.Enum):
    DEPOSIT = "예금"
    LOAN = "대출"
    FUND = "펀드"
    CARD = "카드"
    ETC = "기타"


# ============================================================
# 사용자 테이블
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)       # 로그인 ID
    name = Column(String(50), nullable=False)                        # 이름
    department = Column(String(100))                                 # 부서
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ============================================================
# 심의 이력 테이블
# ============================================================

class ReviewHistory(Base):
    __tablename__ = "review_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 입력 정보
    ad_copy = Column(Text, nullable=False)                           # 원본 광고 카피
    product_type = Column(String(20))                                # 상품 유형
    product_id = Column(String(50))                                  # 상품 ID

    # 심의 결과
    risk_level = Column(String(10))                                  # 위험도 (HIGH/MEDIUM/LOW)
    risk_summary = Column(Text)                                      # 위험도 요약
    revised_copy = Column(Text)                                      # 수정된 광고 카피
    review_status = Column(String(20), default=ReviewStatus.PENDING) # 심의 상태

    # 위반 항목 (JSON)
    violations = Column(JSON, default=list)
    # 예시:
    # [
    #   {"agent": "agent1", "type": "법령위반", "description": "...", "law": "금융소비자보호법 제00조"},
    #   {"agent": "agent2", "type": "스펙불일치", "description": "..."},
    #   {"agent": "agent3", "type": "의무표시누락", "description": "..."}
    # ]

    # 다국어 번역 (JSON)
    multilingual = Column(JSON, default=dict)
    # 예시: {"en": "...", "zh": "..."}

    # 메타
    verification_count = Column(Integer, default=0)                  # 자기 검증 횟수
    created_by = Column(String(50))                                  # 요청자 username
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ============================================================
# Mock 상품 테이블
# ============================================================

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), unique=True, nullable=False)     # 상품 코드 (예: JB-DEP-001)
    product_name = Column(String(100), nullable=False)               # 상품명
    product_type = Column(String(20), nullable=False)                # 상품 유형

    # 상품 스펙 (JSON)
    spec = Column(JSON, default=dict)
    # 예시 (예금):
    # {"interest_rate": 3.5, "period": "12개월", "min_amount": 100000, "max_amount": 100000000}
    # 예시 (대출):
    # {"interest_rate_min": 4.5, "interest_rate_max": 7.5, "limit": 300000000, "period": "최대 30년"}

    description = Column(Text)                                       # 상품 설명
    is_active = Column(Integer, default=1)                           # 판매 여부 (1: 판매중, 0: 판매종료)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
