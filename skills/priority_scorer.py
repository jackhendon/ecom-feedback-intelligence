"""
Priority scorer — deterministic, no LLM.

Design choice: not every step needs AI. Priority scoring is a formula:
  score = base_score × sentiment_weight × confidence × recency_multiplier

This is cheaper, faster, and more predictable than an LLM for this task.
It also means the prioritisation logic is transparent and auditable.

Score interpretation:
  > 8.0  — High priority: negative, recent, confident classification
  5.0-8.0 — Medium priority: monitor, address in next sprint
  < 5.0  — Low priority: positive/neutral or older reviews
"""
from datetime import datetime


def score_reviews(reviews: list[dict], config: dict) -> list[dict]:
    """
    Add priority_score to each review in-place.

    Args:
        reviews: List of review dicts (must have sentiment and date populated)
        config: Brand config dict (uses config['sentiment']['weights'])

    Returns:
        Same list with priority_score field populated on each review
    """
    weights = config["sentiment"]["weights"]
    for review in reviews:
        review["priority_score"] = _compute_score(review, weights)
    return reviews


def _compute_score(review: dict, weights: dict) -> float:
    """
    Compute priority score for a single review.

    Base score inverts the star rating so 1-star = 10.0, 5-star = 2.0.
    Multiplied by sentiment weight, confidence, and recency.
    """
    sentiment = review["sentiment"]["sentiment"]
    confidence = review["sentiment"]["confidence"]
    rating = review["rating"]

    # Invert rating: 1-star is highest urgency
    base = (6 - rating) * 2.0  # range: 2.0 (5-star) to 10.0 (1-star)

    sentiment_weight = weights.get(sentiment, 1.0)

    # Recency multiplier: more recent = higher priority
    try:
        review_date = datetime.strptime(review["date"], "%Y-%m-%d")
        days_old = (datetime.now() - review_date).days
    except (ValueError, TypeError):
        days_old = 99  # treat malformed dates as older

    if days_old <= 7:
        recency = 1.3
    elif days_old <= 30:
        recency = 1.1
    else:
        recency = 1.0

    return round(base * sentiment_weight * confidence * recency, 2)
