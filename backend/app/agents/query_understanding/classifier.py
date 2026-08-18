from .schemas import QueryClassification
from langchain_core.language_models import BaseChatModel


def classify_query(
    llm: BaseChatModel,
    query: str,
) -> QueryClassification:
    """
    Classify a user query into exactly one supported query type.

    Uses Groq's JSON Schema structured-output mode so that the
    GPT-OSS model returns a validated QueryClassification object
    instead of relying on tool/function calling.
    """

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    # Use native JSON Schema structured output.
    structured_llm = llm.with_structured_output(
        QueryClassification,
        method="json_schema",
        strict=True,
    )

    prompt = f"""
You are a query classification component in a knowledge retrieval system.

Classify the user's query into exactly ONE of these four categories:

1. factual
   - The user wants a fact, definition, explanation, or specific piece of information.
   - Example: "What is the company's headquarters?"

2. procedural
   - The user wants instructions, steps, or information about how to perform an action.
   - Example: "How do I apply for leave?"

3. comparative
   - The user explicitly wants to compare two or more entities, options, concepts, or items.
   - Example: "What is the difference between Plan A and Plan B?"

4. ambiguous
   - The query is unclear, incomplete, or does not provide enough context to determine the user's intent.
   - Example: "Tell me more about that."

Important rules:
- Return exactly one category.
- Do not classify a query as ambiguous merely because it is short.
- If the user's intent is clear, choose factual, procedural, or comparative.
- Do not invent information that is not present in the query.

User query:
{query}
"""

    return structured_llm.invoke(prompt)