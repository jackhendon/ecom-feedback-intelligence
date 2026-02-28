# ecom-feedback-intelligence

Customer review intelligence pipeline for Papier. Analyses TrustPilot reviews, classifies sentiment and themes, scores priority, and generates PM insights.

Built as a portfolio project demonstrating a specific architectural insight: **when you already pay for Claude Code, the Python glue code is the wrong layer of abstraction**.

---

## Architecture

This project runs entirely within Claude Code — no Python, no API keys, no pip install.

```
/analyze-reviews  →  reads reviews  →  classifies sentiment + themes
                  →  scores priority (deterministic formula)
                  →  aggregates + generates PM insights
                  →  updates memory/history.json
                  →  offers /generate-report
```

The skill files are the pipeline. The rules files are the prompt engineering.

```
config/brand.yaml                    ← Brand config, theme taxonomy, weights
data/examples/trustpilot_sample.json ← Synthetic review data (50 reviews)
memory/history.json                  ← Rolling history (max 12 snapshots)
outputs/reports/                     ← Generated markdown reports
.claude/skills/                      ← Slash command implementations
.claude/rules/                       ← Analysis standards and constraints
CLAUDE.md                            ← Project instructions (auto-loaded)
```

---

## Slash Commands

| Command | What it does |
|---------|-------------|
| `/analyze-reviews` | Full pipeline: ingest → classify → score → aggregate → insights → history |
| `/classify-review` | Single-review deep-dive — paste text, get analysis card |
| `/generate-report` | Write dated markdown report to `outputs/reports/` |
| `/compare-periods` | Trend analysis across stored history snapshots |

---

## Quickstart

```bash
git clone https://github.com/jackhendon/ecom-feedback-intelligence
cd ecom-feedback-intelligence
# Open in Claude Code — no install needed
/analyze-reviews
```

---

## Design decisions

### Instructions as code

The entire pipeline is implemented as Claude Code skill files and rules. The Python version of this project was ~800 lines across 8 files. The Claude Code version is 8 markdown files.

| Aspect | Python API version | Claude Code native |
|--------|-------------------|-------------------|
| Runtime | Python + pip + venv | Claude Code (already installed) |
| API auth | ANTHROPIC_API_KEY | Included with subscription |
| Orchestration | 100+ lines Python | `analyze-reviews/SKILL.md` |
| Structured output | `tool_use` + schema | Rule files with examples |
| Dependencies | anthropic, pyyaml, pytest, requests | None |
| Testing | pytest + mocks | Run the skill, inspect output |

The craft shifted from Python engineering to prompt engineering: constrained theme taxonomy, evidence-based insight standards, deterministic priority formula, structured report conventions. The question this project answers is *when do you need code and when don't you*.

### Constrained theme taxonomy

The 8 theme slugs in `config/brand.yaml` are the only valid themes. The taxonomy rule file defines exactly what evidence justifies each theme and what is excluded. This prevents theme drift and ensures consistent classification across runs.

### Deterministic priority scoring

Priority scoring uses a formula — no LLM judgment:

```
priority = (6 - rating) × sentiment_weight × confidence × recency_multiplier
```

Where sentiment weights come from `brand.yaml` (negative=2.0, neutral=1.0, positive=0.5) and recency is tiered (≤7 days: 1.2×, ≤30 days: 1.0×, older: 0.8×). High priority threshold: ≥ 6.0.

Not every step needs AI. Deterministic logic is cheaper, faster, and its reasoning is auditable.

### Rolling history

`memory/history.json` stores the last 12 weekly snapshots. `/compare-periods` reads this to identify trends: sentiment trajectory, theme rank movement, priority score acceleration. The PM insight this enables (e.g. "delivery complaints have risen 3 periods in a row") is more valuable than any single-period analysis.

### Config-driven brand abstraction

Swapping `config/brand.yaml` adapts the entire pipeline to a new eCommerce brand — different theme taxonomy, different weights, different brand name in reports. Designed to be portable.

---

## Adapting for your brand

1. Edit `config/brand.yaml`:
   - Set `brand.name`
   - Replace `themes` with your taxonomy (8 slugs recommended)
   - Adjust `sentiment.weights` if urgency priorities differ

2. Replace `data/examples/trustpilot_sample.json` with your reviews in the same schema:
   ```json
   {"reviews": [{"id": "...", "rating": 4, "author": "...", "date": "YYYY-MM-DD", "text": "..."}]}
   ```

3. Run `/analyze-reviews`.

---

## About

Built by [Jack Hendon](https://github.com/jackhendon), Senior Product Manager at Papier.

All data in this repository is **synthetic**. No real customer data is included or should be committed.
