import streamlit as st

SEVERITY_STYLE = {
    "HIGH":   {"bg": "#FEE2E2", "border": "#DC2626", "text": "#991B1B", "label": "HIGH"},
    "MEDIUM": {"bg": "#FEF3C7", "border": "#F59E0B", "text": "#92400E", "label": "MED"},
    "LOW":    {"bg": "#D1FAE5", "border": "#10B981", "text": "#065F46", "label": "LOW"},
}

SOURCE_BADGE = {
    "spec":       ("🟣", "#8B5CF6", "상품 DB"),
    "disclosure": ("🟢", "#10B981", "Rule Engine"),
    "rag":        ("🔵", "#3B82F6", "RAG"),
}


def _severity_badge(severity: str) -> str:
    s = SEVERITY_STYLE.get(severity, SEVERITY_STYLE["LOW"])
    return (
        f'<span style="background:{s["bg"]}; color:{s["text"]}; border:1px solid {s["border"]};'
        f'border-radius:4px; padding:2px 8px; font-size:12px; font-weight:700;">{s["label"]}</span>'
    )


def _source_badge(source: str) -> str:
    icon, color, label = SOURCE_BADGE.get(source, ("⚪", "#6B7280", source))
    return (
        f'<span style="background:{color}22; color:{color}; border:1px solid {color}55;'
        f'border-radius:4px; padding:2px 8px; font-size:12px;">{icon} {label}</span>'
    )


def render_violation_card(v: dict, expanded: bool = False):
    vid = v.get("id", "")
    severity = v.get("severity", "LOW")
    source = v.get("source", "")
    message = v.get("message", "")
    legal_basis = v.get("legal_basis", "")
    item = v.get("item", "")

    s = SEVERITY_STYLE.get(severity, SEVERITY_STYLE["LOW"])

    with st.expander(
        f"[{severity}] {vid} — {message[:60]}{'...' if len(message) > 60 else ''}",
        expanded=expanded,
    ):
        st.markdown(
            f'<div style="background:{s["bg"]}; border-left:4px solid {s["border"]};'
            f'border-radius:6px; padding:12px 16px; margin-bottom:8px;">'
            f'{_severity_badge(severity)}&nbsp;&nbsp;{_source_badge(source)}'
            f'</div>',
            unsafe_allow_html=True,
        )
        if item:
            st.markdown(f"**위반 유형:** {item}")
        st.markdown(f"**내용:** {message}")
        if legal_basis:
            st.markdown(f"**근거 조항:** `{legal_basis}`")


def render_risk_banner(risk_level: str, violation_count: int, risk_summary: str):
    RISK = {
        "HIGH":   {"bg": "#FEE2E2", "border": "#DC2626", "text": "#991B1B", "label": "높음 🔴"},
        "MEDIUM": {"bg": "#FEF3C7", "border": "#F59E0B", "text": "#92400E", "label": "중간 🟠"},
        "LOW":    {"bg": "#D1FAE5", "border": "#10B981", "text": "#065F46", "label": "낮음 🟢"},
    }
    r = RISK.get(risk_level, RISK["LOW"])
    st.markdown(
        f'<div style="background:{r["bg"]}; border:2px solid {r["border"]}; border-radius:12px;'
        f'padding:20px 24px; margin-bottom:20px;">'
        f'<div style="font-size:28px; font-weight:800; color:{r["text"]};">종합 위험도: {r["label"]}</div>'
        f'<div style="font-size:16px; color:{r["text"]}; margin-top:4px;">위반 항목 {violation_count}건</div>'
        f'<hr style="border-color:{r["border"]}55; margin:12px 0;">'
        f'<div style="font-size:14px; color:#374151; line-height:1.6;">{risk_summary}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
