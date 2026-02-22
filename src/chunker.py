from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def chunk_text(text: str, video_id: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[Document]:
    """
    Uses LangChain's RecursiveCharacterTextSplitter to split a long transcript
    into smaller, overlapping Document objects with metadata suitable for vector embeddings.
    
    chunk_size: The maximum number of characters in a chunk.
    chunk_overlap: The number of characters to overlap between chunks to preserve context.
    """
    # Initialize the LangChain text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # It attempts to split by double newline first, then single newline, then space
        separators=["\n\n", "\n", " ", ""] 
    )
    
    # Split the text into Document objects and inject the video_id as metadata
    metadata = {"video_id": video_id}
    docs = text_splitter.create_documents([text], metadatas=[metadata])
    
    return docs