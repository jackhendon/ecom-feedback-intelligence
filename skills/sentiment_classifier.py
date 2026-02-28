"""
Sentiment classifier using claude-haiku-4-5 with forced tool_use.

This is the simplest skill and establishes the tool_use pattern used throughout.
Key design choice: tool_choice={"type": "tool", "name": "..."} forces a structured
response — no JSON parsing, no regex, guaranteed schema compliance.
"""
from pathlib import Path
import anthropic

SYSTEM_PROMPT = Path(__file__).parent.parent / "prompts" / "sentiment_classification.txt"

SENTIMENT_TOOL = {
    "name": "classify_sentiment",
    "description": "Classify the overall sentiment of a customer review",
    "input_schema": {
        "type": "object",
        "properties": {
            "sentiment": {
                "type": "string",
                "enum": ["positive", "neutral", "negative"],
                "description": "Overall sentiment of the review",
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score between 0.0 and 1.0",
            },
            "sentiment_drivers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key phrases or points that drove this classification (max 3)",
            },
        },
        "required": ["sentiment", "confidence", "sentiment_drivers"],
    },
}


def classify_sentiment(review: dict, client: anthropic.Anthropic) -> dict:
    """
    Classify the sentiment of a single review.

    Args:
        review: Internal review dict (must have 'rating' and 'text' keys)
        client: Anthropic client instance

    Returns:
        Dict matching SENTIMENT_TOOL schema:
        {sentiment: str, confidence: float, sentiment_drivers: list[str]}
    """
    system = SYSTEM_PROMPT.read_text()
    user_content = f"Rating: {review['rating']}/5\n\nReview: {review['text']}"

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        system=system,
        tools=[SENTIMENT_TOOL],
        tool_choice={"type": "tool", "name": "classify_sentiment"},
        messages=[{"role": "user", "content": user_content}],
    )

    tool_block = next(b for b in response.content if b.type == "tool_use")
    return tool_block.input
