"""
Milestone 2 - LangGraph orchestration workflow.

Flow:
    Query
      ↓
    Query Understanding
      ↓
    Query Router
      ↓
    Retrieval
      ↓
    Response Generation
      ↓
    Final Result

This file contains orchestration only.
Agent business logic remains inside the respective agent packages.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.query_understanding.agent import (
    QueryUnderstandingAgent,
)
from app.agents.query_understanding.schemas import (
    QueryUnderstandingResult,
)
from app.agents.retrieval.agent import RetrievalAgent
from app.agents.response_generation.agent import (
    generate_response,
)
from app.core.llm import get_llm
from app.orchestration.query_router import (
    get_route_reason,
    route_query,
)


# ---------------------------------------------------------------------
# Shared agent instances
# ---------------------------------------------------------------------

_llm = get_llm()

_query_understanding_agent = QueryUnderstandingAgent(
    _llm
)

_retrieval_agent = RetrievalAgent(
    default_k=3,
    semantic_candidate_multiplier=5,
    relevance_threshold=0.30,
    enable_diversification=True,
)


# ---------------------------------------------------------------------
# LangGraph state
# ---------------------------------------------------------------------

class WorkflowState(TypedDict, total=False):
    query: str
    k: int

    query_analysis: QueryUnderstandingResult

    route: str
    route_reason: str

    retrieval_result: dict[str, Any]

    response: dict[str, Any]

    error: str


# ---------------------------------------------------------------------
# Node 1 - Query Understanding
# ---------------------------------------------------------------------

def query_understanding_node(
    state: WorkflowState,
) -> WorkflowState:
    """Run Query Understanding Agent."""

    try:
        query = state.get("query", "").strip()

        if not query:
            raise ValueError(
                "Query cannot be empty."
            )

        analysis = _query_understanding_agent.run(
            query
        )

        return {
            **state,
            "query_analysis": analysis,
        }

    except Exception as error:
        return {
            **state,
            "error": (
                f"Query Understanding failed: {error}"
            ),
        }


# ---------------------------------------------------------------------
# Node 2 - Query Routing
# ---------------------------------------------------------------------

def routing_node(
    state: WorkflowState,
) -> WorkflowState:
    """Select the next resolution path."""

    if state.get("error"):
        return state

    analysis = state.get(
        "query_analysis"
    )

    if not isinstance(
        analysis,
        QueryUnderstandingResult,
    ):
        return {
            **state,
            "error": (
                "Invalid QueryUnderstandingResult "
                "received by router."
            ),
        }

    try:
        route = route_query(analysis)
        reason = get_route_reason(analysis)

        return {
            **state,
            "route": route,
            "route_reason": reason,
        }

    except Exception as error:
        return {
            **state,
            "error": (
                f"Query routing failed: {error}"
            ),
        }


# ---------------------------------------------------------------------
# Node 3 - Retrieval
# ---------------------------------------------------------------------

def retrieval_node(
    state: WorkflowState,
) -> WorkflowState:
    """Run the Retrieval Agent."""

    if state.get("error"):
        return state

    analysis = state.get(
        "query_analysis"
    )

    if not isinstance(
        analysis,
        QueryUnderstandingResult,
    ):
        return {
            **state,
            "error": (
                "Retrieval requires a valid "
                "QueryUnderstandingResult."
            ),
        }

    try:
        k = state.get("k", 3)

        retrieval_result = _retrieval_agent.run(
            analysis,
            k=k,
        )

        return {
            **state,
            "retrieval_result": retrieval_result,
        }

    except Exception as error:
        return {
            **state,
            "error": (
                f"Retrieval failed: {error}"
            ),
        }


# ---------------------------------------------------------------------
# Node 4 - Response Generation
# ---------------------------------------------------------------------

def response_generation_node(
    state: WorkflowState,
) -> WorkflowState:
    """Generate a grounded response from retrieved chunks."""

    if state.get("error"):
        return state

    query = state.get(
        "query",
        "",
    )

    retrieval_result = state.get(
        "retrieval_result",
        {},
    )

    chunks = retrieval_result.get(
        "results",
        [],
    )

    try:
        response = generate_response(
            question=query,
            chunks=chunks,
        )

        return {
            **state,
            "response": response.model_dump(),
        }

    except Exception as error:
        return {
            **state,
            "error": (
                f"Response Generation failed: {error}"
            ),
        }


# ---------------------------------------------------------------------
# Conditional routing
# ---------------------------------------------------------------------

def route_after_understanding(
    state: WorkflowState,
) -> str:
    """
    Decide which node runs after routing.

    Milestone 2 currently supports the retrieval path.

    Ambiguous queries are also sent to retrieval for now because the
    Clarification Agent is not yet part of the implemented workflow.
    """

    if state.get("error"):
        return "end"

    route = state.get(
        "route",
        "retrieval",
    )

    if route == "retrieval":
        return "retrieval"

    # Future:
    # if route == "clarification":
    #     return "clarification"

    return "retrieval"


# ---------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------

def build_workflow():
    """Build and compile the LangGraph workflow."""

    graph = StateGraph(
        WorkflowState
    )

    graph.add_node(
        "query_understanding",
        query_understanding_node,
    )

    graph.add_node(
        "routing",
        routing_node,
    )

    graph.add_node(
        "retrieval",
        retrieval_node,
    )

    graph.add_node(
        "response_generation",
        response_generation_node,
    )

    graph.add_edge(
        START,
        "query_understanding",
    )

    graph.add_edge(
        "query_understanding",
        "routing",
    )

    graph.add_conditional_edges(
        "routing",
        route_after_understanding,
        {
            "retrieval": "retrieval",
            "end": END,
        },
    )

    graph.add_edge(
        "retrieval",
        "response_generation",
    )

    graph.add_edge(
        "response_generation",
        END,
    )

    return graph.compile()


# Compile once and reuse.
workflow = build_workflow()


# ---------------------------------------------------------------------
# Public workflow API
# ---------------------------------------------------------------------

def run_workflow(
    query: str,
    k: int = 3,
) -> dict[str, Any]:
    """
    Run the complete Milestone 2 workflow.

    Args:
        query: User's natural-language query.
        k: Maximum number of retrieved chunks.

    Returns:
        Final LangGraph state as a dictionary.
    """

    if not isinstance(
        query,
        str,
    ) or not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    if not isinstance(
        k,
        int,
    ) or isinstance(
        k,
        bool,
    ):
        raise ValueError(
            "k must be an integer."
        )

    if k < 1:
        raise ValueError(
            "k must be at least 1."
        )

    initial_state: WorkflowState = {
        "query": query.strip(),
        "k": k,
    }

    result = workflow.invoke(
        initial_state
    )

    return dict(result)


# ---------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------

if __name__ == "__main__":

    result = run_workflow(
        "What does the Retrieval Agent do?",
        k=3,
    )

    print("\n" + "=" * 70)
    print("WORKFLOW TEST")
    print("=" * 70)

    print("\nRoute:")
    print(
        result.get("route")
    )

    print("\nRoute Reason:")
    print(
        result.get("route_reason")
    )

    print("\nQuery Understanding:")
    print(
        result.get("query_analysis")
    )

    print("\nRetrieval Statistics:")

    retrieval = result.get(
        "retrieval_result"
    )

    if retrieval:
        print(
            retrieval.get(
                "retrieval"
            )
        )

    print("\nResponse:")
    print(
        result.get("response")
    )

    if result.get("error"):
        print("\nERROR:")
        print(
            result["error"]
        )