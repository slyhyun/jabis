# JABIS

**JB AI Banking Intelligence System**
*금융 광고 카피 심의 멀티 Agent 시스템*

JB금융그룹 Fin:AI Challenge 2026 출품작 (지정주제 2 — 준법자문가 AI Agent)

---

## 프로젝트 개요

준법감시인이 마케팅팀에서 제출받은 광고 카피를 업로드하면, 7개의 AI Agent가 협업하여 규제 위반 항목·근거 조항·수정안·다국어 버전을 산출하고, 승인 후 공식 심의 결과서 PDF를 자동 생성합니다.

핵심 차별점:
- **RAG + MCP 하이브리드** — 안정적 법령은 사전 인덱싱, 실시간 변경은 국가법령정보센터 OpenAPI로 조회
- **상품 DB 교차 검증** — 광고 속 숫자(금리, 한도)와 실제 상품 스펙 자동 대조
- **자기 검증 루프** — 수정안을 다시 심의에 투입하여 품질 보증

---

## 아키텍처

```
Layer 1: Streamlit (Presentation)
Layer 2: FastAPI + LangGraph + PostgreSQL
Layer 3: Multi-Agent (7개)
Layer 4: Chroma RAG + MCP #1, #2 + Rule Engine + LLM API
```

자세한 설계는 `docs/` 폴더 참조.

---

## 폴더 구조

```
jabis/
├── backend/          FastAPI, Agent 7개, LangGraph
├── frontend/         Streamlit UI
├── mcp_servers/      MCP #1 (법령), MCP #2 (상품 DB)
├── data/             RAG 데이터, Rule Engine
├── docs/             제안서, 명세서
├── demo/             시연 데모 데이터
└── tests/            통합 테스트
```

---

## 실행 방법 (개발 진행 후 업데이트 예정)

```bash
# 1. 가상환경
python -m venv venv
source venv/bin/activate

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경변수 설정
cp .env.example .env
# .env 파일에 API 키 입력

# 4. 백엔드 실행
uvicorn backend.app.main:app --reload --port 8000

# 5. 프론트엔드 실행 (새 터미널)
streamlit run frontend/app.py
```

---

## 팀

| 영역 | 담당 |
|------|------|
| 백엔드 (FastAPI, Agent 1/4/5/6/7, MCP, Streamlit UI) | TBD |
| 데이터 분석 (Chroma RAG, Rule Engine, Agent 2/3, PDF) | TBD |

---

## 일정

| 기간 | 마일스톤 |
|------|---------|
| 5/27 ~ 5/30 | 설계, 환경 셋업 |
| 5/31 ~ 6/4 | Agent 1~3, MCP, RAG 구현 |
| 6/5 ~ 6/9 | Agent 4~7, UI, PDF, 통합 |
| 6/10 ~ 6/12 | 영상, 문서, 제출 |

---

## 라이선스

본 프로젝트는 JB금융그룹 Fin:AI Challenge 2026 제출용으로, 대회 종료까지 비공개입니다.
