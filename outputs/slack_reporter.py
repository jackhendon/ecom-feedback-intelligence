"""
Slack reporter — posts a summary to a Slack webhook.

Enable in config/brand.yaml:
    reporting:
      slack_enabled: true

Add to .env:
    SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

Pattern mirrors the existing photo-book analyst agent for consistency.
"""
import os
import requests


def post_to_slack(insights: dict, aggregated: dict, config: dict) -> None:
    """
    Post a formatted insight summary to Slack.

    Args:
        insights: Output from insight_generator.generate_insights()
        aggregated: Output from orchestrator.aggregate_results()
        config: Brand config dict
    """
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("      Warning: SLACK_WEBHOOK_URL not set — skipping Slack post")
        return

    brand = config["brand"]["name"]
    period = aggregated.get("period", "unknown")
    review_count = aggregated["review_count"]

    dist = aggregated.get("sentiment_distribution", {})
    pos_pct = dist.get("positive", {}).get("pct", 0)
    neg_pct = dist.get("negative", {}).get("pct", 0)

    trend = insights.get("sentiment_trend", "stable")
    trend_emoji = {"improving": ":chart_with_upwards_trend:", "stable": ":arrow_right:", "declining": ":chart_with_downwards_trend:"}.get(trend, ":arrow_right:")

    # Build Slack blocks for rich formatting
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f":memo: {brand} Feedback Insights — {period}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": insights.get("executive_summary", "_No summary generated._"),
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Reviews analysed:*\n{review_count}"},
                {"type": "mrkdwn", "text": f"*Sentiment trend:*\n{trend_emoji} {trend.capitalize()}"},
                {"type": "mrkdwn", "text": f"*Positive:*\n{pos_pct}%"},
                {"type": "mrkdwn", "text": f"*Negative:*\n{neg_pct}%"},
            ],
        },
        {"type": "divider"},
    ]

    # Top opportunity
    opportunities = insights.get("top_opportunities", [])
    if opportunities:
        top = opportunities[0]
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f":bulb: *Top Opportunity*\n"
                        f"*{top.get('opportunity', 'N/A')}*\n"
                        f"_{top.get('suggested_action', 'N/A')}_\n"
                        f"Effort: {top.get('effort_estimate', '?')} | Impact: {top.get('impact_estimate', '?')}"
                    ),
                },
            }
        )

    # Top risk
    risks = insights.get("top_risks", [])
    if risks:
        top_risk = risks[0]
        urgency_emoji = {"monitor": ":blue_circle:", "address_soon": ":yellow_circle:", "urgent": ":red_circle:"}.get(top_risk.get("urgency", "monitor"), ":blue_circle:")
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"{urgency_emoji} *Top Risk*\n"
                        f"*{top_risk.get('risk', 'N/A')}*\n"
                        f"{top_risk.get('frequency', '?')} reviews | Urgency: {top_risk.get('urgency', '?')}"
                    ),
                },
            }
        )

    payload = {"blocks": blocks}
    response = requests.post(webhook_url, json=payload, timeout=10)
    response.raise_for_status()
