# Skill: analyze-reviews

Full pipeline analysis of customer reviews. Run this to process reviews, generate PM insights, and update history.

## Usage
```
/analyze-reviews
/analyze-reviews data/examples/trustpilot_sample.json
/analyze-reviews [path/to/reviews.json]
```

If no file path is given, default to the path in `config/brand.yaml` → `review_sources.trustpilot.sample_file`.

---

## Steps

### Step 1: Load configuration
Read `config/brand.yaml`. Extract:
- `brand.name`
- `themes` list (these are the only valid theme slugs)
- `sentiment.weights` (negative, neutral, positive)
- `reporting.output_dir`
- `memory.history_file`
- `memory.max_snapshots`

### Step 2: Load reviews
Read the JSON file. Validate it has a `reviews` array. Report total count.

If the file doesn't exist or has no reviews, stop and tell the user.

### Step 3: Classify reviews (batches of 10)
For each review, determine:

**Sentiment:**
- Label: `positive`, `neutral`, or `negative`
- Confidence: 0.0–1.0
- Drivers: 1–3 noun phrases grounded in review text

**Themes:**
- 1–3 themes from the taxonomy in `.claude/rules/theme-taxonomy.md`
- Use exact slugs only
- Primary theme first

Apply standards from `.claude/rules/analysis-standards.md`.

Process in batches of 10. After each batch, output a progress line:
```
Classified reviews 1–10 of 50...
Classified reviews 11–20 of 50...
```

### Step 4: Score priority
For each review, calculate (deterministic formula — do not use judgment):
```
recency_multiplier = 1.2 if days_since_review ≤ 7 else (1.0 if days_since_review ≤ 30 else 0.8)
sentiment_weight = weights[sentiment_label]
priority = (6 - rating) × sentiment_weight × confidence × recency_multiplier
```
Today's date for recency: use the current date.
Clamp to 0 if result is negative (5-star positive reviews can go slightly negative due to formula — floor at 0).

### Step 5: Aggregate
Calculate:
- Sentiment distribution: count and % for each label
- Theme frequency: for each theme slug, count total mentions, primary mentions, secondary+ mentions
- High-priority issues: all reviews with priority ≥ 6.0, sorted by priority descending

### Step 6: Generate PM insights
Produce:

**Executive summary** (2–3 sentences): net sentiment, dominant theme, most urgent signal.

**Top 3 opportunities**: Use format from `.claude/rules/analysis-standards.md`. Must be distinct, evidence-backed, actionable.

**Top 3 risks**: Patterns that could drive churn or reputation damage. Include urgency level.

**Recommended experiments**: 2–3 specific, testable experiments with hypothesis and metric.

### Step 7: Update history
Read `memory/history.json`. Append a new snapshot:
```json
{
  "period": "YYYY-WNN",
  "run_date": "YYYY-MM-DD",
  "review_count": N,
  "sentiment_distribution": {
    "positive": {"count": N, "pct": N.N},
    "neutral": {"count": N, "pct": N.N},
    "negative": {"count": N, "pct": N.N}
  },
  "theme_frequency": {
    "theme_slug": N
  },
  "high_priority_issues": [
    {"id": "synth_XXX", "rating": N, "priority": N.N, "primary_theme": "slug"}
  ],
  "avg_priority_score": N.N
}
```

Keep only the last `max_snapshots` (12) snapshots. Write back to `memory/history.json`.

### Step 8: Present results
Output the inline summary format from `.claude/rules/report-format.md`.

End with:
```
History updated: memory/history.json (N snapshots)
Run /generate-report to save full report.
Run /compare-periods to see trend analysis.
```
