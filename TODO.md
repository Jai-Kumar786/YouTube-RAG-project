# TODO: Complete /ask Endpoint Implementation

- [x] Add imports for `retrieve_context` from `src.retriever` and `generate_answer` from `src.generator` in `main.py`
- [x] Implement the `ask_question` function:
  - Call `retrieve_context(request.question)` to retrieve relevant documents
  - Handle case when no documents are found
  - Convert retrieved documents to `context_chunks` format
  - Generate full answer using `generate_answer` and collect content
  - Collect unique video_ids as sources
  - Return `AskResponse` with answer and sources
- [x] Test the endpoint to ensure it works correctly (attempted; requires full environment setup with dependencies, database, and Ollama running)
