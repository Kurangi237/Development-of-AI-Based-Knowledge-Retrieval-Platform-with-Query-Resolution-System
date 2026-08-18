"""
Schemas used by the Response Generation Agent.

The schemas are designed to preserve:
- grounded answer
- source citation
- source/chunk identity
- retrieval relevance
- source metadata
- confidence score
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Source(BaseModel):
    """
    A source referenced by the generated answer.

    `reference` is the citation marker used inside the answer,
    for example "[1]".

    `source` is a human-readable source name, normally the
    uploaded filename.

    `chunk_id` identifies the actual retrieved chunk.

    `relevance_score` preserves the score calculated by the
    Retrieval Agent when available.
    """

    source: str = Field(
        description="Human-readable source name, usually the filename."
    )

    reference: str = Field(
        description="Citation marker used in the answer, e.g. [1]."
    )

    chunk_id: str | None = Field(
        default=None,
        description="Unique identifier of the retrieved chunk."
    )

    relevance_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Retrieval relevance score for the cited chunk."
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata associated with the cited chunk."
    )


class LLMResponse(BaseModel):
    """
    Final response returned by the Response Generation Agent.
    """

    answer: str = Field(
        description="Grounded answer generated from retrieved context."
    )

    sources: list[Source] = Field(
        default_factory=list,
        description="Sources explicitly cited by the answer."
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description=(
            "Confidence estimate based on retrieval relevance "
            "and source citation coverage."
        )
    )


if __name__ == "__main__":

    response = LLMResponse(
        answer=(
            "The Retrieval Agent performs semantic search "
            "and ranks retrieved chunks by relevance. [1]"
        ),
        sources=[
            Source(
                source="project.pdf",
                reference="[1]",
                chunk_id="chunk_001",
                relevance_score=0.91,
                metadata={
                    "filename": "project.pdf",
                    "chunk_index": 2,
                },
            )
        ],
        confidence=0.91,
    )

    print("Schema validation successful!")
    print()
    print(
        response.model_dump_json(
            indent=4
        )
    )