import streamlit as st

AGENT_STEPS = [
    {
        "id": "agent1",
        "name": "Agent 1: 규제 검색",
        "desc": "RAG + 국가법령정보센터 실시간 조회",
        "source": "rag",
        "source_label": "🔵 RAG  🟣 MCP #1 LIVE",
        "duration": 2.5,
    },
    {
        "id": "agent2",
        "name": "Agent 2: 스펙 교차 검증",
        "desc": "상품 DB와 광고 수치 비교",
        "source": "spec",
        "source_label": "🟣 MCP #2 상품 DB",
        "duration": 1.2,
    },
    {
        "id": "agent3",
        "name": "Agent 3: 의무표시 체크",
        "desc": "금지 표현 / 의무 문구 누락 검사",
        "source": "disclosure",
        "source_label": "🟢 Rule Engine",
        "duration": 0.8,
    },
    {
        "id": "agent4",
        "name": "Agent 4: 종합 위험도 판단",
        "desc": "LLM 기반 위험도 종합 평가",
        "source": "llm",
        "source_label": "🤖 LLM (Groq)",
        "duration": 2.0,
    },
    {
        "id": "agent5",
        "name": "Agent 5: 수정안 생성",
        "desc": "규정 준수 카피 자동 생성",
        "source": "llm",
        "source_label": "🤖 LLM (Groq)",
        "duration": 2.5,
    },
    {
        "id": "agent6",
        "name": "Agent 6: 자기 검증",
        "desc": "수정안 재검증 루프 (최대 3회)",
        "source": "loop",
        "source_label": "🔄 자기 검증 루프",
        "duration": 1.5,
    },
    {
        "id": "agent7",
        "name": "Agent 7: 다국어 변환",
        "desc": "영어/중국어 번역 + 문화권 검증",
        "source": "llm",
        "source_label": "🤖 LLM (Groq)",
        "duration": 3.0,
    },
]


def render_agent_card(agent: dict, status: str, verify_count: int = 0):
    """
    status: 'pending' | 'running' | 'done' | 'error'
    """
    STATUS_CONFIG = {
        "pending": {"icon": "⏳", "bg": "#F9FAFB", "border": "#E5E7EB", "text": "#6B7280"},
        "running": {"icon": "⚙️", "bg": "#EFF6FF", "border": "#3B82F6", "text": "#1E40AF"},
        "done":    {"icon": "✅", "bg": "#F0FDF4", "border": "#10B981", "text": "#065F46"},
        "error":   {"icon": "❌", "bg": "#FEF2F2", "border": "#DC2626", "text": "#991B1B"},
    }
    cfg = STATUS_CONFIG.get(status, STATUS_CONFIG["pending"])

    extra = ""
    if agent["id"] == "agent6" and status == "running":
        extra = f'<div style="font-size:12px; color:#7C3AED; margin-top:4px;">🔄 재검증 {verify_count}/3</div>'
    elif agent["id"] == "agent6" and status == "done":
        extra = f'<div style="font-size:12px; color:#065F46; margin-top:4px;">✅ {verify_count}회 검증 통과</div>'

    live_badge = ""
    if agent["id"] == "agent1" and status == "running":
        live_badge = '<span style="background:#DC2626; color:white; border-radius:4px; padding:2px 6px; font-size:11px; font-weight:700; animation:pulse 1s infinite;">🔴 LIVE</span>'

    st.markdown(
        f'<div style="background:{cfg["bg"]}; border:1.5px solid {cfg["border"]}; border-radius:10px;'
        f'padding:14px 18px; margin-bottom:10px;">'
        f'<div style="display:flex; justify-content:space-between; align-items:center;">'
        f'<div style="font-weight:700; font-size:15px; color:{cfg["text"]};">{cfg["icon"]} {agent["name"]}</div>'
        f'{live_badge}'
        f'</div>'
        f'<div style="font-size:13px; color:#6B7280; margin-top:4px;">{agent["desc"]}</div>'
        f'<div style="font-size:12px; color:#9CA3AF; margin-top:6px;">{agent["source_label"]}</div>'
        f'{extra}'
        f'</div>',
        unsafe_allow_html=True,
    )
