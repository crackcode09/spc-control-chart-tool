# Process Inferences — Design Spec
**Date:** 2026-04-28
**Status:** Approved

---

## Overview

Add a plain-English inferences section to the SPC Control Chart Tool that interprets the calculated statistics for the user. The inferences appear in two forms: a colored bullet list (scannable, rule-based) and a narrative paragraph (plain-English synthesis). Both appear in the Streamlit app and in the PDF report.

---

## Inference Rules

Five rules are evaluated in order. Each rule produces one bullet with an icon (✅ / ⚠️ / ❌ / ℹ️) and a plain-English statement.

### Rule 1 — Capability (Cpk)

| Condition | Icon | Text |
|---|---|---|
| Cpk ≥ 1.33 | ✅ | Process is capable — Cpk = {value} meets the 1.33 benchmark |
| 1.0 ≤ Cpk < 1.33 | ⚠️ | Process is marginally capable — Cpk = {value} (target ≥ 1.33) |
| Cpk < 1.0 | ❌ | Process is not capable — Cpk = {value}, defects are likely |
| Cpk is None | ℹ️ | Capability could not be calculated — check spec limits |

### Rule 2 — Centering (Cp vs Cpk)

Only evaluated when both Cp and Cpk are available.

| Condition | Icon | Text |
|---|---|---|
| Cp − Cpk > 0.10 | ⚠️ | Process is off-center — Cp ({Cp}) is notably higher than Cpk ({Cpk}), mean is shifted toward one spec limit |
| Cp − Cpk ≤ 0.10 | ✅ | Process is well-centered within spec limits |
| Cp or Cpk is None | ℹ️ | Centering could not be assessed — spec limits required |

### Rule 3 — Stability (out-of-control points)

Count xbar values outside [LCL_xbar, UCL_xbar].

| Condition | Icon | Text |
|---|---|---|
| 0 out-of-control points | ✅ | Process is stable — no points outside control limits |
| 1–2 out-of-control points | ⚠️ | {n} point(s) outside control limits — investigate for assignable causes |
| 3+ out-of-control points | ❌ | {n} points outside control limits — process is unstable |

### Rule 4 — Long-term Drift (Cpk vs Ppk)

Only evaluated when both Cpk and Ppk are available.

| Condition | Icon | Text |
|---|---|---|
| Cpk − Ppk > 0.15 | ⚠️ | Long-term performance (Ppk = {Ppk}) is notably worse than short-term (Cpk = {Cpk}) — process may have drifted over time |
| Cpk − Ppk ≤ 0.15 | ✅ | Short-term and long-term performance are consistent |
| Either is None | ℹ️ | Long-term drift could not be assessed |

### Rule 5 — Narrative Paragraph

A single plain-English paragraph synthesizing Rules 1–4. Built by joining rule outcomes into a coherent sentence structure. Example:

> "This process is capable with a Cpk of 1.45, meeting the 1.33 benchmark, and is well-centered within spec limits. The control chart shows 2 points outside the control limits, suggesting occasional instability that should be investigated. Short-term and long-term performance are consistent (Cpk 1.45 vs Ppk 1.41)."

The narrative is constructed programmatically from the same rule outputs — not hardcoded templates per combination.

---

## Architecture

### New file: `spc_inferences.py`

Single public function:

```python
def generate_inferences(stats: dict, cap: dict, USL: float, LSL: float) -> dict:
    """
    Returns:
        {
            "bullets": [{"icon": str, "text": str}, ...],  # 4 items
            "narrative": str
        }
    """
```

- Pure Python — no Streamlit, no matplotlib, no fpdf2 dependency
- Takes the same `stats` and `cap` dicts already computed in `app.py`
- Returns a structured dict consumed by both `app.py` (display) and `report_utils.py` (PDF)
- Handles all None values gracefully — no rule ever raises an exception

### `app.py` changes

Between the stats metrics divider and the chart (`st.pyplot(fig)`), insert:

```python
st.caption("PROCESS INFERENCES")
for b in inferences["bullets"]:
    st.markdown(f"{b['icon']} {b['text']}")
st.info(inferences["narrative"])
st.divider()
```

Import: `from spc_inferences import generate_inferences`

Call site: `inferences = generate_inferences(stats, cap, USL, LSL)` — after `cap` is computed, before the chart block.

### `report_utils.py` changes

`build_pdf()` receives `inferences` as a new parameter:

```python
def build_pdf(fig, stats, cap, column, chart_type, subgroup_size, USL, LSL, values, inferences):
```

New section added after the stats table in the PDF:

1. Bold "Process Inferences" section heading
2. Each bullet on its own line: icon + text (8pt)
3. Narrative paragraph in a light grey shaded box (fill color `#F0F0F0`)

The `build_pdf` call in `app.py` is updated to pass `inferences`.

---

## Narrative Construction

The narrative is built by concatenating sentence fragments from each rule result. Each rule contributes one clause:

- Rule 1 (capability): "This process is capable with a Cpk of X" / "This process is not capable (Cpk = X)"
- Rule 2 (centering): "and is well-centered" / "but the mean is shifted off-center (Cp = X vs Cpk = Y)"
- Rule 3 (stability): "No out-of-control points were detected" / "X point(s) outside control limits suggest instability"
- Rule 4 (drift): "Short and long-term performance are consistent" / "Long-term performance (Ppk = X) is notably worse than short-term (Cpk = Y)"

The function assembles these into a single paragraph ending with a period.

---

## Error Handling

- Any `None` cap value triggers the ℹ️ neutral bullet for that rule — no exception is raised
- If `stats["xbar"]` is empty, Rule 3 returns ℹ️ "Stability could not be assessed"
- `generate_inferences` never raises — all edge cases return ℹ️ bullets

---

## Testing

New file: `tests/test_spc_inferences.py`

Tests cover:
- Capable process (Cpk ≥ 1.33) returns ✅ bullet for Rule 1
- Marginal process (1.0 ≤ Cpk < 1.33) returns ⚠️
- Not capable (Cpk < 1.0) returns ❌
- Off-center process (Cp − Cpk > 0.10) returns ⚠️ for Rule 2
- 0 out-of-control points returns ✅ for Rule 3
- 3+ out-of-control points returns ❌ for Rule 3
- Long-term drift (Cpk − Ppk > 0.15) returns ⚠️ for Rule 4
- All-None cap dict returns all ℹ️ bullets without raising
- `generate_inferences` always returns a non-empty narrative string

---

## Files Created / Modified

| File | Change |
|---|---|
| `spc_inferences.py` | NEW — inference logic |
| `tests/test_spc_inferences.py` | NEW — tests |
| `app.py` | Add inferences display between stats and chart |
| `report_utils.py` | Add inferences section to PDF, update `build_pdf` signature |

---

## Out of Scope

- Western Electric / Nelson rules (run rules beyond simple UCL/LCL exceedance)
- Histogram or normality testing
- Trend detection (8 consecutive points above/below centerline)
- Recommended corrective actions
