import re

from nemoguardrails.actions import action
from nemoguardrails.actions.rail_outcome import RailOutcome


OTHER_TENANT_PATTERNS = (
    r"\bshow me another tenant'?s data\b",
    r"\bshow me another tenant data\b",
    r"\bgive me another customer'?s records\b",
    r"\baccess data from another tenant\b",
)


@action(is_system_action=True)
async def check_other_tenant_data(
    context: dict | None = None,
) -> RailOutcome:
    user_message = ""

    if context is not None:
        user_message = context.get("user_message", "")

    normalized = user_message.strip().lower()

    for pattern in OTHER_TENANT_PATTERNS:
        if re.search(pattern, normalized):
            return RailOutcome.block(
                reason="Cross-tenant data access is not allowed."
            )

    return RailOutcome.allow()
