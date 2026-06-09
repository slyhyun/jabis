from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
import operator

from backend.app.agents.agent2_spec import run_agent2


# ============================================================
# State 정의
# ============================================================

class JABISState(TypedDict):
    # 입력
    ad_copy: str                        # 심의 요청 광고 카피
    product_type: str                   # 상품 유형 (예금, 대출, 펀드 등)
    product_id: str                     # 상품 ID (MCP #2 조회용)

    # Agent 1: 규제 검색 결과
    regulation_results: list            # 관련 법령 및 규제 조항 목록

    # Agent 2: 스펙 교차 검증 결과
    spec_violations: list               # 상품 스펙 불일치 위반 목록

    # Agent 3: 의무표시 체크 결과
    disclosure_violations: list         # 의무표시 누락 위반 목록

    # Agent 4: 종합 위험도 판단 결과
    risk_level: str                     # 위험도 (HIGH / MEDIUM / LOW)
    risk_summary: str                   # 위험도 요약 설명

    # Agent 5: 수정안 생성 결과
    revised_copy: str                   # 수정된 광고 카피

    # Agent 6: 자기 검증 루프
    verification_count: int             # 검증 반복 횟수 (최대 3회)
    is_verified: bool                   # 검증 통과 여부

    # Agent 7: 다국어 변환 결과
    multilingual: dict                  # {"en": "...", "zh": "..."}

    # 최종 결과
    final_result: dict                  # 심의 최종 결과 요약


# ============================================================
# Agent 노드 함수 (Placeholder)
# ============================================================

def agent1_regulation_search(state: JABISState) -> dict:
    """Agent 1: 규제 검색 (RAG + MCP #1)"""
    print(f"[Agent 1] 규제 검색 시작: {state['ad_copy'][:30]}...")
    # TODO: RAG 호출 + 국가법령정보센터 MCP 호출
    return {"regulation_results": []}


def agent2_spec_verify(state: JABISState) -> dict:
    """Agent 2: 스펙 교차 검증"""
    result = run_agent2(
        ad_copy=state["ad_copy"],
        product_type=state["product_type"],
        product_id=state["product_id"],
    )
    return {"spec_violations": result["spec_violations"]}


def agent3_disclosure_check(state: JABISState) -> dict:
    """Agent 3: 의무표시 체크 (Rule Engine)"""
    print(f"[Agent 3] 의무표시 체크 시작")
    # TODO: Rule Engine 적용 (정규식 + 키워드 매칭)
    return {"disclosure_violations": []}


def agent4_risk_assessment(state: JABISState) -> dict:
    """Agent 4: 종합 위험도 판단 (LLM)"""
    print(f"[Agent 4] 종합 위험도 판단 시작")
    # TODO: 규제/스펙/의무표시 위반 통합 후 LLM으로 위험도 판단
    return {
        "risk_level": "LOW",
        "risk_summary": "위반 사항 없음 (임시값)",
    }


def agent5_revise_copy(state: JABISState) -> dict:
    """Agent 5: 수정안 생성 (LLM)"""
    print(f"[Agent 5] 수정안 생성 시작")
    # TODO: 위반 항목 기반 LLM 수정안 생성
    return {"revised_copy": state["ad_copy"]}


def agent6_self_verify(state: JABISState) -> dict:
    """Agent 6: 자기 검증 루프 (최대 3회)"""
    count = state.get("verification_count", 0) + 1
    print(f"[Agent 6] 자기 검증 {count}회차")
    # TODO: 수정안이 규제를 준수하는지 재검토
    return {
        "verification_count": count,
        "is_verified": True,  # 임시로 통과 처리
    }


def agent7_multilingual(state: JABISState) -> dict:
    """Agent 7: 다국어 변환 (영어, 중국어)"""
    print(f"[Agent 7] 다국어 변환 시작")
    # TODO: LLM으로 영어/중국어 번역
    return {
        "multilingual": {"en": "", "zh": ""},
        "final_result": {
            "ad_copy": state["ad_copy"],
            "risk_level": state.get("risk_level", ""),
            "revised_copy": state.get("revised_copy", ""),
        },
    }


# ============================================================
# 조건부 엣지: Agent 6 루프 제어
# ============================================================

def should_continue_verification(state: JABISState) -> str:
    """검증 통과 or 최대 3회 도달 시 Agent 7로, 아니면 Agent 5로 재시도"""
    if state.get("is_verified") or state.get("verification_count", 0) >= 3:
        return "agent7"
    return "agent5"


# ============================================================
# LangGraph 워크플로우 구성
# ============================================================

def create_jabis_graph():
    graph = StateGraph(JABISState)

    # 노드 등록
    graph.add_node("agent1", agent1_regulation_search)
    graph.add_node("agent2", agent2_spec_verify)
    graph.add_node("agent3", agent3_disclosure_check)
    graph.add_node("agent4", agent4_risk_assessment)
    graph.add_node("agent5", agent5_revise_copy)
    graph.add_node("agent6", agent6_self_verify)
    graph.add_node("agent7", agent7_multilingual)

    # 엣지 연결
    graph.add_edge(START, "agent1")
    graph.add_edge("agent1", "agent2")
    graph.add_edge("agent2", "agent3")
    graph.add_edge("agent3", "agent4")
    graph.add_edge("agent4", "agent5")
    graph.add_edge("agent5", "agent6")

    # Agent 6 조건부 엣지 (검증 루프)
    graph.add_conditional_edges(
        "agent6",
        should_continue_verification,
        {
            "agent5": "agent5",  # 재시도
            "agent7": "agent7",  # 통과
        },
    )

    graph.add_edge("agent7", END)

    return graph.compile()


# 워크플로우 인스턴스
jabis_graph = create_jabis_graph()


# ============================================================
# 동작 테스트
# ============================================================

if __name__ == "__main__":
    result = jabis_graph.invoke({
        "ad_copy": "JB금융 정기예금 연 5.0% 확정금리! 지금 바로 가입하세요.",
        "product_type": "예금",
        "product_id": "JB-DEP-001",
        "verification_count": 0,
        "is_verified": False,
    })

    print("\n=== 최종 결과 ===")
    print(f"위험도: {result.get('risk_level')}")
    print(f"수정안: {result.get('revised_copy')}")
    print(f"검증 횟수: {result.get('verification_count')}")
