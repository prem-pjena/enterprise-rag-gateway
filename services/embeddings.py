from google import genai
from google.genai import types
from langchain_core.embeddings import Embeddings

from core.config import settings


client = genai.Client(
    api_key=settings.GOOGLE_API_KEY,
)


async def embed_text(text: str) -> list[float]:
    response = await client.aio.models.embed_content(
        model="gemini-embedding-2",
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=768,
        ),
    )

    return response.embeddings[0].values


async def embed_query(text: str) -> list[float]:
    return await embed_text(text)


class GeminiEmbeddings(Embeddings):
    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return [
            embed_text_sync(text)
            for text in texts
        ]

    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        return embed_text_sync(text)


def embed_text_sync(text: str) -> list[float]:
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=768,
        ),
    )

    return response.embeddings[0].values


gemini_embeddings = GeminiEmbeddings()