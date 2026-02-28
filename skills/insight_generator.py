"""
Insight generator using claude-sonnet-4-6 with forced tool_use.

This is the PM-facing centrepiece of the pipeline. Unlike the classification skills
(which run per-review on Haiku), this runs once per analysis period on Sonnet to
produce structured, actionable recommendations.

The INSIGHT_TOOL schema reflects how a PM actually thinks:
  - effort/impact as enums (not scores) for quick prioritisation
  - urgency levels for risks (monitor / address_soon / urgent)
  - recommended_experiments as concrete next steps, not vague suggestions
"""
import json
from pathlib import Path
import anthropic

SYSTEM_PROMPT = Path(__file__).parent.parent / "prompts" / "insight_synthesis.txt"

INSIGHT_TOOL = {
    "name": "generate_pm_insights",
    "description": "Generate structured PM-ready insights from aggregated customer review data",
    "input_schema": {
        "type": "object",
        "properties": {
            "executive_summary": {
                "type": "string",
                "description": "2-3 sentence summary for a VP-level audience. Lead with the most important signal.",
            },
            "sentiment_trend": {
                "type": "string",
                "enum": ["improving", "stable", "declining"],
                "description": "Direction of overall sentiment vs previous periods. Use 'stable' if insufficient history.",
            },
            "top_opportunities": {
                "type": "array",
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "opportunity": {
                            "type": "string",
                            "description": "Specific, concrete opportunity (not vague)",
                        },
                        "supporting_evidence": {
                            "type": "string",
                            "description": "Data or review quotes that support this opportunity",
                        },
                        "suggested_action": {
                            "type": "string",
                            "description": "Specific action to take — testable or investigable",
                        },
                        "effort_estimate": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                        "impact_estimate": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                        },
                    },
                    "required": [
                        "opportunity",
                        "supporting_evidence",
                        "suggested_action",
                        "effort_estimate",
                        "impact_estimate",
                    ],
                },
            },
            "top_risks": {
                "type": "array",
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "properties": {
                        "risk": {
                            "type": "string",
                            "description": "Specific recurring issue that threatens customer satisfaction or retention",
                        },
                        "frequency": {
                            "type": "integer",
                            "description": "Approximate number of reviews mentioning this issue",
                        },
                        "urgency": {
                            "type": "string",
                            "enum": ["monitor", "address_soon", "urgent"],
                        },
                    },
                    "required": ["risk", "frequency", "urgency"],
                },
            },
            "recommended_experiments": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific A/B tests, investigations, or initiatives to run. Be concrete.",
                "maxItems": 3,
            },
        },
        "required": [
            "executive_summary",
            "sentiment_trend",
            "top_opportunities",
            "top_risks",
            "recommended_experiments",
        ],
    },
}


def generate_insights(
    aggregated_data: dict, history: dict, client: anthropic.Anthropic
) -> dict:
    """
    Synthesise PM-ready insights from aggregated review data and historical context.

    Uses claude-sonnet-4-6 (not Haiku) — this is the only place in the pipeline
    where quality matters more than cost. Called once per run, not per review.

    Args:
        aggregated_data: Output from orchestrator's aggregate_results()
        history: Dict from memory/history.json (may be empty on first run)
        client: Anthropic client instance

    Returns:
        Dict matching INSIGHT_TOOL schema with executive_summary, opportunities, risks, experiments
    """
    system = SYSTEM_PROMPT.read_text()

    snapshot_count = len(history.get("snapshots", []))
    history_context = (
        f"Historical data: {snapshot_count} previous period(s) available.\n"
        f"{json.dumps(history.get('snapshots', [])[-3:], indent=2)}"  # last 3 snapshots
        if snapshot_count > 0
        else "Historical data: this is the first run — no prior periods to compare against."
    )

    user_content = (
        f"Current period analysis ({aggregated_data.get('period', 'unknown')}):\n"
        f"{json.dumps(aggregated_data, indent=2)}\n\n"
        f"{history_context}\n\n"
        "Generate PM-ready insights and recommendations."
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system,
        tools=[INSIGHT_TOOL],
        tool_choice={"type": "tool", "name": "generate_pm_insights"},
        messages=[{"role": "user", "content": user_content}],
    )

    tool_block = next(b for b in response.content if b.type == "tool_use")
    return tool_block.input
