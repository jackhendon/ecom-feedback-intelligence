"""
Tests for the sentiment classifier skill.

These tests use unittest.mock to avoid making real API calls.
Run with: python -m pytest tests/ -v
"""
from unittest.mock import MagicMock, patch
import pytest

from skills.sentiment_classifier import classify_sentiment, SENTIMENT_TOOL


def _make_mock_client(sentiment: str, confidence: float, drivers: list[str]):
    """Helper: returns a mock Anthropic client that returns a given tool_use response."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = {
        "sentiment": sentiment,
        "confidence": confidence,
        "sentiment_drivers": drivers,
    }
    mock_response = MagicMock()
    mock_response.content = [tool_block]

    client = MagicMock()
    client.messages.create.return_value = mock_response
    return client


class TestClassifySentiment:
    def test_returns_expected_schema(self):
        client = _make_mock_client("negative", 0.92, ["arrived late", "no communication"])
        review = {"rating": 1, "text": "Terrible experience, arrived very late."}

        result = classify_sentiment(review, client)

        assert result["sentiment"] == "negative"
        assert result["confidence"] == 0.92
        assert "arrived late" in result["sentiment_drivers"]

    def test_positive_review_passthrough(self):
        client = _make_mock_client("positive", 0.95, ["beautiful product"])
        review = {"rating": 5, "text": "Absolutely beautiful, perfect gift."}

        result = classify_sentiment(review, client)
        assert result["sentiment"] == "positive"

    def test_calls_correct_model(self):
        client = _make_mock_client("neutral", 0.6, [])
        review = {"rating": 3, "text": "Average experience."}

        classify_sentiment(review, client)

        call_kwargs = client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-haiku-4-5"

    def test_forces_tool_choice(self):
        client = _make_mock_client("neutral", 0.6, [])
        review = {"rating": 3, "text": "Average experience."}

        classify_sentiment(review, client)

        call_kwargs = client.messages.create.call_args[1]
        assert call_kwargs["tool_choice"] == {
            "type": "tool",
            "name": "classify_sentiment",
        }

    def test_sentiment_tool_schema_has_required_fields(self):
        required = SENTIMENT_TOOL["input_schema"]["required"]
        assert "sentiment" in required
        assert "confidence" in required
        assert "sentiment_drivers" in required

    def test_sentiment_enum_values(self):
        enum_values = SENTIMENT_TOOL["input_schema"]["properties"]["sentiment"]["enum"]
        assert set(enum_values) == {"positive", "neutral", "negative"}
