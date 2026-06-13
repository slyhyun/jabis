import streamlit as st


def render_sidebar():
    st.markdown("""
    <style>
    [data-testid="stSidebarNavItems"],
    [data-testid="stSidebarNavSeparator"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 16px 0 8px 0;">
            <div style="font-size:56px;">👨‍💼</div>
            <div style="font-weight:700; font-size:18px; color:#1E3A8A;">박상준 팀장</div>
            <div style="font-size:13px; color:#6B7280;">전북은행 준법감시부</div>
        </div>
        <hr style="margin:8px 0 16px 0;">
        """, unsafe_allow_html=True)

        st.page_link("app.py", label="🏠  메인 대시보드")
        st.page_link("pages/1_new_review.py", label="📝  신규 심의")
        st.page_link("pages/2_history.py", label="📚  심의 이력")

        st.divider()

        st.markdown("""
        <div style="font-size:12px; color:#9CA3AF; text-align:center; padding:8px 0;">
            ⚙️ 설정 (준비 중)
        </div>
        """, unsafe_allow_html=True)

        st.button("🔓 로그아웃", use_container_width=True, disabled=True,
                  help="시연용 — 실제 로그아웃 기능 없음")

        st.markdown("""
        <div style="position:fixed; bottom:16px; left:0; width:100%;
                    text-align:center; font-size:11px; color:#9CA3AF;">
            JABIS v0.1 | JB금융그룹 Fin:AI Challenge 2026
        </div>
        """, unsafe_allow_html=True)
