import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import time

st.set_page_config(page_title="JABIS - 신규 심의", page_icon="⚖️", layout="wide")

from components.sidebar import render_sidebar
from components.breadcrumb import render_breadcrumb
from components.progress_bar import AGENT_STEPS, render_agent_card
from utils.session import init_session, save_review_data, PRODUCT_MAP, SAMPLE_COPIES, product_id_from_label
from utils.api_client import create_review

init_session()
render_sidebar()

step = st.session_state.get("review_step", "input")
if step not in ("input", "reviewing"):
    st.session_state.review_step = "input"
    step = "input"

# ============================================================
# P4 + P5: 입력 화면
# ============================================================
if step == "input":
    render_breadcrumb(1)
    st.markdown("## 📝 신규 심의")

    tab1, tab2 = st.tabs(["📄 광고 카피 입력", "⚙️ 메타정보 설정"])

    with tab1:
        st.markdown("#### 시연용 샘플 카피")
        sample_cols = st.columns(2)
        for i, sample in enumerate(SAMPLE_COPIES):
            with sample_cols[i % 2]:
                if st.button(sample["label"], key=f"sample_{i}", use_container_width=True):
                    st.session_state.current_copy = sample["ad_copy"]
                    st.session_state.meta_info["product_type"] = sample["product_type"]
                    st.session_state.meta_info["product_id"] = sample["product_id"]
                    st.rerun()

        st.markdown("---")
        copy_input = st.text_area(
            "광고 카피를 입력하세요",
            value=st.session_state.get("current_copy", ""),
            height=180,
            max_chars=2000,
            placeholder="예: JB 주거래 우대 정기예금 연 6.0% 확정금리! 지금 바로 가입하세요.",
            key="copy_textarea",
        )
        st.session_state.current_copy = copy_input
        char_count = len(copy_input)
        st.caption(f"{char_count}/2000자")

    with tab2:
        if st.session_state.get("current_copy"):
            st.info(f"📄 입력 카피: {st.session_state.current_copy[:80]}{'...' if len(st.session_state.current_copy) > 80 else ''}")

        col1, col2 = st.columns(2)
        with col1:
            product_type = st.selectbox(
                "상품 종류",
                options=["예금", "대출", "펀드", "카드"],
                index=["예금", "대출", "펀드", "카드"].index(
                    st.session_state.meta_info.get("product_type", "예금")
                ),
            )
            st.session_state.meta_info["product_type"] = product_type

            product_options = PRODUCT_MAP.get(product_type, [])
            current_pid = st.session_state.meta_info.get("product_id", "")
            matched = next((p for p in product_options if p.startswith(current_pid)), product_options[0] if product_options else "")
            product_label = st.selectbox("상품 선택", options=product_options,
                                          index=product_options.index(matched) if matched in product_options else 0)
            st.session_state.meta_info["product_id"] = product_id_from_label(product_label)

        with col2:
            channel = st.selectbox(
                "광고 채널",
                options=["SNS", "지면", "배너", "기타"],
                index=["SNS", "지면", "배너", "기타"].index(
                    st.session_state.meta_info.get("channel", "SNS")
                ),
            )
            st.session_state.meta_info["channel"] = channel

            languages = st.multiselect(
                "대상 언어",
                options=["한국어", "영어", "중국어"],
                default=st.session_state.meta_info.get("languages", ["한국어"]),
            )
            if "한국어" not in languages:
                languages = ["한국어"] + languages
            st.session_state.meta_info["languages"] = languages

        memo = st.text_input(
            "추가 메모 (선택)",
            value=st.session_state.meta_info.get("memo", ""),
            placeholder="심의 관련 특이사항을 입력하세요",
        )
        st.session_state.meta_info["memo"] = memo

    st.divider()

    can_submit = bool(st.session_state.get("current_copy", "").strip())
    if not can_submit:
        st.warning("카피를 입력해주세요.")

    if st.button("🚀 심의 시작", type="primary", disabled=not can_submit, use_container_width=True):
        st.session_state.review_step = "reviewing"
        st.rerun()


# ============================================================
# P6: 심의 진행 화면
# ============================================================
elif step == "reviewing":
    render_breadcrumb(3)
    st.markdown("## ⚙️ AI 심의 진행 중")

    st.info(f"📄 심의 대상: **{st.session_state.current_copy[:80]}{'...' if len(st.session_state.current_copy) > 80 else ''}**")

    progress_bar = st.progress(0)
    status_text = st.empty()
    elapsed_text = st.empty()
    agent_area = st.empty()

    statuses = ["pending"] * len(AGENT_STEPS)

    # 각 Agent 카드 초기 렌더링
    def render_all(statuses, verify_count=0):
        with agent_area.container():
            for i, agent in enumerate(AGENT_STEPS):
                render_agent_card(agent, statuses[i], verify_count if agent["id"] == "agent6" else 0)

    render_all(statuses)

    # 백엔드 호출 (별도 스레드 불가 → 먼저 호출 후 시각화)
    start_time = time.time()

    # 실제 API 호출
    with st.spinner(""):
        result = create_review(
            ad_copy=st.session_state.current_copy,
            product_type=st.session_state.meta_info["product_type"],
            product_id=st.session_state.meta_info["product_id"],
        )

    elapsed = time.time() - start_time

    # 결과 나온 후 시각적 시뮬레이션 재생
    if result["ok"]:
        verify_count = result["data"].get("verification_count", 1)
        for i, agent in enumerate(AGENT_STEPS):
            statuses[i] = "running"
            render_all(statuses, verify_count)
            progress_bar.progress((i + 1) / len(AGENT_STEPS) * 0.9)
            status_text.markdown(f"**{agent['name']}** 처리 중...")
            elapsed_text.caption(f"심의 진행 중... {agent['duration']:.1f}초 경과")
            time.sleep(agent["duration"] * 0.4)

            statuses[i] = "done"
            render_all(statuses, verify_count)
            progress_bar.progress((i + 1) / len(AGENT_STEPS))

        progress_bar.progress(1.0)
        status_text.markdown("**✅ 심의 완료!**")
        elapsed_text.caption(f"총 소요 시간: {elapsed:.1f}초")

        save_review_data(result["data"])
        st.session_state.review_step = "result"
        time.sleep(0.8)
        st.balloons()
        st.switch_page("pages/3_result.py")
    else:
        for i in range(len(AGENT_STEPS)):
            statuses[i] = "error"
        render_all(statuses)
        st.error(f"❌ 심의 실패: {result['error']}")
        if st.button("다시 시도", type="primary"):
            st.session_state.review_step = "input"
            st.rerun()
