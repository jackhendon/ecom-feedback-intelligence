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
Use the full report template from `.claude/rules/report-format.md`.

Populate all sections with data from the analysis. For the "Trend vs Previous Period" section:
- Read `memory/history.json`
- If 2+ snapshots exist, compare the most recent two: sentiment shift (pp change), theme movement (rank changes), avg priority score delta
- If only 1 snapshot, write: "Insufficient history for trend comparison. Run again next week to begin tracking trends."

### Step 4: Confirm
```
Report saved: outputs/reports/{brand.name.lower()}_YYYY-WNN.md
[N lines | ~N words]
```
