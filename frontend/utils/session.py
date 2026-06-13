import streamlit as st

DEFAULTS = {
    "current_copy": "",
    "meta_info": {
        "product_type": "예금",
        "product_id": "JB-DEP-001",
        "channel": "SNS",
        "languages": ["한국어"],
        "memo": "",
    },
    "review_id": None,
    "review_result": None,
    "review_step": "input",   # input | reviewing | result | multilingual | pdf
    "decision": None,
    "decision_memo": "",
    "translations": None,
}

PRODUCT_MAP = {
    "예금": ["JB-DEP-001 (JB 주거래 우대 정기예금)", "JB-DEP-002 (JB 청년 자유적금)"],
    "대출": ["JB-LOAN-001 (JB 직장인 신용대출)", "JB-LOAN-002 (JB 주택담보대출)"],
    "펀드": [
        "JB-FUND-001 (JB 성장형 주식혼합펀드)",
        "JB-FUND-002 (JB KOSPI 200 ETF)",
        "JB-FUND-003 (JB 월분배 채권혼합 ETF)",
    ],
    "카드": ["JB-CARD-001 (JB 클래식 신용카드)", "JB-CARD-002 (JB 체크카드)"],
}

SAMPLE_COPIES = [
    {
        "label": "샘플 1: 예금 광고 (확정금리 위반)",
        "ad_copy": "JB 주거래 우대 정기예금 연 6.0% 확정금리! 지금 바로 가입하세요.",
        "product_type": "예금",
        "product_id": "JB-DEP-001",
    },
    {
        "label": "샘플 2: 대출 광고 (과장 표현 + 의무표시 누락)",
        "ad_copy": "JB 직장인 신용대출 연 4.5% 저금리! 지금 바로 대출, 당일 입금 보장. 누구나 가능.",
        "product_type": "대출",
        "product_id": "JB-LOAN-001",
    },
    {
        "label": "샘플 3: 펀드 광고 (원금보장 금지 표현)",
        "ad_copy": "JB KOSPI 200 ETF 총보수 연 0.05%. 위험등급 3등급. 원금 보장! 안전한 투자.",
        "product_type": "펀드",
        "product_id": "JB-FUND-002",
    },
    {
        "label": "샘플 4: 카드 광고 (연회비 불일치 + 최상급 표현)",
        "ad_copy": "JB 클래식 신용카드 연회비 없음! 편의점 5% 할인. 업계 최고 혜택.",
        "product_type": "카드",
        "product_id": "JB-CARD-001",
    },
]


def init_session():
    for key, val in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = val


def save_review_data(result: dict):
    st.session_state.review_result = result
    st.session_state.review_id = result.get("review_id")


def clear_session():
    for key, val in DEFAULTS.items():
        st.session_state[key] = val


def product_id_from_label(label: str) -> str:
    return label.split(" ")[0]
