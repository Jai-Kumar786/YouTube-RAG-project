"""
Generation & guardrails — answers questions using only the retrieved
transcript context via Ollama deepseek-v3.1, with optional thinking mode.
"""
from __future__ import annotations

import os
from ollama import Client
from dotenv import load_dotenv

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-v3.1:671b-cloud")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")

SYSTEM_PROMPT = """\
You are a helpful assistant that answers questions about a YouTube video.

RULES — follow these strictly:
1. Answer ONLY using the transcript excerpts provided below.
2. If the answer cannot be found in the excerpts, reply exactly:
   "This question is not covered in the video."
3. Do NOT use any outside knowledge.
4. When possible, cite the excerpt number(s) you used (e.g., [1], [3]).
5. Keep your answer concise and well-structured.
"""


def _build_context_block(chunks: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block."""
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        lines.append(f"[{i}] {chunk['content']}")
    return "\n\n".join(lines)


def generate_answer(query: str, context_chunks: list[dict], think: bool = False):
    """
    Generate an answer to the query using only the provided transcript chunks.
    Yields (thinking, content) tuples for streaming.
    """
    if not context_chunks:
        yield "", "No relevant transcript excerpts were found. This question is not covered in the video."
        return

    context = _build_context_block(context_chunks)
    user_content = (
        f"TRANSCRIPT EXCERPTS:\n{context}\n\n"
        f"QUESTION: {query}"
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    api_key = os.environ.get("OLLAMA_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else None

    client = Client(
        host=OLLAMA_BASE_URL,
        headers=headers,
    )

    for part in client.chat(
        model=LLM_MODEL,
        messages=messages,
        stream=True,
        think=think,
    ):
        thinking = part["message"].get("thinking", "")
        content = part["message"].get("content", "")
        yield thinking, content
