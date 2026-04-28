# Process Inferences Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a plain-English inferences section to the SPC tool that applies 4 rule-based checks to the computed statistics and displays the results as a colored bullet list + narrative paragraph in both the Streamlit app and the PDF report.

**Architecture:** New `spc_inferences.py` module holds all inference logic as a pure function with no Streamlit or fpdf2 dependencies — fully testable in isolation. `app.py` calls it and renders the result with `st.markdown`/`st.info`. `report_utils.py` receives the result as a new `inferences` parameter to `build_pdf` and renders it as a text section after the stats table.

**Tech Stack:** Pure Python (spc_inferences.py), numpy (out-of-control point counting), Streamlit (display), fpdf2 (PDF section)

---

### Task 1: Create spc_inferences.py with TDD

**Files:**
- Create: `spc_inferences.py`
- Create: `tests/test_spc_inferences.py`

- [ ] **Step 1: Create the failing test file**

Create `tests/test_spc_inferences.py`:

```python
import numpy as np
import pytest

from spc_inferences import generate_inferences


def _stats(xbar=None, UCL_xbar=10.5, LCL_xbar=9.5):
    return {
        "xbar": np.array(xbar if xbar is not None else [10.0, 10.1, 9.9, 10.2, 10.0]),
        "xbar_bar": 10.0,
        "UCL_xbar": UCL_xbar,
        "LCL_xbar": LCL_xbar,
    }


def _cap(Cp=1.5, Cpk=1.45, Pp=1.42, Ppk=1.42, sigma_st=0.2, sigma_lt=0.25):
    return {"Cp": Cp, "Cpk": Cpk, "Pp": Pp, "Ppk": Ppk, "sigma_st": sigma_st, "sigma_lt": sigma_lt}


# Rule 1 — Capability

def test_rule1_capable():
    result = generate_inferences(_stats(), _cap(Cpk=1.45), 11.0, 9.0)
    assert result["bullets"][0]["icon"] == "✅"
    assert "capable" in result["bullets"][0]["text"].lower()


def test_rule1_marginal():
    result = generate_inferences(_stats(), _cap(Cpk=1.10), 11.0, 9.0)
    assert result["bullets"][0]["icon"] == "⚠️"
    assert "marginal" in result["bullets"][0]["text"].lower()


def test_rule1_not_capable():
    result = generate_inferences(_stats(), _cap(Cpk=0.85), 11.0, 9.0)
    assert result["bullets"][0]["icon"] == "❌"


def test_rule1_none_cpk():
    cap = {"Cp": None, "Cpk": None, "Pp": None, "Ppk": None, "sigma_st": 0.2, "sigma_lt": None}
    result = generate_inferences(_stats(), cap, 11.0, 9.0)
    assert result["bullets"][0]["icon"] == "ℹ️"


# Rule 2 — Centering

def test_rule2_off_center():
    result = generate_inferences(_stats(), _cap(Cp=1.6, Cpk=1.4), 11.0, 9.0)
    assert result["bullets"][1]["icon"] == "⚠️"
    assert "center" in result["bullets"][1]["text"].lower()


def test_rule2_centered():
    result = generate_inferences(_stats(), _cap(Cp=1.5, Cpk=1.46), 11.0, 9.0)
    assert result["bullets"][1]["icon"] == "✅"


def test_rule2_none():
    cap = {"Cp": None, "Cpk": None, "Pp": 1.3, "Ppk": 1.2, "sigma_st": 0.2, "sigma_lt": 0.25}
    result = generate_inferences(_stats(), cap, 11.0, 9.0)
    assert result["bullets"][1]["icon"] == "ℹ️"


# Rule 3 — Stability

def test_rule3_stable():
    result = generate_inferences(_stats(xbar=[10.0, 10.1, 9.9, 10.2, 10.3]), _cap(), 11.0, 9.0)
    assert result["bullets"][2]["icon"] == "✅"


def test_rule3_warning_1_to_2():
    # one point above UCL=10.5
    result = generate_inferences(_stats(xbar=[10.0, 10.7, 9.9, 10.1, 10.0]), _cap(), 11.0, 9.0)
    assert result["bullets"][2]["icon"] == "⚠️"


def test_rule3_unstable_3plus():
    # three points outside limits
    result = generate_inferences(_stats(xbar=[11.0, 10.7, 9.2, 10.1, 10.0]), _cap(), 11.0, 9.0)
    assert result["bullets"][2]["icon"] == "❌"


# Rule 4 — Long-term drift

def test_rule4_drift():
    result = generate_inferences(_stats(), _cap(Cpk=1.45, Ppk=1.20), 11.0, 9.0)
    assert result["bullets"][3]["icon"] == "⚠️"
    assert "long-term" in result["bullets"][3]["text"].lower()


def test_rule4_consistent():
    result = generate_inferences(_stats(), _cap(Cpk=1.45, Ppk=1.43), 11.0, 9.0)
    assert result["bullets"][3]["icon"] == "✅"


# Edge cases

def test_all_none_cap_no_exception():
    cap = {"Cp": None, "Cpk": None, "Pp": None, "Ppk": None, "sigma_st": None, "sigma_lt": None}
    result = generate_inferences(_stats(), cap, 11.0, 9.0)
    assert len(result["bullets"]) == 4
    assert all(b["icon"] == "ℹ️" for b in result["bullets"])


def test_narrative_is_nonempty_string():
    result = generate_inferences(_stats(), _cap(), 11.0, 9.0)
    assert isinstance(result["narrative"], str)
    assert len(result["narrative"]) > 20


def test_returns_four_bullets():
    result = generate_inferences(_stats(), _cap(), 11.0, 9.0)
    assert len(result["bullets"]) == 4
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_spc_inferences.py -v
```

Expected: All 14 tests FAIL with `ModuleNotFoundError: No module named 'spc_inferences'`

- [ ] **Step 3: Create spc_inferences.py**

Create `spc_inferences.py` in the project root:

```python
import numpy as np


def generate_inferences(stats: dict, cap: dict, USL: float, LSL: float) -> dict:
    bullets = []
    narrative_parts = []

    cpk = cap.get("Cpk")
    cp = cap.get("Cp")
    ppk = cap.get("Ppk")

    # Rule 1 — Capability (Cpk)
    if cpk is None:
        bullets.append({"icon": "ℹ️", "text": "Capability could not be calculated — check spec limits"})
        narrative_parts.append("Capability could not be assessed (spec limits may equal control limits).")
    elif cpk >= 1.33:
        bullets.append({"icon": "✅", "text": f"Process is capable — Cpk = {cpk:.3f} meets the 1.33 benchmark"})
        narrative_parts.append(f"This process is capable with a Cpk of {cpk:.3f}, meeting the 1.33 benchmark.")
    elif cpk >= 1.0:
        bullets.append({"icon": "⚠️", "text": f"Process is marginally capable — Cpk = {cpk:.3f} (target ≥ 1.33)"})
        narrative_parts.append(f"This process is marginally capable (Cpk = {cpk:.3f}), falling short of the 1.33 target.")
    else:
        bullets.append({"icon": "❌", "text": f"Process is not capable — Cpk = {cpk:.3f}, defects are likely"})
        narrative_parts.append(f"This process is not capable (Cpk = {cpk:.3f}), and defects are likely.")

    # Rule 2 — Centering (Cp vs Cpk)
    if cp is None or cpk is None:
        bullets.append({"icon": "ℹ️", "text": "Centering could not be assessed — spec limits required"})
        narrative_parts.append("Centering could not be assessed.")
    elif cp - cpk > 0.10:
        bullets.append({"icon": "⚠️", "text": f"Process is off-center — Cp ({cp:.3f}) is notably higher than Cpk ({cpk:.3f}), mean is shifted toward one spec limit"})
        narrative_parts.append(f"The process mean is shifted off-center (Cp = {cp:.3f} vs Cpk = {cpk:.3f}).")
    else:
        bullets.append({"icon": "✅", "text": "Process is well-centered within spec limits"})
        narrative_parts.append("The process is well-centered within spec limits.")

    # Rule 3 — Stability (out-of-control points on X-bar chart)
    xbar = np.asarray(stats.get("xbar", []))
    UCL = stats.get("UCL_xbar", float("inf"))
    LCL = stats.get("LCL_xbar", float("-inf"))
    if len(xbar) == 0:
        bullets.append({"icon": "ℹ️", "text": "Stability could not be assessed"})
        narrative_parts.append("Stability could not be assessed.")
    else:
        ooc = int(np.sum((xbar > UCL) | (xbar < LCL)))
        if ooc == 0:
            bullets.append({"icon": "✅", "text": "Process is stable — no points outside control limits"})
            narrative_parts.append("No out-of-control points were detected on the control chart.")
        elif ooc <= 2:
            bullets.append({"icon": "⚠️", "text": f"{ooc} point(s) outside control limits — investigate for assignable causes"})
            narrative_parts.append(f"{ooc} point(s) outside control limits suggest occasional instability worth investigating.")
        else:
            bullets.append({"icon": "❌", "text": f"{ooc} points outside control limits — process is unstable"})
            narrative_parts.append(f"{ooc} points outside control limits indicate the process is unstable.")

    # Rule 4 — Long-term drift (Cpk vs Ppk)
    if cpk is None or ppk is None:
        bullets.append({"icon": "ℹ️", "text": "Long-term drift could not be assessed"})
        narrative_parts.append("Long-term drift could not be assessed.")
    elif cpk - ppk > 0.15:
        bullets.append({"icon": "⚠️", "text": f"Long-term performance (Ppk = {ppk:.3f}) is notably worse than short-term (Cpk = {cpk:.3f}) — process may have drifted over time"})
        narrative_parts.append(f"Long-term performance (Ppk = {ppk:.3f}) is notably worse than short-term capability (Cpk = {cpk:.3f}), suggesting the process may have drifted.")
    else:
        bullets.append({"icon": "✅", "text": f"Short-term and long-term performance are consistent (Cpk = {cpk:.3f}, Ppk = {ppk:.3f})"})
        narrative_parts.append(f"Short and long-term performance are consistent (Cpk = {cpk:.3f}, Ppk = {ppk:.3f}).")

    return {"bullets": bullets, "narrative": " ".join(narrative_parts)}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_spc_inferences.py -v
```

Expected: 14 tests PASS

- [ ] **Step 5: Commit**

```bash
git add spc_inferences.py tests/test_spc_inferences.py
git commit -m "feat: add generate_inferences — 4-rule SPC inference engine"
```

---

### Task 2: Wire inferences into app.py display

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Add import at the top of app.py**

In `app.py`, find the existing import block:
```python
from report_utils import build_excel, build_pdf
```

Add one line immediately after it:
```python
from spc_inferences import generate_inferences
```

- [ ] **Step 2: Add the inferences call and display**

In `app.py`, find this block (around line 175–177):
```python
st.divider()

# --- Chart ---
```

Insert the following between `st.divider()` and `# --- Chart ---`:

```python
inferences = generate_inferences(stats, cap, USL, LSL)
st.caption("PROCESS INFERENCES")
for b in inferences["bullets"]:
    st.markdown(f"{b['icon']} {b['text']}")
st.info(inferences["narrative"])
st.divider()

```

- [ ] **Step 3: Run the full test suite**

```bash
python -m pytest -v
```

Expected: All 24 tests PASS (6 spc_utils + 4 report_utils + 14 spc_inferences)

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: display process inferences in Streamlit app"
```

---

### Task 3: Add inferences section to PDF

**Files:**
- Modify: `report_utils.py` — update `build_pdf` signature and add PDF rendering
- Modify: `app.py` — update `build_pdf` call to pass `inferences`
- Modify: `tests/test_report_utils.py` — update `build_pdf` calls to pass `inferences`

- [ ] **Step 1: Update build_pdf signature and add the inferences section**

In `report_utils.py`, find:
```python
def build_pdf(fig, stats, cap, column, chart_type, subgroup_size, USL, LSL, values):
```

Replace with:
```python
def build_pdf(fig, stats, cap, column, chart_type, subgroup_size, USL, LSL, values, inferences):
```

Then find the footer block at the end of `build_pdf`:
```python
    # Footer
    pdf.set_y(pdf.h - 15)
    pdf.set_font("Helvetica", "I", 7)
    pdf.cell(0, 5, "Generated by SPC Control Chart Tool - Internal Use Only", align="R")
```

Insert the following immediately before that footer block:

```python
    # Inferences section
    _icon_ascii = {"✅": "[OK]", "⚠️": "[!]", "❌": "[X]", "ℹ️": "[i]"}

    def _pdf_safe(text):
        for emoji, replacement in _icon_ascii.items():
            text = text.replace(emoji, replacement)
        return text

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Process Inferences", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    for b in inferences["bullets"]:
        pdf.set_font("Helvetica", "", 8)
        line = _pdf_safe(f"{b['icon']}  {b['text']}")
        pdf.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 5, _pdf_safe(inferences["narrative"]), fill=True)
    pdf.ln(2)

```

- [ ] **Step 2: Update build_pdf call in app.py**

In `app.py`, find:
```python
    pdf_buf = build_pdf(
        fig, stats, cap, column, chart_type, subgroup_size, USL, LSL, values
    )
```

Replace with:
```python
    pdf_buf = build_pdf(
        fig, stats, cap, column, chart_type, subgroup_size, USL, LSL, values, inferences
    )
```

- [ ] **Step 3: Update test_report_utils.py to pass inferences**

In `tests/test_report_utils.py`, add this import at the top (after the existing imports):
```python
from spc_inferences import generate_inferences
```

Then add this helper function after `_make_values()`:
```python
def _make_inferences():
    return generate_inferences(
        {
            "xbar": np.array([10.0, 10.1, 9.9]),
            "xbar_bar": 10.0,
            "UCL_xbar": 10.5,
            "LCL_xbar": 9.5,
        },
        _make_cap(),
        11.0,
        9.0,
    )
```

Then update all four test functions to pass `_make_inferences()` as the last argument. The four calls currently end with `_make_values()` — add `, _make_inferences()` after each:

```python
def test_build_pdf_returns_bytesio():
    fig = _make_fig()
    result = build_pdf(fig, _make_stats(), _make_cap(), "Diameter", "xbar_r", 5, 11.0, 9.0, _make_values(), _make_inferences())
    plt.close(fig)
    assert isinstance(result, io.BytesIO)


def test_build_pdf_produces_valid_pdf_bytes():
    fig = _make_fig()
    result = build_pdf(fig, _make_stats(), _make_cap(), "Diameter", "xbar_r", 5, 11.0, 9.0, _make_values(), _make_inferences())
    plt.close(fig)
    content = result.read()
    assert content[:4] == b"%PDF", "Output must start with PDF magic bytes"


def test_build_pdf_handles_none_capability():
    fig = _make_fig()
    cap = {"Cp": None, "Cpk": None, "Pp": None, "Ppk": None, "sigma_st": 0.2, "sigma_lt": None}
    none_inferences = generate_inferences(
        {"xbar": np.array([10.0, 10.1, 9.9]), "xbar_bar": 10.0, "UCL_xbar": 10.5, "LCL_xbar": 9.5},
        cap, 11.0, 9.0,
    )
    result = build_pdf(fig, _make_stats(), cap, "Diameter", "xbar_r", 5, 11.0, 9.0, _make_values(), none_inferences)
    plt.close(fig)
    content = result.read()
    assert content[:4] == b"%PDF"


def test_build_pdf_all_chart_types():
    for chart_type in ("xbar_r", "xbar_s", "im_r"):
        fig = _make_fig()
        result = build_pdf(
            fig, _make_stats(), _make_cap(), "Diameter", chart_type, 5, 11.0, 9.0, _make_values(), _make_inferences()
        )
        plt.close(fig)
        content = result.read()
        assert content[:4] == b"%PDF", f"Failed for chart_type={chart_type}"
```

- [ ] **Step 4: Run the full test suite**

```bash
python -m pytest -v
```

Expected: All 24 tests PASS

- [ ] **Step 5: Commit**

```bash
git add report_utils.py app.py tests/test_report_utils.py
git commit -m "feat: add process inferences section to PDF report"
```

---

### Task 4: Push to GitHub

- [ ] **Step 1: Push all commits**

```bash
git push
```

Expected: All commits pushed to `origin/main`.
