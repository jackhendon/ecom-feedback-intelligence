"""
Tests for the theme extractor skill.

Verifies that:
1. build_theme_tool() correctly injects brand themes into the enum constraint
2. extract_themes() returns the expected schema
3. The tool_use pattern is used correctly
"""
from unittest.mock import MagicMock
import pytest

from skills.theme_extractor import extract_themes, build_theme_tool, _BASE_THEME_TOOL


SAMPLE_THEMES = ["packaging", "personalisation", "delivery", "product_quality", "website_ux"]


def _make_mock_client(themes: list[str], primary: str, evidence: dict):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = {
        "themes": themes,
        "primary_theme": primary,
        "theme_evidence": evidence,
    }
    mock_response = MagicMock()
    mock_response.content = [tool_block]

    client = MagicMock()
    client.messages.create.return_value = mock_response
    return client


class TestBuildThemeTool:
    def test_injects_valid_themes_into_enum(self):
        tool = build_theme_tool(SAMPLE_THEMES)
        items_enum = tool["input_schema"]["properties"]["themes"]["items"]["enum"]
        primary_enum = tool["input_schema"]["properties"]["primary_theme"]["enum"]

        assert items_enum == SAMPLE_THEMES
        assert primary_enum == SAMPLE_THEMES

    def test_does_not_mutate_base_tool(self):
        original_enum = _BASE_THEME_TOOL["input_schema"]["properties"]["themes"]["items"]["enum"][:]
        build_theme_tool(SAMPLE_THEMES)
        after_enum = _BASE_THEME_TOOL["input_schema"]["properties"]["themes"]["items"]["enum"]
        assert after_enum == original_enum

    def test_tool_name_is_extract_themes(self):
        tool = build_theme_tool(SAMPLE_THEMES)
        assert tool["name"] == "extract_themes"


class TestExtractThemes:
    def test_returns_expected_schema(self):
        client = _make_mock_client(
            ["delivery", "customer_service"],
            "delivery",
            {"delivery": "arrived two weeks late", "customer_service": "no response"},
        )
        theme_tool = build_theme_tool(SAMPLE_THEMES)
        review = {"rating": 1, "text": "Arrived two weeks late, no response from support."}

        result = extract_themes(review, theme_tool, client)

        assert result["primary_theme"] == "delivery"
        assert "delivery" in result["themes"]
        assert isinstance(result["theme_evidence"], dict)

    def test_calls_correct_model(self):
        client = _make_mock_client(["packaging"], "packaging", {})
        theme_tool = build_theme_tool(SAMPLE_THEMES)
        review = {"rating": 4, "text": "Beautiful packaging."}

        extract_themes(review, theme_tool, client)

        call_kwargs = client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-haiku-4-5"

    def test_forces_tool_choice(self):
        client = _make_mock_client(["packaging"], "packaging", {})
        theme_tool = build_theme_tool(SAMPLE_THEMES)
        review = {"rating": 4, "text": "Beautiful packaging."}

        extract_themes(review, theme_tool, client)

        call_kwargs = client.messages.create.call_args[1]
        assert call_kwargs["tool_choice"] == {
            "type": "tool",
            "name": "extract_themes",
        }
