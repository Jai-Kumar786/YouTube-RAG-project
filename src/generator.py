import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

# Read model name from environment (configurable via .env)
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-v3.1:671b-cloud")

def generate_answer(question: str, context_docs: list[Document]) -> str:
    """
    Uses DeepSeek (via Ollama) to generate an answer based purely on the retrieved context.
    """
    print(f"Generating answer using {LLM_MODEL}...")
    
    # Combine the document chunks into a single readable string
    context_text = "\n\n---\n\n".join([doc.page_content for doc in context_docs])
    
    # Define a strict prompt template to prevent hallucination
    prompt_template = """
    You are an expert assistant. Answer the question based ONLY on the following context from YouTube transcripts.
    If the context does not contain the answer, say "I don't know based on the provided transcripts." Do not make up information.
    
    Context:
    {context}
    
    Question:
    {question}
    
    Answer:
    """
    
    prompt = ChatPromptTemplate.from_template(prompt_template)
    
    # Initialize the LLM via Ollama using the configured model name
    llm = ChatOllama(model=LLM_MODEL) 
    
    # Create the LCEL (LangChain Expression Language) chain
    chain = prompt | llm
    
    # Execute the chain
    response = chain.invoke({"context": context_text, "question": question})
    
    # Return the text content of the AI's response
    return response.content


def generate_video_summary(transcript_text: str) -> dict:
    """
    Analyzes the transcript and generates a short title and 3 suggested questions.
    Returns {"title": "...", "suggested_questions": ["...", "...", "..."]}
    """
    import json as _json

    # Use first ~2000 chars for efficiency
    snippet = transcript_text[:2000]

    prompt_template = """You are given a snippet from a YouTube video transcript.
Based on this content, generate:
1. A short, descriptive title for the video (maximum 8 words, no quotes)
2. Exactly 3 interesting questions a viewer might want answered from this video

You MUST respond in this exact JSON format and nothing else:
{{"title": "Your Title Here", "suggested_questions": ["Question 1?", "Question 2?", "Question 3?"]}}

Transcript snippet:
{snippet}"""

    prompt = ChatPromptTemplate.from_template(prompt_template)
    llm = ChatOllama(model=LLM_MODEL)
    chain = prompt | llm

    try:
        response = chain.invoke({"snippet": snippet})
        raw = response.content.strip()

        # Try to extract JSON from the response (LLM may wrap it in markdown)
        if "```" in raw:
            # Extract content between code fences
            parts = raw.split("```")
            for part in parts:
                cleaned = part.strip()
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()
                if cleaned.startswith("{"):
                    raw = cleaned
                    break

        data = _json.loads(raw)
        title = str(data.get("title", "Untitled Video"))[:60]
        questions = data.get("suggested_questions", [])
        # Ensure exactly 3 questions (strings only)
        questions = [str(q) for q in questions if isinstance(q, str)][:3]

        return {"title": title, "suggested_questions": questions}
    except Exception as e:
        print(f"Warning: could not generate video summary: {e}")
        return {"title": "Untitled Video", "suggested_questions": []}