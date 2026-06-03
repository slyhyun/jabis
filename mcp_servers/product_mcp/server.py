"""
MCP #2 — Mock 상품 DB 조회 서버
FastAPI 엔드포인트로 상품 정보를 제공
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException
from backend.app.db.session import SessionLocal
from backend.app.db.models import Product

app = FastAPI(
    title="JABIS Product MCP",
    description="MCP #2 — JB 금융 Mock 상품 DB 조회 API",
    version="0.1.0",
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# 조회 API
# ============================================================

@app.get("/products")
def get_all_products(product_type: str = None):
    """전체 상품 목록 조회 (상품 유형 필터링 가능)"""
    db = SessionLocal()
    try:
        query = db.query(Product).filter(Product.is_active == 1)
        if product_type:
            query = query.filter(Product.product_type == product_type)
        products = query.all()
        return [
            {
                "product_id": p.product_id,
                "product_name": p.product_name,
                "product_type": p.product_type,
                "spec": p.spec,
                "description": p.description,
            }
            for p in products
        ]
    finally:
        db.close()


@app.get("/products/{product_id}")
def get_product(product_id: str):
    """상품 ID로 단건 조회"""
    db = SessionLocal()
    try:
        product = db.query(Product).filter(
            Product.product_id == product_id,
            Product.is_active == 1
        ).first()

        if not product:
            raise HTTPException(status_code=404, detail=f"상품을 찾을 수 없습니다: {product_id}")

        return {
            "product_id": product.product_id,
            "product_name": product.product_name,
            "product_type": product.product_type,
            "spec": product.spec,
            "description": product.description,
        }
    finally:
        db.close()


@app.get("/products/type/{product_type}")
def get_products_by_type(product_type: str):
    """상품 유형별 조회 (예금, 대출, 펀드, 카드)"""
    db = SessionLocal()
    try:
        products = db.query(Product).filter(
            Product.product_type == product_type,
            Product.is_active == 1
        ).all()

        if not products:
            raise HTTPException(status_code=404, detail=f"해당 유형의 상품이 없습니다: {product_type}")

        return [
            {
                "product_id": p.product_id,
                "product_name": p.product_name,
                "spec": p.spec,
                "description": p.description,
            }
            for p in products
        ]
    finally:
        db.close()


# ============================================================
# 동작 테스트
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
