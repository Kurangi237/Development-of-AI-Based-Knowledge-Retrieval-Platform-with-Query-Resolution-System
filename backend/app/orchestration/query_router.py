"""
Milestone 2 - Query Routing

The router decides which resolution path should be followed after
Query Understanding.

Current Milestone 2 behavior:
    factual
    procedural
    comparative
        -> retrieval

    ambiguous
        -> retrieval for now, because the Clarification Agent belongs
           to a later milestone.

The router is intentionally deterministic and contains no LLM call.
"""

from __future__ import annotations

from typing import Literal

from app.agents.query_understanding.schemas import (
    QueryUnderstandingResult,
)


RouteName = Literal[
    "retrieval",
    "clarification",
]


SUPPORTED_RETRIEVAL_TYPES = {
    "factual",
    "procedural",
    "comparative",
}

# Clarification is planned for a later milestone.
# Keep the route name available now so the graph can be extended
# without redesigning the routing interface.
AMBIGUOUS_QUERY_TYPE = "ambiguous"


def normalize_query_type(
    query_type: str | None,
) -> str:
    """
    Normalize a query type returned by Query Understanding.
    """

    if not isinstance(query_type, str):
        return "ambiguous"

    normalized = query_type.strip().lower()

    if not normalized:
        return "ambiguous"

    return normalized


def route_query(
    query_analysis: QueryUnderstandingResult,
) -> RouteName:
    """
    Decide the next resolution path.

    Current Milestone 2:
        factual       -> retrieval
        procedural    -> retrieval
        comparative   -> retrieval
        ambiguous     -> retrieval

    Why ambiguous -> retrieval for now?
        The Clarification Agent is a later-milestone component.
        We still want the current Milestone 2 graph to complete
        instead of introducing an unavailable node.

    Once the Clarification Agent is implemented, the ambiguous branch
    can simply return "clarification".
    """

    if not isinstance(
        query_analysis,
        QueryUnderstandingResult,
    ):
        raise TypeError(
            "query_analysis must be a "
            "QueryUnderstandingResult."
        )

    query_type = normalize_query_type(
        query_analysis.query_type
    )

    if query_type in SUPPORTED_RETRIEVAL_TYPES:
        return "retrieval"

    if query_type == AMBIGUOUS_QUERY_TYPE:
        # Future:
        # return "clarification"
        return "retrieval"

    # Safe fallback for unexpected classifier output.
    return "retrieval"


def get_route_reason(
    query_analysis: QueryUnderstandingResult,
) -> str:
    """
    Return a human-readable explanation of the selected path.

    Useful for debugging and future analytics.
    """

    query_type = normalize_query_type(
        query_analysis.query_type
    )

    if query_type == "factual":
        return (
            "Factual query routed to semantic/exact retrieval."
        )

    if query_type == "procedural":
        return (
            "Procedural query routed to semantic/exact retrieval."
        )

    if query_type == "comparative":
        return (
            "Comparative query routed to semantic/exact retrieval."
        )

    if query_type == "ambiguous":
        return (
            "Ambiguous query currently routed to retrieval; "
            "Clarification Agent can replace this path in a later milestone."
        )

    return (
        "Unknown query type safely routed to retrieval."
    )


if __name__ == "__main__":
    from app.agents.query_understanding.schemas import (
        QueryUnderstandingResult,
    )

    test_cases = [
        "factual",
        "procedural",
        "comparative",
        "ambiguous",
    ]

    for query_type in test_cases:

        analysis = QueryUnderstandingResult(
            original_query="Test query",
            normalized_query="Test query",
            search_query="Test query",
            query_type=query_type,
            entities=[],
            keywords=["test"],
            exact_terms=[],
        )

        print(
            f"{query_type:12} -> "
            f"{route_query(analysis)}"
        )
        print(
            "Reason:",
            get_route_reason(analysis),
        )
        print()