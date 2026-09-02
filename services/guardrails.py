from pathlib import Path

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.integrations.langchain.runnable_rails import (
    RunnableRails,
)
from nemoguardrails.rails.llm.options import RailStatus


GUARDRAILS_PATH = (
    Path(__file__).resolve().parent.parent / "guardrails"
)

config = RailsConfig.from_path(str(GUARDRAILS_PATH))

rails = LLMRails(config)

guardrails = RunnableRails(
    config,
    passthrough=True,
)


async def check_input(question: str) -> str | None:
    result = await rails.check_async(
        messages=[
            {
                "role": "user",
                "content": question,
            }
        ]
    )

    if result.status == RailStatus.BLOCKED:
        return (
            "I'm sorry, I can't help with access "
            "to another tenant's data."
        )

    return None