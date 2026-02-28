# Skill: generate-report

Writes a full markdown report to `outputs/reports/`. Requires `/analyze-reviews` to have been run first in this session (results are in context).

## Usage
```
/generate-report
```

---

## Steps

### Step 1: Check for analysis results
Look in the current conversation context for results from `/analyze-reviews`. The report needs:
- Sentiment distribution
- Theme frequency
- High-priority issues
- PM insights (opportunities, risks, experiments)
- Review count and run date

If no analysis results are in context, output:
```
No analysis results found. Run /analyze-reviews first, then /generate-report.
```
And stop.

### Step 2: Determine filename
Format: `{brand.name.lower()}_YYYY-WNN.md` where YYYY-WNN is the ISO week of the run date (brand name from `config/brand.yaml`).
Path: `outputs/reports/{brand.name.lower()}_YYYY-WNN.md`

If a file with that name already exists, append `-v2`, `-v3` etc.

### Step 3: Write the report
Use the template from `.claude/rules/report-format.md`. Write the file in a single pass — do not output to terminal first.

For the "Trend vs Previous Period" section, read `memory/history.json` and compute directly from the two most recent snapshots:
- Sentiment: pp change in positive% and negative%
- Themes: rank order each period by frequency, list themes that moved up or down
- Priority: avg_priority_score delta, high_priority_issues count delta

If fewer than 2 snapshots: write "Insufficient history for trend comparison. Run again next week."

### Step 4: Confirm
```
Report saved: outputs/reports/{brand.name.lower()}_YYYY-WNN.md
```
