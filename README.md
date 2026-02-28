# ecom-feedback-intelligence

Open-source Claude Code skills for turning eCommerce customer reviews into structured PM insights. Configurable for any brand via a single YAML file.

Includes sample data for a stationery brand. Swap `config/brand.yaml` and your review data to use it with your own.

---

## What it does

Reads customer reviews, classifies sentiment and themes, scores issues by priority, and generates PM-ready recommendations. Runs entirely within Claude Code — no API keys, no dependencies, no install.

Works with two data sources:
- **TrustPilot API** — connect your API key to pull reviews directly
- **Local spreadsheet/JSON** — export reviews manually and drop them in `data/examples/`

---

## Slash Commands

| Command | What it does |
|---------|-------------|
| `/analyze-reviews` | Full pipeline: classify reviews → score priority → aggregate → PM insights → update history |
| `/classify-review` | Single-review deep-dive — paste text, get an analysis card |
| `/generate-report` | Write a dated markdown report to `outputs/reports/` |
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

## Configuring for your brand

1. Edit `config/brand.yaml`:
   - Set `brand.name`
   - Replace `themes` with your taxonomy (8 slugs recommended)
   - Adjust `sentiment.weights` if needed

2. Replace `data/examples/trustpilot_sample.json` with your reviews:
   ```json
   {"reviews": [{"id": "...", "rating": 4, "author": "...", "date": "YYYY-MM-DD", "text": "..."}]}
   ```

3. Run `/analyze-reviews`.

---

All data in this repository is **synthetic**. No real customer data is included or should be committed.
