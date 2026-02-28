"""
Integration tests for the orchestrator pipeline.

Tests use the dry_run flag to verify the pipeline flow and aggregation
logic without making real API calls.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from agents.orchestrator import aggregate_results, load_config, update_history


SAMPLE_CONFIG = {
    "brand": {"name": "TestBrand", "industry": "test"},
    "review_sources": {"trustpilot": {"mock_mode": True, "sample_file": "data/examples/trustpilot_sample.json"}},
    "themes": ["delivery", "product_quality", "packaging", "personalisation"],
    "sentiment": {"weights": {"negative": 2.0, "neutral": 1.0, "positive": 0.5}},
    "reporting": {"slack_enabled": False, "markdown_enabled": False, "output_dir": "/tmp/test_reports"},
    "memory": {"history_file": "/tmp/test_history.json", "max_snapshots": 5},
}

SAMPLE_CLASSIFIED_REVIEWS = [
    {
        "review_id": "r1",
        "source": "trustpilot",
        "rating": 1,
        "text": "Terrible",
        "date": "2026-02-20",
        "author": "A",
        "sentiment": {"sentiment": "negative", "confidence": 0.95, "sentiment_drivers": ["terrible"]},
        "themes": {"themes": ["delivery"], "primary_theme": "delivery", "theme_evidence": {}},
        "priority_score": 9.5,
    },
    {
        "review_id": "r2",
        "source": "trustpilot",
        "rating": 5,
        "text": "Excellent",
        "date": "2026-02-19",
        "author": "B",
        "sentiment": {"sentiment": "positive", "confidence": 0.98, "sentiment_drivers": ["excellent"]},
        "themes": {"themes": ["product_quality"], "primary_theme": "product_quality", "theme_evidence": {}},
        "priority_score": 1.0,
    },
    {
        "review_id": "r3",
        "source": "trustpilot",
        "rating": 3,
        "text": "Average",
        "date": "2026-02-18",
        "author": "C",
        "sentiment": {"sentiment": "neutral", "confidence": 0.7, "sentiment_drivers": ["average"]},
        "themes": {"themes": ["packaging"], "primary_theme": "packaging", "theme_evidence": {}},
        "priority_score": 3.5,
    },
]


class TestAggregateResults:
    def test_counts_sentiments(self):
        result = aggregate_results(SAMPLE_CLASSIFIED_REVIEWS)
        dist = result["sentiment_distribution"]
        assert dist["negative"]["count"] == 1
        assert dist["positive"]["count"] == 1
        assert dist["neutral"]["count"] == 1

    def test_calculates_percentages(self):
        result = aggregate_results(SAMPLE_CLASSIFIED_REVIEWS)
        dist = result["sentiment_distribution"]
        assert dist["negative"]["pct"] == pytest.approx(33.3, abs=0.1)

    def test_counts_theme_frequency(self):
        result = aggregate_results(SAMPLE_CLASSIFIED_REVIEWS)
        assert result["theme_frequency"]["delivery"] == 1
        assert result["theme_frequency"]["product_quality"] == 1

    def test_surfaces_high_priority_negatives(self):
        result = aggregate_results(SAMPLE_CLASSIFIED_REVIEWS)
        # r1 has priority_score 9.5 and is negative — should be surfaced
        high = result["high_priority_issues"]
        assert len(high) == 1
        assert high[0]["primary_theme"] == "delivery"

    def test_includes_review_count(self):
        result = aggregate_results(SAMPLE_CLASSIFIED_REVIEWS)
        assert result["review_count"] == 3


class TestUpdateHistory:
    def test_appends_snapshot(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            config = {**SAMPLE_CONFIG}
            config["memory"] = {"history_file": f.name, "max_snapshots": 5}

            aggregated = aggregate_results(SAMPLE_CLASSIFIED_REVIEWS)
            history = update_history(aggregated, config)

            assert len(history["snapshots"]) == 1
            assert history["snapshots"][0]["review_count"] == 3

    def test_enforces_max_snapshots(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            history_path = Path(tmpdir) / "history.json"
            config = {**SAMPLE_CONFIG}
            config["memory"] = {"history_file": str(history_path), "max_snapshots": 3}

            aggregated = aggregate_results(SAMPLE_CLASSIFIED_REVIEWS)

            # Run 5 times — should only keep last 3
            for _ in range(5):
                update_history(aggregated, config)

            history = json.loads(history_path.read_text())
            assert len(history["snapshots"]) == 3
