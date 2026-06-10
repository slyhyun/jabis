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


# ============================================================
# 핵심 엔드포인트
# ============================================================

@router.post("", response_model=ReviewResponse)
def create_review(request: ReviewRequest, db: Session = Depends(get_db)):
    """광고 카피 심의 요청 — LangGraph 워크플로우 실행"""
    try:
        from backend.app.workflow.graph import jabis_graph
        result = jabis_graph.invoke({
            "ad_copy": request.ad_copy,
            "product_type": request.product_type,
            "product_id": request.product_id,
            "verification_count": 0,
            "is_verified": False,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"심의 워크플로우 오류: {str(e)}")

    try:
        record = _save_review(db, request, result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 저장 오류: {str(e)}")

    return _record_to_response(record)


@router.post("/{review_id}/decision", response_model=DecisionResponse)
def set_decision(review_id: int, body: DecisionRequest, db: Session = Depends(get_db)):
    """승인 / 반려 / 보류 결정"""
    valid = {s.value for s in ReviewStatus}
    if body.decision not in valid:
        raise HTTPException(status_code=400, detail=f"decision은 {valid} 중 하나여야 합니다.")

    record = db.query(ReviewHistory).filter(ReviewHistory.id == review_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"심의 이력 {review_id}를 찾을 수 없습니다.")

    record.review_status = body.decision
    db.commit()

    label = {"APPROVED": "승인", "REJECTED": "반려", "PENDING": "보류"}.get(body.decision, body.decision)
    return DecisionResponse(
        review_id=review_id,
        review_status=body.decision,
        message=f"심의 이력 {review_id}이 {label} 처리되었습니다.",
    )


@router.post("/{review_id}/translate", response_model=dict)
def translate_review(review_id: int, db: Session = Depends(get_db)):
    """다국어 변환 — 박팀장 선택 시 Agent 7 호출"""
    record = db.query(ReviewHistory).filter(ReviewHistory.id == review_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"심의 이력 {review_id}를 찾을 수 없습니다.")

    try:
        from backend.app.agents.agent7_multilingual import run_agent7
        result = run_agent7(
            revised_copy=record.revised_copy or record.ad_copy,
            product_type=record.product_type or "",
        )
        multilingual = result["multilingual"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다국어 변환 오류: {str(e)}")

    record.multilingual = multilingual
    db.commit()

    return {"review_id": review_id, "multilingual": multilingual}


@router.get("/{review_id}/pdf")
def download_pdf(review_id: int, db: Session = Depends(get_db)):
    """PDF 심의서 다운로드"""
    record = db.query(ReviewHistory).filter(ReviewHistory.id == review_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"심의 이력 {review_id}를 찾을 수 없습니다.")

    try:
        from backend.app.pdf.generator import generate_pdf
        from fastapi.responses import StreamingResponse
        import io
        pdf_bytes = generate_pdf(record)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=jabis_review_{review_id}.pdf"},
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="PDF 생성 모듈이 아직 준비되지 않았습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 생성 오류: {str(e)}")
