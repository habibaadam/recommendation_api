"""Format a recommendation for a short channel. A real sender would call a provider API."""

def format_sms(user_id: str, items: list[str], limit: int = 160) -> str:
    text = f"Hi {user_id}, picks for you: " + ", ".join(items)
    return text if len(text) <= limit else text[: limit - 3] + "..."