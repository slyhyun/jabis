import streamlit as st
import httpx

st.set_page_config(
    page_title="JABIS",
    page_icon="⚖️",
    layout="wide",
)

st.title("⚖️ JABIS")
st.subheader("JB AI Banking Intelligence System")
st.markdown("금융 광고 카피 자동 심의 시스템입니다.")

st.success("Streamlit 서버가 정상 동작 중입니다.")

st.divider()

st.subheader("🔌 FastAPI 서버 연결 테스트")

if st.button("FastAPI 상태 확인"):
    try:
        response = httpx.get("http://localhost:8000/health")
        data = response.json()
        st.success(f"✅ 연결 성공! 응답: {data}")
    except Exception as e:
        st.error(f"❌ 연결 실패: {e}")
