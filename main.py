"""
YouTube RAG Pipeline — CLI entry point.

Commands:
    python main.py ingest <youtube_url>   Fetch, chunk, embed & store the transcript.
    python main.py ask "<question>"        Ask a question about the ingested video.
"""
from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

console = Console()


def cmd_ingest(args):
    """Run the full ingestion pipeline: fetch → chunk → embed → store."""
    from src.ingest import fetch_transcript
    from src.chunker import chunk_transcript
    from src.store import init_db, embed_and_store, clear_chunks

    url = args.url

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 1 — Fetch transcript
        task = progress.add_task("Fetching transcript…", total=None)
        transcript, segments = fetch_transcript(url)
        progress.update(task, description=f"✅ Transcript fetched ({len(transcript):,} chars)")
        progress.stop_task(task)

        # Step 2 — Chunk
        task = progress.add_task("Chunking transcript…", total=None)
        chunks = chunk_transcript(transcript, segments, source_url=url)
        progress.update(task, description=f"✅ Created {len(chunks)} chunks")
        progress.stop_task(task)

        # Print sample chunks
        console.print("\n[bold]Sample Chunks:[/bold]")
        for i in range(min(5, len(chunks))):
            meta = chunks[i].metadata
            console.print(f"  [{i+1}] Start: {meta['start_time']:.1f}s, End: {meta['end_time']:.1f}s, Tokens: {meta['token_count']}, Content: {chunks[i].page_content[:150]}…")
        console.print()

        # Step 3 — Init DB & store
        task = progress.add_task("Initialising database…", total=None)
        init_db()
        progress.update(task, description="✅ Database ready")
        progress.stop_task(task)

        if args.clear:
            task = progress.add_task("Clearing old chunks…", total=None)
            clear_chunks()
            progress.update(task, description="✅ Old chunks cleared")
            progress.stop_task(task)

        task = progress.add_task("Embedding & storing chunks…", total=None)
        count = embed_and_store(chunks)
        progress.update(task, description=f"✅ Stored {count} chunks in PostgreSQL")
        progress.stop_task(task)

    console.print(
        Panel(
            f"[bold green]Done![/bold green]  Ingested [cyan]{url}[/cyan] → {count} chunks stored.",
            title="📹 Ingestion Complete",
        )
    )


def cmd_ask(args):
    """Retrieve relevant chunks and generate an answer."""
    from src.retriever import retrieve
    from src.generator import generate_answer, LLM_MODEL

    query = args.question

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Searching transcript…", total=None)
        chunks = retrieve(query, top_k=args.top_k)
        progress.update(task, description=f"✅ Found {len(chunks)} relevant excerpts")
        progress.stop_task(task)

    if args.think:
        console.print()
        thinking_started = False
        answer_started = False
        for thinking, content in generate_answer(query, chunks, think=True):
            if thinking:
                if not thinking_started:
                    console.print("── Chain of Thought ──")
                    thinking_started = True
                print(thinking, end="", flush=True)
            if content:
                if not answer_started:
                    if thinking_started:
                        console.print("\n\n── Final Answer ──")
                    else:
                        console.print("── Answer ──")
                    answer_started = True
                print(content, end="", flush=True)
        console.print("\n\n✅ Done!")
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Generating answer with {LLM_MODEL}…", total=None)
            result = ""
            for _, content in generate_answer(query, chunks, think=False):
                result += content
            progress.update(task, description="✅ Answer generated")
            progress.stop_task(task)

        console.print()
        console.print(Panel(Markdown(result), title="💬 Answer", border_style="green"))

    if args.show_sources:
        console.print()
        console.print("[bold]📄 Sources used:[/bold]")
        for i, chunk in enumerate(chunks, 1):
            score = chunk.get("score", "?")
            console.print(f"  [{i}] (score: {score}) {chunk['content'][:120]}…")


def main():
    parser = argparse.ArgumentParser(
        description="YouTube RAG Pipeline — ask questions about any YouTube video.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- ingest ---
    p_ingest = subparsers.add_parser("ingest", help="Ingest a YouTube video transcript.")
    p_ingest.add_argument("url", help="YouTube video URL or video ID.")
    p_ingest.add_argument("--clear", action="store_true", help="Clear existing chunks before ingesting.")
    p_ingest.set_defaults(func=cmd_ingest)

    # --- ask ---
    p_ask = subparsers.add_parser("ask", help="Ask a question about the ingested video.")
    p_ask.add_argument("question", help="Your question (in quotes).")
    p_ask.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve (default: 5).")
    p_ask.add_argument("--show-sources", action="store_true", help="Show the source excerpts used.")
    p_ask.add_argument("--think", action="store_true", help="Enable thinking mode for chain-of-thought reasoning.")
    p_ask.set_defaults(func=cmd_ask)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
