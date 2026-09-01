from collections.abc import AsyncIterator

from pydantic import BaseModel
from pydantic_ai import Agent


class AnswerResponse(BaseModel):
    answer: str


agent = Agent(
    "google:gemini-3.6-flash",
    output_type=AnswerResponse,
)


def build_prompt(
    context: str,
    question: str,
) -> str:
    return (
        "Answer the question using the provided context.\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{question}"
    )


async def generate_answer(
    context: str,
    question: str,
) -> str:
    prompt = build_prompt(
        context=context,
        question=question,
    )

    result = await agent.run(prompt)

    return result.output.answer


async def stream_answer(
    context: str,
    question: str,
) -> AsyncIterator[str]:
    prompt = build_prompt(
        context=context,
        question=question,
    )

    async with agent.run_stream(prompt) as result:
        async for output in result.stream_output():
            yield output.answer