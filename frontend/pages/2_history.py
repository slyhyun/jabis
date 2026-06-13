import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

st.set_page_config(page_title="JABIS - 심의 이력", page_icon="⚖️", layout="wide")

from components.sidebar import render_sidebar
from utils.session import init_session
from utils.api_client import get_history

init_session()
render_sidebar()

st.markdown("## 📚 심의 이력")

# ============================================================
# 필터
# ============================================================
with st.expander("🔍 검색 / 필터", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        risk_filter = st.multiselect("위험도", ["HIGH", "MEDIUM", "LOW"],
                                     default=["HIGH", "MEDIUM", "LOW"])
    with col2:
        status_filter = st.multiselect("결정 상태", ["APPROVED", "REJECTED", "PENDING"],
                                       default=["APPROVED", "REJECTED", "PENDING"])
    with col3:
        search_text = st.text_input("카피 내용 검색", placeholder="검색어 입력...")

# ============================================================
# 이력 목록
# ============================================================
resp = get_history(limit=50)
if not resp["ok"]:
    st.error(f"이력 조회 실패: {resp['error']}")
    st.stop()

records = resp["data"]

# 필터 적용
if risk_filter:
    records = [r for r in records if r.get("risk_level") in risk_filter]
if status_filter:
    records = [r for r in records if r.get("review_status") in status_filter]
if search_text:
    records = [r for r in records if search_text.lower() in r.get("ad_copy_preview", "").lower()]

st.markdown(f"**총 {len(records)}건**")
st.divider()

if not records:
    st.info("조건에 맞는 심의 이력이 없습니다.")
else:
    RISK_COLOR = {
        "HIGH":   ("#DC2626", "#FEE2E2", "높음"),
        "MEDIUM": ("#F59E0B", "#FEF3C7", "중간"),
        "LOW":    ("#10B981", "#D1FAE5", "낮음"),
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
        preview = r.get("ad_copy_preview", "")
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
                f'<div style="font-size:14px; font-weight:600;">{preview}</div>'
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
            if st.button("보기", key=f"view_{rid}"):
                st.session_state.view_review_id = rid
                st.session_state.review_result = None
                st.session_state.review_step = "result"
                st.switch_page("pages/3_result.py")
