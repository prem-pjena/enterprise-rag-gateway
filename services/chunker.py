from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter

from services.embeddings import gemini_embeddings


def create_parents(
    text: str,
    parent_size: int = 3000,
    parent_overlap: int = 200,
) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=parent_size,
        chunk_overlap=parent_overlap,
        separators=["\n\n", "\n", " ", ""],
    )

    return splitter.split_text(text)


def create_children(
    parent: str,
    child_size: int = 800,
    child_overlap: int = 100,
) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=child_size,
        chunk_overlap=child_overlap,
        separators=["\n\n", "\n", " ", ""],
    )

    return splitter.split_text(parent)


def create_semantic_chunks(
    text: str,
) -> list[str]:
    splitter = SemanticChunker(
        gemini_embeddings,
    )

    return splitter.split_text(text)