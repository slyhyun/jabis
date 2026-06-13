import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import time

st.set_page_config(page_title="JABIS - 결과 검토", page_icon="⚖️", layout="wide")

from components.sidebar import render_sidebar
from components.breadcrumb import render_breadcrumb
from components.review_card import render_violation_card, render_risk_banner
from utils.session import init_session, clear_session
from utils.api_client import set_decision, translate_review, get_review, get_pdf_url

init_session()
render_sidebar()

# 이력에서 직접 들어온 경우
view_id = st.session_state.get("view_review_id")
if view_id and not st.session_state.get("review_result"):
    resp = get_review(view_id)
    if resp["ok"]:
        st.session_state.review_result = resp["data"]
        st.session_state.review_id = view_id
        st.session_state.review_step = "result"

result = st.session_state.get("review_result")
step = st.session_state.get("review_step", "result")

if not result:
    st.warning("심의 결과가 없습니다.")
    if st.button("신규 심의 시작"):
        st.switch_page("pages/1_new_review.py")
    st.stop()

review_id = st.session_state.get("review_id") or result.get("review_id")
violations = result.get("violations", [])
risk_level = result.get("risk_level", "LOW")
risk_summary = result.get("risk_summary", "")
ad_copy = result.get("ad_copy", "")
revised_copy = result.get("revised_copy", "")
verification_count = result.get("verification_count", 0)
multilingual = result.get("multilingual", {}) or st.session_state.get("translations", {})

# ============================================================
# P7: 결과 검토
# ============================================================
if step in ("result", "reviewing"):
    render_breadcrumb(4)
    st.markdown("## 📊 심의 결과 검토")

    render_risk_banner(risk_level, len(violations), risk_summary)

    col_orig, col_rev = st.columns(2, gap="large")
    with col_orig:
        st.markdown("#### 🔴 원본 카피")
        st.markdown(
            f'<div style="background:#FFF7F7; border:1.5px solid #FCA5A5; border-radius:8px;'
            f'padding:16px; font-size:14px; line-height:1.8; min-height:120px; color:#111827;">{ad_copy}</div>',
            unsafe_allow_html=True,
        )
    with col_rev:
        st.markdown("#### 🟢 AI 수정안")
        st.markdown(
            f'<div style="background:#F0FDF4; border:1.5px solid #6EE7B7; border-radius:8px;'
            f'padding:16px; font-size:14px; line-height:1.8; min-height:120px; color:#111827;">'
            f'{revised_copy.replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<div style='font-size:12px; color:#9CA3AF; margin-top:4px;'>"
        f"🔄 Agent 6 자기검증 {verification_count}회 완료</div>",
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown(f"#### ⚠️ 위반 항목 ({len(violations)}건)")
    if violations:
        for i, v in enumerate(violations):
            render_violation_card(v, expanded=(i == 0))
    else:
        st.success("위반 항목이 발견되지 않았습니다.")

    st.divider()
    st.markdown("#### 📋 박팀장 의사결정")

    review_status = result.get("review_status", "PENDING")
    already_decided = review_status in ("APPROVED", "REJECTED")

    if already_decided:
        STATUS_DISPLAY = {
            "APPROVED": ("✅ 승인 완료", "#065F46", "#D1FAE5"),
            "REJECTED": ("❌ 반려 처리", "#991B1B", "#FEE2E2"),
        }
        label, color, bg = STATUS_DISPLAY[review_status]
        st.markdown(
            f'<div style="background:{bg}; color:{color}; border-radius:8px; padding:16px 20px;'
            f'font-size:16px; font-weight:700;">{label}</div>',
            unsafe_allow_html=True,
        )
        reviewer_memo = result.get("reviewer_memo") or result.get("memo")
        if reviewer_memo:
            st.caption(f"메모: {reviewer_memo}")
        if review_status == "APPROVED":
            st.markdown("")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🌐 다국어 변환 보기", use_container_width=True):
                    st.session_state.review_step = "multilingual"
                    st.rerun()
            with c2:
                if st.button("📄 PDF 결과서", use_container_width=True):
                    st.session_state.decision = "APPROVED"
                    st.session_state.review_step = "pdf"
                    st.rerun()
    else:
        memo = st.text_area(
            "메모 (반려 시 필수)",
            value=st.session_state.get("decision_memo", ""),
            placeholder="심의 의견을 입력하세요...",
            height=100,
        )
        st.session_state.decision_memo = memo

        col_a, col_r, col_p = st.columns(3)

        with col_a:
            approve_btn = st.button("✅ 승인", type="primary", use_container_width=True)
            if approve_btn:
                if risk_level == "HIGH":
                    st.warning("⚠️ 위험도가 높은 광고입니다. 메모를 입력 후 다시 눌러주세요.")
                    st.session_state._approve_confirm = True
                else:
                    resp = set_decision(review_id, "APPROVED", memo or None)
                    if resp["ok"]:
                        st.session_state.decision = "APPROVED"
                        st.session_state.review_step = "multilingual"
                        st.rerun()
                    else:
                        st.error(f"처리 실패: {resp['error']}")

            if st.session_state.get("_approve_confirm") and risk_level == "HIGH":
                if st.button("그래도 승인", key="force_approve"):
                    resp = set_decision(review_id, "APPROVED", memo or None)
                    if resp["ok"]:
                        st.session_state.decision = "APPROVED"
                        st.session_state._approve_confirm = False
                        st.session_state.review_step = "multilingual"
                        st.rerun()

        with col_r:
            if st.button("❌ 반려", use_container_width=True):
                if not memo.strip():
                    st.error("반려 사유를 입력해주세요.")
                else:
                    resp = set_decision(review_id, "REJECTED", memo)
                    if resp["ok"]:
                        st.session_state.decision = "REJECTED"
                        st.session_state.review_step = "rejected"
                        st.rerun()
                    else:
                        st.error(f"처리 실패: {resp['error']}")

        with col_p:
            if st.button("⏸️ 보류", use_container_width=True):
                resp = set_decision(review_id, "PENDING", memo or None)
                if resp["ok"]:
                    st.session_state.decision = "PENDING"
                    st.session_state.review_step = "pending"
                    st.rerun()
                else:
                    st.error(f"처리 실패: {resp['error']}")


# ============================================================
# 반려
# ============================================================
elif step == "rejected":
    render_breadcrumb(4)
    st.markdown("## ❌ 반려 처리 완료")
    st.error(
        f"심의 #{review_id}이 반려 처리되었습니다.\n\n"
        f"**반려 사유:** {st.session_state.get('decision_memo', '')}"
    )
    st.info("✉️ 마케팅팀 김대리에게 반려 사유와 함께 회신되었습니다.")
    if st.button("🏠 메인으로", type="primary"):
        clear_session()
        st.switch_page("app.py")


# ============================================================
# 보류
# ============================================================
elif step == "pending":
    render_breadcrumb(4)
    st.markdown("## ⏸️ 보류 처리 완료")
    st.warning("보류 상태로 저장되었습니다. 24시간 후 재검토 대기열에 표시됩니다.")
    if st.button("🏠 메인으로", type="primary"):
        clear_session()
        st.switch_page("app.py")


# ============================================================
# P9: 다국어 변환
# ============================================================
elif step == "multilingual":
    render_breadcrumb(5)
    st.markdown("## 🌐 다국어 변환")

    meta = st.session_state.get("meta_info", {})
    langs = meta.get("languages", ["한국어"])
    need_translation = "영어" in langs or "중국어" in langs

    st.markdown("#### 한국어 최종안")
    st.markdown(
        f'<div style="background:#F0FDF4; border:1.5px solid #6EE7B7; border-radius:8px;'
        f'padding:16px; font-size:14px; line-height:1.8; color:#111827;">'
        f'{revised_copy.replace(chr(10), "<br>")}</div>',
        unsafe_allow_html=True,
    )

    if not need_translation:
        st.info("영어/중국어가 선택되지 않았습니다.")
        if st.button("📄 PDF 생성", type="primary"):
            st.session_state.review_step = "pdf"
            st.rerun()
    else:
        translations = st.session_state.get("translations") or multilingual

        if not translations:
            st.markdown("---")
            if st.button("🌐 다국어 변환 시작", type="primary", use_container_width=True):
                with st.spinner("번역 중... (영어/중국어)"):
                    resp = translate_review(review_id)
                if resp["ok"]:
                    st.session_state.translations = resp["data"].get("multilingual", {})
                    st.rerun()
                else:
                    st.error(f"번역 실패: {resp['error']}")
        else:
            LANG_CONFIG = {
                "en": {"flag": "🇬🇧", "label": "영어"},
                "zh": {"flag": "🇨🇳", "label": "중국어"},
            }
            for code, data in translations.items():
                cfg = LANG_CONFIG.get(code, {"flag": "🌐", "label": code})
                show = ("영어" in langs and code == "en") or ("중국어" in langs and code == "zh")
                if not show:
                    continue
                st.markdown(f"#### {cfg['flag']} {cfg['label']} 버전")
                st.markdown(
                    f'<div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:8px;'
                    f'padding:16px; font-size:14px; line-height:1.8; color:#111827;">{data.get("text", "")}</div>',
                    unsafe_allow_html=True,
                )
                c1, c2 = st.columns(2)
                c1.markdown(f'{"✅" if data.get("disclosure_preserved") else "⚠️"} 의무표시 보존')
                c2.markdown(f'{"✅ 문화권 적합" if not data.get("has_issues") else "⚠️ 이슈 있음"}')
                st.markdown("")

            if st.button("📄 PDF 생성", type="primary", use_container_width=True):
                st.session_state.review_step = "pdf"
                st.rerun()


# ============================================================
# P10: PDF 심의서
# ============================================================
elif step == "pdf":
    render_breadcrumb(6)
    st.markdown("## 📄 심의 결과서")
    st.success("✅ 심의 결과서가 생성되었습니다.")

    RISK_LABEL = {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}
    STATUS_LABEL = {"APPROVED": "승인", "REJECTED": "반려", "PENDING": "보류"}

    st.markdown(
        f"""
        <div style="background:white; color:#111827; border:1px solid #E5E7EB; border-radius:12px; padding:28px 32px;">
        <h3 style="color:#1E3A8A; margin-top:0;">⚖️ JABIS 광고 심의 결과서</h3>
        <hr>
        <table style="width:100%; font-size:14px; border-collapse:collapse;">
        <tr><td style="color:#6B7280; width:140px; padding:6px 0;">심의 번호</td>
            <td><strong>#{review_id}</strong></td></tr>
        <tr><td style="color:#6B7280; padding:6px 0;">담당자</td>
            <td>박상준 팀장 / 전북은행 준법감시부</td></tr>
        <tr><td style="color:#6B7280; padding:6px 0;">상품 유형</td>
            <td>{result.get('product_type', '')}</td></tr>
        <tr><td style="color:#6B7280; padding:6px 0;">종합 위험도</td>
            <td><strong>{RISK_LABEL.get(risk_level, risk_level)}</strong></td></tr>
        <tr><td style="color:#6B7280; padding:6px 0;">심의 결정</td>
            <td><strong>{STATUS_LABEL.get(st.session_state.get('decision', 'PENDING'), '보류')}</strong></td></tr>
        <tr><td style="color:#6B7280; padding:6px 0;">위반 항목</td>
            <td>{len(violations)}건</td></tr>
        </table>
        <hr>
        <p style="color:#6B7280; font-size:13px; margin-bottom:4px;">원본 카피</p>
        <p style="font-size:14px; background:#FFF7F7; color:#111827; padding:12px; border-radius:6px;">{ad_copy}</p>
        <p style="color:#6B7280; font-size:13px; margin-bottom:4px;">AI 수정안</p>
        <p style="font-size:14px; background:#F0FDF4; color:#111827; padding:12px; border-radius:6px;">
        {revised_copy.replace(chr(10), "<br>")}</p>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.get("decision_memo"):
        st.markdown(
            f'<p style="color:#6B7280; font-size:13px; margin-bottom:4px;">박팀장 메모</p>'
            f'<p style="font-size:14px;">{st.session_state.decision_memo}</p>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        pdf_url = get_pdf_url(review_id)
        st.link_button("📥 PDF 다운로드", url=pdf_url, use_container_width=True)
    with col2:
        if st.button("✉️ 마케팅팀에 회신", use_container_width=True):
            st.toast("✉️ 마케팅팀 김대리에게 회신되었습니다!", icon="✅")
    with col3:
        if st.button("🔗 링크 복사", use_container_width=True):
            st.toast("링크가 복사되었습니다!", icon="🔗")
    with col4:
        if st.button("✅ 새 심의 시작", type="primary", use_container_width=True):
            clear_session()
            st.switch_page("app.py")
