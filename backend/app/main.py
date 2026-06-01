from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="JABIS API",
    description="JB AI Banking Intelligence System - 금융 광고 카피 자동 심의",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "JABIS API 서버가 정상 동작 중입니다."}


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "JABIS",
        "version": "0.1.0",
    }
