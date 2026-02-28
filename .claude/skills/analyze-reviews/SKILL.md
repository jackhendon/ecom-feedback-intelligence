# Skill: analyze-reviews

Full pipeline analysis of customer reviews. Parallel classification via subagents — fast and token-efficient.

## Usage
```
/analyze-reviews
/analyze-reviews data/examples/trustpilot_sample.json
```

If no file path is given, default to the path in `config/brand.yaml` → `review_sources.trustpilot.sample_file`.

---

## Steps

### Step 1: Load configuration
Read `config/brand.yaml`. Extract:
- `brand.name`
- `themes` list (valid slugs)
- `sentiment.weights` (negative, neutral, positive)
- `reporting.output_dir`
- `memory.history_file`
- `memory.max_snapshots`

### Step 2: Load reviews
Read the JSON file. Validate it has a `reviews` array. Report total count.
If the file doesn't exist or has no reviews, stop and tell the user.

### Step 3: Classify reviews — parallel subagents

First, calculate chunk size and agent count based on total reviews (N):

| Reviews | Chunk size | Agents |
|---------|-----------|--------|
| 1–20    | N (single agent) | 1 |
| 21–100  | 20 | ceil(N/20) |
| 101–300 | 30 | ceil(N/30) |
| 300+    | 40 | ceil(N/40) |

Split the reviews array into evenly-sized chunks. The last chunk may be smaller.

**CRITICAL: Make all Agent tool calls in a single response to run them in parallel.** Do not wait for one to finish before starting the next — issue all calls simultaneously. Each call: subagent_type=general-purpose, model=haiku, foreground.

Each subagent receives this exact prompt (substitute the actual reviews JSON and valid theme slugs):

---
**Subagent prompt:**

Classify each review below. Return ONLY a JSON array — no explanation, no markdown, no other text.

Valid theme slugs (use only these): `packaging`, `personalisation`, `delivery`, `product_quality`, `website_ux`, `customer_service`, `pricing`, `gifting_experience`

Sentiment weights for reference: negative=2.0, neutral=1.0, positive=0.5

For each review output one object:
```json
{"id":"<id>","r":<rating>,"s":"<pos|neu|neg>","c":<confidence 0.0-1.0>,"t":["<primary_theme>","<optional_secondary>"],"date":"<YYYY-MM-DD>"}
```

Rules:
- `s`: positive = net satisfied (rating 4-5, affirming language); negative = net dissatisfied (rating 1-2, or strong complaint); neutral = mixed/indeterminate
- `c`: 0.9-1.0 unambiguous; 0.7-0.8 strong signal; 0.5-0.6 mixed; 0.3-0.4 conflicting rating vs language
- `t`: 1-3 slugs only, primary theme first, must have explicit evidence in text
- Do not infer themes beyond what is stated

Reviews to classify:
[INSERT REVIEWS JSON ARRAY HERE]
---

Once all agents have returned, merge their JSON arrays into a single flat list.

### Step 4: Score priority
For each classified review, calculate (deterministic — no LLM):
```
today = current date
days_old = (today - review date) in days
recency = 1.2 if days_old ≤ 7 else (1.0 if days_old ≤ 30 else 0.8)
weight = sentiment_weights[s]  # from brand.yaml
priority = max(0, (6 - r) × weight × c × recency)
```

### Step 5: Aggregate
- Sentiment distribution: count and % for pos/neu/neg
- Theme frequency: for each slug, total mentions (primary + secondary)
- High-priority issues: all reviews with priority ≥ 6.0, sorted descending
- avg_priority_score: mean of all priority scores

### Step 6: Generate PM insights
Using the aggregated data, produce:

**Executive summary** (2–3 sentences): net sentiment, dominant theme, most urgent signal.

**Top 3 opportunities**: distinct, evidence-backed, actionable. Format:
`[Theme] — [Observation with count] → [Action] (Effort: X, Impact: X)`

**Top 3 risks**: patterns threatening churn or reputation. Include urgency (immediate/monitor/watch).

**Recommended experiments**: 2–3 with hypothesis and metric.

Apply standards from `.claude/rules/analysis-standards.md`.

### Step 7: Update history
Read `memory/history.json`. Append snapshot:
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
  "theme_frequency": {"slug": N},
  "high_priority_issues": [{"id": "...", "rating": N, "priority": N.N, "primary_theme": "slug"}],
  "avg_priority_score": N.N
}
```
Keep only last `max_snapshots` entries. Write back to `memory/history.json`.

### Step 8: Present results
Output the inline summary format from `.claude/rules/report-format.md`.

End with:
```
History updated: memory/history.json (N snapshots)
Run /generate-report to save full report.
Run /compare-periods to see trend analysis.
```
