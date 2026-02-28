# Skill: compare-periods

Reads `memory/history.json` and compares trends across stored snapshots. No new classification — pure analysis of historical data.

## Usage
```
/compare-periods
/compare-periods 4        # compare last 4 snapshots
/compare-periods all      # compare all snapshots in history
```

Default: compare last 4 snapshots (or all if fewer than 4 exist).

---

## Steps

### Step 1: Load history
Read `memory/history.json`. Extract the snapshots array.

If fewer than 2 snapshots exist:
```
Not enough history to compare periods.
Snapshots found: N
Run /analyze-reviews at least twice to build history.
```
And stop.

### Step 2: Select snapshots
Apply the count argument (default 4). Use the most recent N snapshots, ordered chronologically.

### Step 3: Compute trends

For each metric, show direction of change across the selected window:

**Sentiment trend:**
- Positive %: is it rising, falling, or flat (< 2pp change = flat)?
- Negative %: same
- Net sentiment score: positive% - negative% per period

**Theme trends:**
- Rank each theme by frequency per period
- Identify: themes rising in rank, themes falling in rank, themes newly appearing, themes disappearing
- Flag any theme that has increased by > 5 mentions period-over-period as "accelerating"

**Priority trends:**
- Average priority score per period
- Count of high-priority issues (≥ 6.0) per period
- Any themes consistently generating high-priority issues

**Review volume:**
- Review count per period (context: is volume increasing/decreasing?)

### Step 4: Output trend report

Compute all values directly from the JSON data — no estimation.

```
TREND ANALYSIS — [earliest period] to [latest period]
N snapshots | N total reviews

SENTIMENT TREND
  Period    | Positive | Neutral | Negative | Net
  ──────────────────────────────────────────────
  YYYY-WNN  |   N%    |   N%   |    N%    |  ±N

THEME MOVEMENT
  Rising:       [theme] (↑ N), ...
  Falling:      [theme] (↓ N), ...
  Stable:       [themes with < 2 mention change]
  Accelerating: [any theme up > 5 mentions period-over-period]

PRIORITY TRENDS
  Avg score:         N → N → N
  High-priority count: N → N → N

KEY SIGNALS
  • [signal 1]
  • [signal 2]
  • [signal 3]
```

### Step 5: PM recommendation
```
RECOMMENDED ACTION
[One specific, evidence-based recommendation derived from the trend data]
```
