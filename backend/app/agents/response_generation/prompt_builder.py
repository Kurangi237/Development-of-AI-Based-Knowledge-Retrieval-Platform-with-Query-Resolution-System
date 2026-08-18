"""
Prompt construction for the Response Generation Agent.

The prompt is deliberately domain-agnostic.

It accepts retrieved chunks from the Retrieval Agent and instructs
the LLM to:
1. Answer only from the supplied context.
2. Avoid unsupported claims.
3. Clearly state when the context is insufficient.
4. Cite the supplied chunks using [1], [2], etc.
"""

from __future__ import annotations

from typing import Any


def format_chunks(
    chunks: list[dict[str, Any] | str],
) -> str:
    """
    Format retrieved chunks into numbered source blocks.

    Retrieval Agent result shape supported:

    {
        "id": ...,
        "content": ...,
        "metadata": ...,
        "distance": ...,
        "matched_terms": ...,
        "relevance_score": ...
    }

    Extra retrieval fields are not exposed as instructions to the
    model, but useful source metadata is included for citation.
    """

    if not chunks:
        return ""

    lines: list[str] = []

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        if isinstance(chunk, dict):

            content = str(
                chunk.get(
                    "content",
                    "",
                )
            ).strip()

            if not content:
                continue

            chunk_id = chunk.get(
                "id"
            )

            metadata = chunk.get(
                "metadata",
                {},
            )

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}

            filename = metadata.get(
                "filename"
            )

            chunk_index = metadata.get(
                "chunk_index"
            )

            source_parts: list[str] = []

            if filename:
                source_parts.append(
                    f"source={filename}"
                )

            if chunk_index is not None:
                source_parts.append(
                    f"chunk={chunk_index}"
                )

            if chunk_id:
                source_parts.append(
                    f"id={chunk_id}"
                )

            source_label = (
                " | ".join(source_parts)
                if source_parts
                else "source=unknown"
            )

            lines.append(
                f"[{index}] {source_label}\n"
                f"{content}"
            )

        else:

            content = str(
                chunk
            ).strip()

            if not content:
                continue

            lines.append(
                f"[{index}]\n{content}"
            )

    return "\n\n".join(
        lines
    )


def build_prompt(
    question: str,
    chunks: list[dict[str, Any] | str],
) -> str:
    """
    Build the grounded answer-generation prompt.
    """

    context = format_chunks(
        chunks
    )

    if not context:
        context = (
            "No relevant context was retrieved."
        )

    prompt = f"""
You are the Response Generation Agent of a knowledge retrieval system.

Answer the user's question using ONLY the retrieved context below.

Rules:
1. Do not use outside knowledge.
2. Do not invent facts, values, names, dates, policies, or explanations.
3. If the context does not contain enough information to answer the
   question, clearly say that the available knowledge base does not
   contain enough information.
4. When making a factual claim from the context, cite the corresponding
   source using [1], [2], [3], etc.
5. Use only citation numbers that actually exist in the provided context.
6. Do not create or guess citations.
7. When multiple sources provide relevant evidence, cite all relevant
   sources.
8. Prefer a concise, direct answer.
9. If the retrieved context contains conflicting information, explicitly
   mention the conflict and cite the conflicting sources instead of
   choosing one without evidence.

Retrieved Context:
------------------
{context}
------------------

User Question:
{question}

Answer:
"""

    return prompt.strip()


if __name__ == "__main__":

    sample_chunks = [
        {
            "id": "chunk_001",
            "content": (
                "Employees are entitled to "
                "12 days of paid leave per year."
            ),
            "metadata": {
                "filename": "hr_policy.pdf",
                "chunk_index": 3,
            },
            "relevance_score": 0.91,
        },
        {
            "id": "chunk_002",
            "content": (
                "Sick leave requests longer than "
                "2 days require a medical certificate."
            ),
            "metadata": {
                "filename": "hr_policy.pdf",
                "chunk_index": 4,
            },
            "relevance_score": 0.82,
        },
    ]

    prompt = build_prompt(
        question="How many leave days do employees get?",
        chunks=sample_chunks,
    )

    print(prompt)