"""
Main pipeline orchestrator.

Wires ingestion, classification, aggregation, insight generation, and output
into a single end-to-end run. No business logic lives here — it only orchestrates.

Usage:
    python -m agents.orchestrator
    python -m agents.orchestrator --config config/brand.yaml
    python -m agents.orchestrator --dry-run  # skips API calls, useful for testing

Cost estimate with 100 reviews (as of 2026):
  Sentiment (Haiku): 100 x ~200 tokens = 20K tokens ≈ $0.005
  Themes (Haiku):    100 x ~300 tokens = 30K tokens ≈ $0.0075
  Insights (Sonnet): 1 x ~2K tokens    =  2K tokens ≈ $0.006
  Total per run: ~$0.02 (less than 2 cents)
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import yaml
from anthropic import Anthropic, RateLimitError

from agents.ingestion.trustpilot import TrustPilotConnector
from skills.sentiment_classifier import classify_sentiment
from skills.theme_extractor import extract_themes, build_theme_tool
from skills.priority_scorer import score_reviews
from skills.insight_generator import generate_insights
from outputs.markdown_reporter import generate_markdown_report
from outputs.slack_reporter import post_to_slack

# Model selection — visible here to demonstrate intentional cost/quality trade-off
CLASSIFICATION_MODEL = "claude-haiku-4-5"  # bulk per-review classification
SYNTHESIS_MODEL = "claude-sonnet-4-6"      # single synthesis call at end


def load_config(path: str = "config/brand.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_history(history_path: str) -> dict:
    path = Path(history_path)
    if path.exists():
        content = path.read_text().strip()
        if content:
            return json.loads(content)
    return {"snapshots": []}


def update_history(aggregated: dict, config: dict) -> dict:
    """Append current snapshot and enforce the rolling window."""
    history_path = config["memory"]["history_file"]
    max_snapshots = config["memory"]["max_snapshots"]

    history = load_history(history_path)
    history["snapshots"].append(aggregated)
    history["snapshots"] = history["snapshots"][-max_snapshots:]

    Path(history_path).parent.mkdir(parents=True, exist_ok=True)
    Path(history_path).write_text(json.dumps(history, indent=2))
    return history


def aggregate_results(classified_reviews: list[dict]) -> dict:
    """
    Pure Python aggregation — no LLM needed.
    Groups themes, computes sentiment distribution, surfaces high-priority issues.
    """
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    theme_counts: dict[str, int] = {}
    high_priority: list[dict] = []

    for review in classified_reviews:
        # Sentiment distribution
        s = review["sentiment"]["sentiment"]
        sentiment_counts[s] = sentiment_counts.get(s, 0) + 1

        # Theme frequency
        for theme in review["themes"].get("themes", []):
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

        # Surface high-priority negatives for insight generator context
        if review["priority_score"] >= 7.0 and s == "negative":
            high_priority.append(
                {
                    "text": review["text"][:250],
                    "primary_theme": review["themes"].get("primary_theme", "unknown"),
                    "priority_score": review["priority_score"],
                    "rating": review["rating"],
                    "date": review["date"],
                }
            )

    total = len(classified_reviews)
    return {
        "period": datetime.now().strftime("%Y-W%V"),
        "run_date": datetime.now().strftime("%Y-%m-%d"),
        "review_count": total,
        "sentiment_distribution": {
            k: {"count": v, "pct": round(v / total * 100, 1) if total > 0 else 0}
            for k, v in sentiment_counts.items()
        },
        "theme_frequency": dict(
            sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        ),
        "high_priority_issues": sorted(
            high_priority, key=lambda x: x["priority_score"], reverse=True
        )[:10],
    }


def _call_with_retry(fn, max_retries: int = 3):
    """Exponential backoff wrapper for Anthropic API calls."""
    for attempt in range(max_retries):
        try:
            return fn()
        except RateLimitError:
            wait = 2 ** attempt
            print(f"    Rate limited, waiting {wait}s before retry {attempt + 1}/{max_retries}...")
            time.sleep(wait)
    raise RuntimeError(f"Anthropic API rate limit: max retries ({max_retries}) exceeded")


def classify_all_reviews(
    reviews: list[dict],
    theme_tool: dict,
    client: Anthropic,
    batch_size: int = 10,
    dry_run: bool = False,
) -> list[dict]:
    """Classify all reviews in batches with rate-limit protection."""
    for i in range(0, len(reviews), batch_size):
        batch = reviews[i : i + batch_size]
        for j, review in enumerate(batch):
            overall = i + j + 1
            print(f"    [{overall}/{len(reviews)}] {review['review_id']}", end=" ")

            if dry_run:
                # Stub outputs for dry runs — no API calls
                review["sentiment"] = {
                    "sentiment": "neutral",
                    "confidence": 0.5,
                    "sentiment_drivers": ["[dry-run]"],
                }
                review["themes"] = {
                    "themes": ["product_quality"],
                    "primary_theme": "product_quality",
                    "theme_evidence": {},
                }
                print("(dry-run)")
            else:
                review["sentiment"] = _call_with_retry(
                    lambda r=review: classify_sentiment(r, client)
                )
                review["themes"] = _call_with_retry(
                    lambda r=review: extract_themes(r, theme_tool, client)
                )
                print(f"→ {review['sentiment']['sentiment']}, {review['themes']['primary_theme']}")

        # Brief pause between batches to respect rate limits
        if not dry_run and i + batch_size < len(reviews):
            time.sleep(0.5)

    return reviews


def run_pipeline(config_path: str = "config/brand.yaml", dry_run: bool = False) -> dict:
    config = load_config(config_path)
    brand = config["brand"]["name"]

    if dry_run:
        print(f"\n=== DRY RUN — no API calls will be made ===\n")

    print(f"[1/6] Ingesting reviews for {brand}...")
    connector = TrustPilotConnector(config)
    reviews = connector.fetch()
    print(f"      Loaded {len(reviews)} reviews\n")

    print(f"[2/6] Classifying {len(reviews)} reviews ({CLASSIFICATION_MODEL})...")
    theme_tool = build_theme_tool(config["themes"])
    reviews = classify_all_reviews(reviews, theme_tool, Anthropic(), dry_run=dry_run)
    print()

    print("[3/6] Scoring priority (deterministic, no LLM)...")
    reviews = score_reviews(reviews, config)
    high_pri = sum(1 for r in reviews if r["priority_score"] >= 7.0)
    print(f"      {high_pri} high-priority reviews (score ≥ 7.0)\n")

    print("[4/6] Aggregating results...")
    aggregated = aggregate_results(reviews)
    history = update_history(aggregated, config)
    neg_pct = aggregated["sentiment_distribution"]["negative"]["pct"]
    pos_pct = aggregated["sentiment_distribution"]["positive"]["pct"]
    print(f"      Positive: {pos_pct}% | Negative: {neg_pct}%")
    top_themes = list(aggregated["theme_frequency"].items())[:3]
    print(f"      Top themes: {', '.join(f'{t} ({c})' for t, c in top_themes)}\n")

    print(f"[5/6] Generating insights ({SYNTHESIS_MODEL})...")
    if dry_run:
        insights = {
            "executive_summary": "[Dry run — no insights generated]",
            "sentiment_trend": "stable",
            "top_opportunities": [],
            "top_risks": [],
            "recommended_experiments": [],
        }
    else:
        insights = _call_with_retry(
            lambda: generate_insights(aggregated, history, Anthropic())
        )
    print(f"      Done — {len(insights.get('top_opportunities', []))} opportunities, "
          f"{len(insights.get('top_risks', []))} risks identified\n")

    print("[6/6] Writing outputs...")
    if config["reporting"]["markdown_enabled"]:
        report_path = generate_markdown_report(insights, aggregated, config)
        print(f"      Report: {report_path}")

    if config["reporting"]["slack_enabled"]:
        post_to_slack(insights, aggregated, config)
        print("      Slack: message posted")

    print("\nDone.")
    return insights


def main():
    parser = argparse.ArgumentParser(description="ecom-feedback-intelligence pipeline")
    parser.add_argument(
        "--config",
        default="config/brand.yaml",
        help="Path to brand config file (default: config/brand.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline without making API calls (for testing)",
    )
    args = parser.parse_args()
    run_pipeline(config_path=args.config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
