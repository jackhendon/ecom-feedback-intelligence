# Skill: classify-review

Deep-dive analysis of a single review. Useful for spot-checking, edge cases, or understanding how the classifier handles ambiguous reviews.

## Usage
```
/classify-review
```
After running the command, paste the review text (or provide rating + text). Claude will prompt if not given.

Optionally provide: `/classify-review rating=2 "The product was lovely but delivery was terrible"`

---

## Steps

### Step 1: Accept input
If the user hasn't provided a review, ask:
```
Paste the review text (include the star rating if you have it):
```

Parse:
- `rating`: integer 1–5 (if not provided, ask or infer from language)
- `text`: the review body
- `date`: optional (default to today if not provided — affects recency in priority score)

### Step 2: Classify

Apply `.claude/rules/analysis-standards.md` and `.claude/rules/theme-taxonomy.md`.

**Sentiment analysis:**
- Label + confidence + 1–3 drivers
- Explain the reasoning briefly (1–2 sentences)

**Theme classification:**
- 1–3 themes (primary first)
- For each theme: quote the specific phrase that justified inclusion

**Priority score:**
- Calculate using the formula from `.claude/rules/analysis-standards.md`
- Show the working: `(6 - rating) × weight × confidence × recency = score`

### Step 3: Output analysis card

```
REVIEW ANALYSIS
───────────────────────────────────────
Rating:    ★N
Text:      "[full review text]"

SENTIMENT: POSITIVE/NEUTRAL/NEGATIVE (confidence: 0.X)
  Drivers: driver1, driver2

THEMES
  Primary:   theme_slug — "[quoted evidence]"
  Secondary: theme_slug — "[quoted evidence]"

PRIORITY SCORE: N.N / 12.0
  Working: (6 - N) × N.N × N.N × N.N = N.N
  Threshold: [HIGH PRIORITY ≥ 6.0 | below threshold]

PM NOTE
  [One sentence: what a PM should do with this review, if anything]
───────────────────────────────────────
```

### Step 4: Offer follow-up
```
Run /analyze-reviews to process all reviews. Run /classify-review again to analyse another.
```
