# ecom-feedback-intelligence

Customer review intelligence pipeline for Papier. Analyses TrustPilot reviews, classifies sentiment and themes, scores priority, and generates PM insights.

## Architecture

This project runs entirely within Claude Code — no Python, no API keys, no dependencies. The skill files are the pipeline.

```
config/brand.yaml                    ← Brand config, theme taxonomy, weights
data/examples/trustpilot_sample.json ← Synthetic review data (50 reviews)
memory/history.json                  ← Rolling history (max 12 snapshots)
outputs/reports/                     ← Generated markdown reports
.claude/skills/                      ← Slash command implementations
.claude/rules/                       ← Analysis standards and conventions
```

## Slash Commands

| Command | What it does |
|---------|-------------|
| `/analyze-reviews` | Full pipeline: read → classify → score → aggregate → insights → update history |
| `/classify-review` | Deep-dive on a single review — paste text, get analysis card |
| `/generate-report` | Write dated markdown report to `outputs/reports/` |
| `/compare-periods` | Trend analysis across stored history snapshots |

## Rules (always apply)

- Theme slugs: use only those defined in `.claude/rules/theme-taxonomy.md`
- Sentiment standards: follow `.claude/rules/analysis-standards.md` exactly
- Report format: follow `.claude/rules/report-format.md` for all output
- Priority formula is deterministic — calculate it, do not estimate
- Insights must cite evidence counts — never vague language like "some customers"
- Data is synthetic — do not treat it as real customer PII

## Configuration

Edit `config/brand.yaml` to:
- Change the brand name (to use with a different eCommerce brand)
- Update the theme taxonomy
- Adjust sentiment weights
- Toggle reporting options

## Data

`data/examples/trustpilot_sample.json` contains 50 synthetic reviews. All names and scenarios are fictional. Do not commit real customer data to this repo.

To use real TrustPilot data: replace the contents of the sample file with real reviews in the same JSON schema (`id`, `rating`, `author`, `date`, `text`).
