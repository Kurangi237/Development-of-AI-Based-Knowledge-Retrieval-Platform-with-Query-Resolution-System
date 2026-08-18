"""
Groq LLM handler for the Response Generation Agent.

Uses the same centralized LLM configuration as the Query Understanding
Agent:

    backend/.env
        ↓
    app/core/llm.py
        ↓
    get_llm()
        ↓
    ChatGroq
"""

from __future__ import annotations

from app.core.llm import get_llm


class GroqHandler:
    """
    Thin wrapper around the shared LangChain Groq model.
    """

    def __init__(self) -> None:
        self.llm = get_llm()

    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a response from the shared LLM.

        Args:
            prompt:
                Grounded response-generation prompt.

        Returns:
            Generated text.

        Raises:
            ValueError:
                If the prompt is empty.

            RuntimeError:
                If the LLM request fails or returns empty content.
        """

        if not isinstance(
            prompt,
            str,
        ):
            raise ValueError(
                "Prompt must be a string."
            )

        prompt = prompt.strip()

        if not prompt:
            raise ValueError(
                "Prompt cannot be empty."
            )

        try:
            response = self.llm.invoke(
                prompt
            )

            answer = (
                response.content
                if hasattr(
                    response,
                    "content",
                )
                else str(response)
            )

            if not isinstance(
                answer,
                str,
            ):
                answer = str(answer)

            answer = answer.strip()

            if not answer:
                raise RuntimeError(
                    "LLM returned an empty response."
                )

            return answer

        except ValueError:
            raise

        except RuntimeError:
            raise

        except Exception as error:
            raise RuntimeError(
                f"LLM request failed: {error}"
            )


if __name__ == "__main__":

    handler = GroqHandler()

    test_prompt = (
        "Answer briefly: What is 2 + 2?"
    )

    print(
        "Sending test prompt to shared LLM..."
    )

    print(
        handler.generate(
            test_prompt
        )
    )