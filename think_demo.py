"""
DeepSeek V3.1 Thinking Mode Demo — Ollama Cloud

Uses the `think=True` flag to enable the model's internal
chain-of-thought reasoning before producing a final answer.

Usage:
    set OLLAMA_API_KEY=your_api_key_here
    python think_demo.py
"""
import os
from dotenv import load_dotenv
from ollama import Client

load_dotenv()


def main():
    api_key = os.environ.get("OLLAMA_API_KEY")
    if not api_key:
        print("❌ Missing OLLAMA_API_KEY environment variable.")
        print("   Set it with:  set OLLAMA_API_KEY=your_api_key_here")
        return

    client = Client(
        host="https://ollama.com",
        headers={"Authorization": f"Bearer {api_key}"},
    )

    # Change this to any question you'd like the model to reason about
    question = input("🧠 Enter your question: ").strip()
    if not question:
        print("No question provided, exiting.")
        return

    messages = [{"role": "user", "content": question}]

    print("\n🧠 Thinking…\n")

    thinking_started = False
    answer_started = False

    for part in client.chat(
        model="deepseek-v3.1:671b-cloud",
        messages=messages,
        stream=True,
        think=True,
    ):
        thinking = part["message"].get("thinking", "")
        content = part["message"].get("content", "")

        if thinking:
            if not thinking_started:
                print("── Chain of Thought ──")
                thinking_started = True
            print(thinking, end="", flush=True)

        if content:
            if not answer_started:
                if thinking_started:
                    print("\n\n── Final Answer ──")
                else:
                    print("── Answer ──")
                answer_started = True
            print(content, end="", flush=True)

    print("\n\n✅ Done!")


if __name__ == "__main__":
    main()
