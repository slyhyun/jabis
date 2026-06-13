import streamlit as st

STEPS = ["입력", "메타정보", "심의", "결과", "다국어", "PDF"]


def render_breadcrumb(current: int):
    """current: 1-indexed 현재 단계"""
    cols = st.columns(len(STEPS))
    for i, (col, label) in enumerate(zip(cols, STEPS), start=1):
        with col:
            if i == current:
                st.markdown(
                    f'<div style="background:#1E3A8A; color:white; border-radius:6px;'
                    f'text-align:center; padding:6px 4px; font-size:13px; font-weight:700;">'
                    f'{i}. {label}</div>',
                    unsafe_allow_html=True,
                )
            elif i < current:
                st.markdown(
                    f'<div style="background:#D1FAE5; color:#065F46; border-radius:6px;'
                    f'text-align:center; padding:6px 4px; font-size:13px;">✅ {label}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="background:#F3F4F6; color:#9CA3AF; border-radius:6px;'
                    f'text-align:center; padding:6px 4px; font-size:13px;">{i}. {label}</div>',
                    unsafe_allow_html=True,
                )
    st.markdown("<div style='margin-bottom:16px'></div>", unsafe_allow_html=True)
