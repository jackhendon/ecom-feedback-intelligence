# Analysis Standards

## Sentiment Classification

### Labels and Definitions
- **positive**: Review expresses net satisfaction. Rating 4–5 with affirming language. Complaints, if present, are minor and do not undermine overall satisfaction.
- **neutral**: Mixed or indeterminate. Rating 3, or conflicting signals (e.g., loves product, hates delivery). No strong net valence.
- **negative**: Review expresses net dissatisfaction. Rating 1–2, or rating 3+ with strong complaint language.

### Confidence Score (0.0–1.0)
Assign confidence based on signal strength:
- **0.9–1.0**: Unambiguous — clear rating + matching language, no mixed signals
- **0.7–0.8**: Strong signal — rating aligns with language, minor nuance
- **0.5–0.6**: Moderate — rating and language partially conflict, or language is vague
- **0.3–0.4**: Weak — strong conflict between rating and language (e.g., 5-star but complains throughout)
- Never assign < 0.3 — if that uncertain, classify as neutral

### Sentiment Drivers
List 1–3 specific drivers for the assigned sentiment. Use noun phrases, not verbs.
Examples: "late delivery", "gold foil quality", "poor customer service response time", "packaging waste", "price increase"

Drivers must be grounded in the review text — do not infer beyond what is stated.

---

## Theme Classification

Apply the taxonomy from `.claude/rules/theme-taxonomy.md`. Rules:
- Assign 1–3 themes per review (never 0, never 4+)
- Primary theme first (most prominent)
- A theme must have explicit evidence in the review text — do not infer
- If a review genuinely touches only one theme, assign one
- Use exact theme slugs from the taxonomy (e.g., `delivery`, not `shipping`)

---

## Priority Scoring

Formula (deterministic — do not use LLM judgment for the number):

```
priority = (6 - rating) × sentiment_weight × confidence × recency_multiplier
```

Where:
- `sentiment_weight`: negative=2.0, neutral=1.0, positive=0.5 (from brand.yaml)
- `recency_multiplier`: reviews ≤ 7 days old = 1.2, 8–30 days = 1.0, > 30 days = 0.8
- Score range: 0 (5-star positive) to 12 (1-star negative, recent, high confidence)

**High priority threshold**: score ≥ 6.0

---

## PM Insights Quality Standards

Insights must be:
- **Specific**: Cite evidence ("14 reviews mention late December delivery", not "some customers complained")
- **Actionable**: Name a concrete next step or experiment
- **Scoped**: Opportunities and risks must be distinct — no overlap

### Opportunity Definition
An opportunity is a strength that can be amplified or a gap that can be addressed with reasonable effort.
Format: `[Theme] — [Observation] → [Recommended action] (Effort: Low/Med/High, Impact: Low/Med/High)`

### Risk Definition
A risk is a pattern that, if unaddressed, will drive churn or damage brand reputation.
Format: `[Theme] — [Pattern] → [Urgency: immediate/monitor/watch]`

### Experiments
Recommend 2–3 specific, testable experiments. Each must:
- State the hypothesis
- Name the metric to move
- Be completable in ≤ 8 weeks
