"""
TrustPilot connector with mock mode for development and portfolio demo.

Mock mode (default): reads from data/examples/trustpilot_sample.json
Real API mode: see implementation notes below

To connect to the real TrustPilot API:
1. Set mock_mode: false in config/brand.yaml
2. Register at https://support.trustpilot.com/hc/en-us/articles/201178023 for API access
3. Add TRUSTPILOT_API_KEY and TRUSTPILOT_BUSINESS_UNIT_ID to your .env file
4. Implement _fetch_from_api() below using the Consumer API v1
"""
import json
import os
from datetime import datetime
from pathlib import Path


class TrustPilotConnector:
    def __init__(self, config: dict):
        self.config = config["review_sources"]["trustpilot"]
        self.mock_mode = self.config.get("mock_mode", True)

    def fetch(self) -> list[dict]:
        """Fetch reviews and return as normalised internal schema."""
        if self.mock_mode:
            return self._fetch_from_file()
        return self._fetch_from_api()

    def _fetch_from_file(self) -> list[dict]:
        path = Path(self.config["sample_file"])
        raw = json.loads(path.read_text())
        return [self._normalise(r) for r in raw["reviews"]]

    def _normalise(self, raw: dict) -> dict:
        """
        Transform source format to internal review schema.
        All downstream code depends on this shape — do not change field names.
        """
        return {
            "review_id": raw.get("id", f"mock_{raw.get('author', 'unknown')}"),
            "source": "trustpilot",
            "rating": int(raw["rating"]),
            "text": raw["text"],
            "date": raw.get("date", datetime.now().strftime("%Y-%m-%d")),
            "author": raw.get("author", "Anonymous"),
            # Filled by skills in orchestrator
            "sentiment": None,
            "themes": None,
            "priority_score": None,
        }

    def _fetch_from_api(self) -> list[dict]:
        """
        Real TrustPilot API implementation (not yet built).

        When implementing:
        - Use the TrustPilot Consumer API v1
        - Endpoint: GET /v1/business-units/{businessUnitId}/reviews
        - Auth: Bearer token from TRUSTPILOT_API_KEY env var
        - Paginate with ?page=N&perPage=100
        - Filter with ?stars=1,2 for negative-first triage
        - Map API response fields to _normalise() schema

        Example response fields to map:
          raw["id"] -> review_id
          raw["stars"] -> rating
          raw["text"]["review"] -> text
          raw["createdAt"][:10] -> date
          raw["consumer"]["displayName"] -> author
        """
        raise NotImplementedError(
            "Real TrustPilot API not implemented. "
            "Set mock_mode: true in config/brand.yaml to use sample data, "
            "or implement this method. See module docstring for API details."
        )
