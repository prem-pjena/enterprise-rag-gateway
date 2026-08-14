from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

from core.config import settings


prompt = ChatPromptTemplate.from_template(
    "Answer the question using the provided context.\n\n"
    "Context:\n{context}\n\n"
    "Question:\n{question}"
)


llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=settings.GOOGLE_API_KEY,
)


output_parser = StrOutputParser()


chain = prompt | llm | output_parser


async def generate_answer(
    context: str,
    question: str,
) -> str:
    return await chain.ainvoke(
        {
            "context": context,
            "question": question,
        }
    )