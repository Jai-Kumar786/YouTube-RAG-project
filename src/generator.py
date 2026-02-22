from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

def generate_answer(question: str, context_docs: list[Document]) -> str:
    """
    Uses DeepSeek (via Ollama) to generate an answer based purely on the retrieved context.
    """
    print("Generating answer using DeepSeek...")
    
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
    
    # Initialize the DeepSeek model via Ollama
    # Note: adjust the model name if you pulled a specific tag like 'deepseek-coder'
    llm = ChatOllama(model="deepseek-v3.1:671b-cloud") 
    
    # Create the LCEL (LangChain Expression Language) chain
    chain = prompt | llm
    
    # Execute the chain
    response = chain.invoke({"context": context_text, "question": question})
    
    # Return the text content of the AI's response
    return response.content