"""
Theme extractor using claude-haiku-4-5 with forced tool_use.

Same pattern as sentiment_classifier, but with a richer output schema.
Key design choice: the theme enum is populated at runtime from config/brand.yaml
via build_theme_tool(). This means Claude can only return themes in the brand's
taxonomy — it cannot hallucinate or invent new categories.
"""
import copy
from pathlib import Path
import anthropic

SYSTEM_PROMPT = Path(__file__).parent.parent / "prompts" / "theme_extraction.txt"

_BASE_THEME_TOOL = {
    "name": "extract_themes",
    "description": "Extract product and experience themes from a customer review",
    "input_schema": {
        "type": "object",
        "properties": {
            "themes": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [],  # Populated at runtime from brand config
                },
                "description": "Themes present in this review (max 3)",
                "maxItems": 3,
            },
            "primary_theme": {
                "type": "string",
                "enum": [],  # Populated at runtime from brand config
                "description": "The single most prominent theme in this review",
            },
            "theme_evidence": {
                "type": "object",
                "description": "Brief quote or paraphrase from the review supporting each theme",
                "additionalProperties": {"type": "string"},
            },
        },
        "required": ["themes", "primary_theme", "theme_evidence"],
    },
}


def build_theme_tool(valid_themes: list[str]) -> dict:
    """
    Inject brand-specific theme taxonomy into the tool schema.
    Call this once after loading config, then reuse the tool for all reviews.

    Args:
        valid_themes: List of theme strings from config['themes']

    Returns:
        Tool definition dict with enum constraints set to valid_themes
    """
    tool = copy.deepcopy(_BASE_THEME_TOOL)
    tool["input_schema"]["properties"]["themes"]["items"]["enum"] = valid_themes
    tool["input_schema"]["properties"]["primary_theme"]["enum"] = valid_themes
    return tool


def extract_themes(review: dict, theme_tool: dict, client: anthropic.Anthropic) -> dict:
    """
    Extract themes from a single review using the brand-configured theme tool.

    Args:
        review: Internal review dict (must have 'rating' and 'text' keys)
        theme_tool: Tool definition from build_theme_tool()
        client: Anthropic client instance

    Returns:
        Dict matching theme tool schema:
        {themes: list[str], primary_theme: str, theme_evidence: dict[str, str]}
    """
    system = SYSTEM_PROMPT.read_text()
    user_content = f"Rating: {review['rating']}/5\n\nReview: {review['text']}"

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        system=system,
        tools=[theme_tool],
        tool_choice={"type": "tool", "name": "extract_themes"},
        messages=[{"role": "user", "content": user_content}],
    )

    tool_block = next(b for b in response.content if b.type == "tool_use")
    return tool_block.input
