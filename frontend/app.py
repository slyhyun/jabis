import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="JABIS - 대시보드",
    page_icon="⚖️",
    layout="wide",
)

from components.sidebar import render_sidebar
from utils.api_client import health_check, get_history
from utils.session import init_session

init_session()
render_sidebar()

# ============================================================
# 헤더
# ============================================================
today = datetime.now().strftime("%Y년 %m월 %d일")
st.markdown(f"## 안녕하세요, 박팀장님 👋")
st.markdown(f"<span style='color:#6B7280; font-size:14px;'>{today}</span>", unsafe_allow_html=True)
st.divider()

# ============================================================
# 서버 상태 확인
# ============================================================
server_ok = health_check()
if not server_ok:
    st.error("⚠️ 백엔드 서버에 연결할 수 없습니다. `uvicorn backend.app.main:app --reload` 실행 여부를 확인해주세요.")

# ============================================================
# 2컬럼 레이아웃
# ============================================================
left, right = st.columns([2, 1], gap="large")

with right:
    # 신규 심의 버튼
    st.markdown("### 📝 신규 심의")
    if st.button("새 심의 시작하기", use_container_width=True, type="primary"):
        st.switch_page("pages/1_new_review.py")

    st.markdown("---")

    # 통계 카드
    st.markdown("### 📊 현황")
    history_resp = get_history(limit=100)
    if history_resp["ok"]:
        records = history_resp["data"]
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_reviews = [
            r for r in records
            if r.get("created_at", "").startswith(today_str)
        ]

        risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for r in records:
            lvl = r.get("risk_level", "LOW")
            if lvl in risk_counts:
                risk_counts[lvl] += 1

        dominant = max(risk_counts, key=lambda k: risk_counts[k]) if records else "—"
        dominant_label = {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}.get(dominant, "—")

        c1, c2 = st.columns(2)
        c1.metric("오늘 심의", f"{len(today_reviews)}건")
        c2.metric("전체 심의", f"{len(records)}건")
        st.metric("주요 위험도", dominant_label)
    else:
        st.info("통계를 불러올 수 없습니다.")

with left:
    st.markdown("### 📋 최근 심의 이력")

    history_resp = get_history(limit=5)
    if not history_resp["ok"]:
        st.warning(f"이력 조회 실패: {history_resp['error']}")
    else:
        records = history_resp["data"]
        if not records:
            st.markdown("""
            <div style='text-align:center; padding:60px 20px; background:#F9FAFB;
                        border-radius:12px; border:2px dashed #E5E7EB;'>
                <div style='font-size:48px;'>🎯</div>
                <div style='font-size:20px; font-weight:700; margin:12px 0 8px;'>
                    첫 심의를 시작해보세요!</div>
                <div style='color:#6B7280;'>아직 심의 이력이 없습니다.</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            if st.button("📝 첫 심의 시작하기", type="primary", use_container_width=True):
                st.switch_page("pages/1_new_review.py")
        else:
            RISK_COLOR = {
                "HIGH": ("#DC2626", "#FEE2E2", "높음"),
                "MEDIUM": ("#F59E0B", "#FEF3C7", "중간"),
                "LOW": ("#10B981", "#D1FAE5", "낮음"),
            }
            STATUS_LABEL = {
                "APPROVED": ("✅ 승인", "#065F46", "#D1FAE5"),
                "REJECTED": ("❌ 반려", "#991B1B", "#FEE2E2"),
                "PENDING":  ("⏸️ 보류", "#92400E", "#FEF3C7"),
            }

            for r in records:
                risk = r.get("risk_level", "LOW")
                rc, rbg, rlabel = RISK_COLOR.get(risk, ("#10B981", "#D1FAE5", "낮음"))
                status = r.get("review_status", "PENDING")
                slabel, sc, sbg = STATUS_LABEL.get(status, ("⏸️ 보류", "#92400E", "#FEF3C7"))
                preview = r.get("ad_copy_preview", "")[:30]
                rid = r.get("review_id")
                created = r.get("created_at", "")[:16].replace("T", " ")
                ptype = r.get("product_type", "")

                col_main, col_btn = st.columns([6, 1])
                with col_main:
                    st.markdown(
                        f'<div style="background:white; color:#111827; border:1px solid #E5E7EB; border-radius:10px;'
                        f'padding:14px 18px; display:flex; align-items:center; gap:12px;">'
                        f'<div style="min-width:48px; font-weight:700; color:#1E3A8A;">#{rid}</div>'
                        f'<div style="flex:1;">'
                        f'<div style="font-size:14px; font-weight:600;">{preview}...</div>'
                        f'<div style="font-size:12px; color:#9CA3AF;">{created} · {ptype}</div>'
                        f'</div>'
                        f'<span style="background:{rbg}; color:{rc}; border-radius:4px; padding:3px 10px;'
                        f'font-size:12px; font-weight:700; white-space:nowrap;">{rlabel}</span>'
                        f'<span style="background:{sbg}; color:{sc}; border-radius:4px; padding:3px 10px;'
                        f'font-size:12px; white-space:nowrap;">{slabel}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with col_btn:
                    if st.button("보기", key=f"detail_{rid}"):
                        st.session_state.view_review_id = rid
                        st.session_state.review_result = None
                        st.session_state.review_step = "result"
                        st.switch_page("pages/3_result.py")

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("📚 전체 이력 보기", use_container_width=True):
                st.switch_page("pages/2_history.py")
