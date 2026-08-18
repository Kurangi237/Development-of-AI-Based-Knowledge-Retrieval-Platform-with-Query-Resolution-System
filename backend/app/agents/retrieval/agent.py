"""
Milestone 2 - Retrieval Agent

Coordinates:
    1. Semantic retrieval
    2. Exact retrieval
    3. Candidate merging
    4. Query-aware reranking
    5. Low-confidence filtering
    6. Final context selection

The Retrieval Agent consumes QueryUnderstandingResult produced
by the Query Understanding Agent.

LangGraph should call this class as one graph node.

No LLM is required inside this agent.
"""

from __future__ import annotations

from typing import Any

from app.agents.query_understanding.schemas import (
    QueryUnderstandingResult,
)

from app.agents.retrieval.exact_search import (
    search_exact,
)

from app.agents.retrieval.reranker import (
    diversify_results,
    rerank_results,
)

from app.agents.retrieval.semantic_search import (
    search_semantic,
)


class RetrievalAgent:
    """
    Query-aware Retrieval Agent.

    The agent uses the Query Understanding output to decide what
    information should be passed into semantic search, exact search,
    and reranking.
    """

    def __init__(
        self,
        *,
        default_k: int = 3,
        semantic_candidate_multiplier: int = 5,
        relevance_threshold: float = 0.20,
        enable_diversification: bool = True,
    ) -> None:
        """
        Initialize the Retrieval Agent.

        Args:
            default_k:
                Number of final chunks returned.

            semantic_candidate_multiplier:
                Retrieve more semantic candidates than the final k
                so reranking has a larger candidate pool.

            relevance_threshold:
                Minimum relevance score allowed after reranking.

            enable_diversification:
                Prevent repetitive chunks from occupying the entire
                final context.
        """
        if default_k < 1:
            raise ValueError(
                "default_k must be at least 1."
            )

        if semantic_candidate_multiplier < 1:
            raise ValueError(
                "semantic_candidate_multiplier must be at least 1."
            )

        if not 0.0 <= relevance_threshold <= 1.0:
            raise ValueError(
                "relevance_threshold must be between 0.0 and 1.0."
            )

        self.default_k = default_k

        self.semantic_candidate_multiplier = (
            semantic_candidate_multiplier
        )

        self.relevance_threshold = relevance_threshold

        self.enable_diversification = (
            enable_diversification
        )

    # -----------------------------------------------------------------
    # Candidate merging
    # -----------------------------------------------------------------

    @staticmethod
    def _normalize_content(
        content: Any,
    ) -> str:
        """
        Normalize chunk content for deduplication.
        """
        if not isinstance(content, str):
            return ""

        return " ".join(
            content.lower().split()
        )

    @staticmethod
    def _merge_terms(
        first: list[str] | None,
        second: list[str] | None,
    ) -> list[str]:
        """
        Merge matched terms without duplicates.
        """
        merged: list[str] = []
        seen: set[str] = set()

        for term in [*(first or []), *(second or [])]:
            if not isinstance(term, str):
                continue

            cleaned = term.strip()

            if not cleaned:
                continue

            key = cleaned.lower()

            if key not in seen:
                seen.add(key)
                merged.append(cleaned)

        return merged

    def _merge_results(
        self,
        semantic_results: list[dict[str, Any]],
        exact_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Merge semantic and exact-search candidates.

        Duplicate chunks are merged by normalized content.

        When the same chunk is found by both retrieval mechanisms,
        exact-match information is preserved.
        """
        merged: dict[str, dict[str, Any]] = {}

        # -------------------------------------------------------------
        # Semantic results
        # -------------------------------------------------------------

        for result in semantic_results:
            if not isinstance(result, dict):
                continue

            content = result.get(
                "content",
                "",
            )

            key = self._normalize_content(
                content
            )

            if not key:
                continue

            item = dict(result)

            item["matched_terms"] = list(
                result.get(
                    "matched_terms",
                    [],
                )
                or []
            )

            merged[key] = item

        # -------------------------------------------------------------
        # Exact-search results
        # -------------------------------------------------------------

        for result in exact_results:
            if not isinstance(result, dict):
                continue

            content = result.get(
                "content",
                "",
            )

            key = self._normalize_content(
                content
            )

            if not key:
                continue

            if key not in merged:
                item = dict(result)

                item["matched_terms"] = list(
                    result.get(
                        "matched_terms",
                        [],
                    )
                    or []
                )

                merged[key] = item
                continue

            existing = merged[key]

            existing["matched_terms"] = self._merge_terms(
                existing.get("matched_terms"),
                result.get("matched_terms"),
            )

            # Keep semantic distance when already available.
            if (
                existing.get("distance") is None
                and result.get("distance") is not None
            ):
                existing["distance"] = result["distance"]

        return list(
            merged.values()
        )

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    @staticmethod
    def _validate_query_analysis(
        query_analysis: QueryUnderstandingResult,
    ) -> None:
        """
        Validate the Query Understanding output before retrieval.
        """
        if not isinstance(
            query_analysis,
            QueryUnderstandingResult,
        ):
            raise TypeError(
                "query_analysis must be a "
                "QueryUnderstandingResult."
            )

        if not query_analysis.search_query.strip():
            raise ValueError(
                "QueryUnderstandingResult.search_query "
                "cannot be empty."
            )

    # -----------------------------------------------------------------
    # Main retrieval method
    # -----------------------------------------------------------------

    def retrieve(
    self,
    query_analysis: QueryUnderstandingResult,
    *,
    k: int | None = None,
) -> dict[str, Any]:
        """
        Run the complete Retrieval Agent pipeline.

        Flow:
            QueryUnderstandingResult
                ↓
            Semantic Search
                +
            Exact Search
                ↓
            Merge
                ↓
            Query-aware Reranking
                ↓
            Low-confidence filtering
                ↓
            Diversification
                ↓
            Top-K
        """

        self._validate_query_analysis(
            query_analysis
        )

        final_k = (
            k
            if k is not None
            else self.default_k
        )

        if final_k < 1:
            raise ValueError(
                "k must be at least 1."
            )

        search_query = (
            query_analysis.search_query.strip()
        )

        exact_terms = list(
            query_analysis.exact_terms
        )

        keywords = list(
            query_analysis.keywords
        )

        query_type = (
            query_analysis.query_type
        )

        # -------------------------------------------------------------
        # 1. Semantic candidate generation
        # -------------------------------------------------------------

        semantic_k = max(
            10,
            final_k
            * self.semantic_candidate_multiplier,
        )

        semantic_results = search_semantic(
            query=search_query,
            k=semantic_k,
        )

        if not isinstance(
            semantic_results,
            list,
        ):
            semantic_results = []

        # -------------------------------------------------------------
        # 2. Exact candidate generation
        # -------------------------------------------------------------

        exact_results: list[
            dict[str, Any]
        ] = []

        if exact_terms:
            exact_results = search_exact(
                exact_terms
            )

            if not isinstance(
                exact_results,
                list,
            ):
                exact_results = []

        # -------------------------------------------------------------
        # 3. Merge semantic + exact candidates
        # -------------------------------------------------------------

        candidates = self._merge_results(
            semantic_results=semantic_results,
            exact_results=exact_results,
        )

        # -------------------------------------------------------------
        # 4. Query-aware reranking
        # -------------------------------------------------------------

        ranked_results = rerank_results(
            candidates,
            exact_terms=exact_terms,
            keywords=keywords,
            query_type=query_type,
            exact_candidates_found=bool(
                exact_results
            ),
            relevance_threshold=(
                self.relevance_threshold
            ),
        )

        # -------------------------------------------------------------
        # 5. Diversification
        # -------------------------------------------------------------

        if self.enable_diversification:
            final_results = diversify_results(
                ranked_results,
                max_results=final_k,
            )
        else:
            final_results = ranked_results[
                :final_k
            ]

        final_results = final_results[
            :final_k
        ]

        # -------------------------------------------------------------
        # 6. Return structured result
        # -------------------------------------------------------------

        return {
            "success": True,
            "query": query_analysis.original_query,
            "search_query": search_query,
            "query_type": query_type,
            "results": final_results,
            "count": len(final_results),
            "retrieval": {
                "semantic_candidates": len(
                    semantic_results
                ),
                "exact_candidates": len(
                    exact_results
                ),
                "merged_candidates": len(
                    candidates
                ),
                "returned_results": len(
                    final_results
                ),
            },
        }

    # -----------------------------------------------------------------
    # Convenience method for LangGraph
    # -----------------------------------------------------------------

    def run(
        self,
        query_analysis: QueryUnderstandingResult,
        *,
        k: int | None = None,
    ) -> dict[str, Any]:
        """
        Alias for retrieve().

        This provides a simple callable interface for LangGraph
        node integration.
        """
        return self.retrieve(
            query_analysis,
            k=k,
        )