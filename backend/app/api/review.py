"""
FastAPI 심의 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from backend.app.db.session import get_db
from backend.app.db.models import ReviewHistory, ReviewStatus

router = APIRouter(prefix="/api/review", tags=["review"])


# ============================================================
# Pydantic 모델
# ============================================================

class ReviewRequest(BaseModel):
    ad_copy: str
    product_type: str       # 예금 / 대출 / 펀드 / 카드
    product_id: str         # JB-DEP-001 등


class ViolationItem(BaseModel):
    id: str
    severity: str           # HIGH / MEDIUM / LOW
    source: str             # spec / disclosure
    item: str
    message: str


class ReviewResponse(BaseModel):
    review_id: int
    ad_copy: str
    product_type: str
    product_id: str
    risk_level: str
    risk_summary: str
    revised_copy: str
    violations: list
    verification_count: int
    review_status: str
    created_at: datetime


class ReviewSummary(BaseModel):
    review_id: int
    product_type: str
    risk_level: str
    review_status: str
    created_at: datetime
    ad_copy_preview: str    # 광고 카피 앞 50자


class DecisionRequest(BaseModel):
    decision: str           # APPROVED / REJECTED / PENDING
    comment: Optional[str] = None


class DecisionResponse(BaseModel):
    review_id: int
    review_status: str
    message: str


# ============================================================
# DB 저장 헬퍼
# ============================================================

def _save_review(db: Session, request: ReviewRequest, result: dict) -> ReviewHistory:
    violations = (
        result.get("spec_violations", []) +
        result.get("disclosure_violations", [])
    )
    record = ReviewHistory(
        ad_copy=request.ad_copy,
        product_type=request.product_type,
        product_id=request.product_id,
        risk_level=result.get("risk_level", "LOW"),
        risk_summary=result.get("risk_summary", ""),
        revised_copy=result.get("revised_copy", request.ad_copy),
        review_status=ReviewStatus.PENDING,
        violations=violations,
        multilingual=result.get("multilingual", {}),
        verification_count=result.get("verification_count", 0),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _record_to_response(record: ReviewHistory) -> ReviewResponse:
    return ReviewResponse(
        review_id=record.id,
        ad_copy=record.ad_copy,
        product_type=record.product_type,
        product_id=record.product_id,
        risk_level=record.risk_level or "",
        risk_summary=record.risk_summary or "",
        revised_copy=record.revised_copy or "",
        violations=record.violations or [],
        verification_count=record.verification_count or 0,
        review_status=record.review_status or ReviewStatus.PENDING,
        created_at=record.created_at,
    )


# ============================================================
# 헬스 체크
# ============================================================

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "JABIS API"}


# ============================================================
# 심의 이력 조회
# ============================================================

@router.get("/history", response_model=list[ReviewSummary])
def get_history(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    records = (
        db.query(ReviewHistory)
        .order_by(ReviewHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        ReviewSummary(
            review_id=r.id,
            product_type=r.product_type or "",
            risk_level=r.risk_level or "",
            review_status=r.review_status or ReviewStatus.PENDING,
            created_at=r.created_at,
            ad_copy_preview=r.ad_copy[:50] if r.ad_copy else "",
        )
        for r in records
    ]


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int, db: Session = Depends(get_db)):
    record = db.query(ReviewHistory).filter(ReviewHistory.id == review_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"심의 이력 {review_id}를 찾을 수 없습니다.")
    return _record_to_response(record)
