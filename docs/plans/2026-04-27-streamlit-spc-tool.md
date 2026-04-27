# Streamlit SPC Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the Jupyter notebook SPC tool into a Streamlit web app anyone can use in a browser without installing Jupyter.

**Architecture:** Single-page Streamlit app with a sidebar for controls (file upload, column, chart type, subgroup size, USL/LSL) and a main area for the chart and capability stats. Calculation logic is extracted into a separate `spc_utils.py` module so it can be tested independently. Excel export uses an in-memory buffer delivered as a download button.

**Tech Stack:** Python, Streamlit, pandas, numpy, matplotlib, openpyxl

---

## File Structure

| File | Purpose |
|---|---|
| `app.py` | Streamlit entry point — UI layout, sidebar controls, chart display, download button |
| `spc_utils.py` | Pure calculation logic — chart stats, control limits, capability indices |
| `requirements.txt` | All Python dependencies |
| `tests/test_spc_utils.py` | Unit tests for calculation logic |
| `.streamlit/config.toml` | Streamlit theme config |

---

### Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.streamlit/config.toml`

- [ ] **Step 1: Create `requirements.txt`**

```
streamlit>=1.33.0
pandas>=2.0.0
numpy>=1.26.0
matplotlib>=3.8.0
openpyxl>=3.1.0
pytest>=8.0.0
```

- [ ] **Step 2: Create `.streamlit/config.toml`**

```toml
[theme]
primaryColor = "#0078E6"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F4F8"
textColor = "#1A1A1A"
font = "sans serif"
```

- [ ] **Step 3: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 4: Commit**

```bash
git add requirements.txt .streamlit/config.toml
git commit -m "config: add streamlit requirements and theme"
```

---

### Task 2: Calculation Logic (`spc_utils.py`)

**Files:**
- Create: `spc_utils.py`
- Create: `tests/test_spc_utils.py`

- [ ] **Step 1: Create `tests/test_spc_utils.py` with failing tests**

```python
import numpy as np
import pytest
from spc_utils import calculate_xbar_r, calculate_xbar_s, calculate_imr, calculate_capability

VALUES = np.array([3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.0,
                   3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.0, 4.1] * 5)

def test_xbar_r_returns_required_keys():
    result = calculate_xbar_r(VALUES, n=5)
    for key in ['xbar', 'sub_stat', 'xbar_bar', 'UCL_xbar', 'LCL_xbar', 'UCL_R', 'LCL_R', 'sigma_st', 'sub_label']:
        assert key in result, f"Missing key: {key}"

def test_xbar_r_ucl_gt_lcl():
    result = calculate_xbar_r(VALUES, n=5)
    assert result['UCL_xbar'] > result['LCL_xbar']
    assert result['UCL_R'] > result['LCL_R']

def test_xbar_s_returns_required_keys():
    result = calculate_xbar_s(VALUES, n=10)
    for key in ['xbar', 'sub_stat', 'xbar_bar', 'UCL_xbar', 'LCL_xbar', 'UCL_R', 'LCL_R', 'sigma_st', 'sub_label']:
        assert key in result, f"Missing key: {key}"

def test_imr_returns_required_keys():
    result = calculate_imr(VALUES)
    for key in ['xbar', 'sub_stat', 'xbar_bar', 'UCL_xbar', 'LCL_xbar', 'UCL_R', 'LCL_R', 'sigma_st', 'sub_label']:
        assert key in result, f"Missing key: {key}"

def test_capability_indices():
    stats = calculate_xbar_r(VALUES, n=5)
    cap = calculate_capability(VALUES, stats['xbar_bar'], stats['sigma_st'], USL=4.5, LSL=3.0)
    assert cap['Cp'] > 0
    assert cap['Cpk'] > 0
    assert cap['Pp'] > 0
    assert cap['Ppk'] > 0

def test_auto_select_chart_type():
    from spc_utils import auto_select_chart_type
    assert auto_select_chart_type(2) == 'xbar_r'
    assert auto_select_chart_type(8) == 'xbar_r'
    assert auto_select_chart_type(9) == 'xbar_s'
    assert auto_select_chart_type(15) == 'xbar_s'
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_spc_utils.py -v
```

Expected: `ModuleNotFoundError: No module named 'spc_utils'`

- [ ] **Step 3: Create `spc_utils.py`**

```python
import numpy as np

CONSTANTS = {
    2:  {"A2": 1.880, "D3": 0,     "D4": 3.267, "A3": 2.659, "B3": 0,     "B4": 3.267},
    3:  {"A2": 1.023, "D3": 0,     "D4": 2.574, "A3": 1.954, "B3": 0,     "B4": 2.568},
    4:  {"A2": 0.729, "D3": 0,     "D4": 2.282, "A3": 1.628, "B3": 0,     "B4": 2.266},
    5:  {"A2": 0.577, "D3": 0,     "D4": 2.114, "A3": 1.427, "B3": 0,     "B4": 2.089},
    6:  {"A2": 0.483, "D3": 0,     "D4": 2.004, "A3": 1.287, "B3": 0.030, "B4": 1.970},
    7:  {"A2": 0.419, "D3": 0.076, "D4": 1.924, "A3": 1.182, "B3": 0.118, "B4": 1.882},
    8:  {"A2": 0.373, "D3": 0.136, "D4": 1.864, "A3": 1.099, "B3": 0.185, "B4": 1.815},
    9:  {"A2": 0.337, "D3": 0.184, "D4": 1.816, "A3": 1.032, "B3": 0.239, "B4": 1.761},
    10: {"A2": 0.308, "D3": 0.223, "D4": 1.777, "A3": 0.975, "B3": 0.284, "B4": 1.716},
    11: {"A2": 0.283, "D3": 0.247, "D4": 1.742, "A3": 0.943, "B3": 0.310, "B4": 1.695},
    12: {"A2": 0.261, "D3": 0.268, "D4": 1.712, "A3": 0.915, "B3": 0.332, "B4": 1.674},
    13: {"A2": 0.243, "D3": 0.284, "D4": 1.693, "A3": 0.888, "B3": 0.352, "B4": 1.653},
    14: {"A2": 0.226, "D3": 0.297, "D4": 1.676, "A3": 0.864, "B3": 0.370, "B4": 1.637},
    15: {"A2": 0.211, "D3": 0.308, "D4": 1.663, "A3": 0.848, "B3": 0.386, "B4": 1.622},
    16: {"A2": 0.197, "D3": 0.318, "D4": 1.651, "A3": 0.833, "B3": 0.400, "B4": 1.608},
    17: {"A2": 0.185, "D3": 0.325, "D4": 1.641, "A3": 0.819, "B3": 0.413, "B4": 1.597},
    18: {"A2": 0.173, "D3": 0.330, "D4": 1.632, "A3": 0.807, "B3": 0.425, "B4": 1.585},
    19: {"A2": 0.162, "D3": 0.334, "D4": 1.624, "A3": 0.797, "B3": 0.435, "B4": 1.575},
    20: {"A2": 0.153, "D3": 0.338, "D4": 1.617, "A3": 0.787, "B3": 0.443, "B4": 1.566},
    21: {"A2": 0.145, "D3": 0.341, "D4": 1.611, "A3": 0.779, "B3": 0.451, "B4": 1.557},
    22: {"A2": 0.135, "D3": 0.344, "D4": 1.604, "A3": 0.769, "B3": 0.459, "B4": 1.548},
    23: {"A2": 0.126, "D3": 0.347, "D4": 1.598, "A3": 0.761, "B3": 0.467, "B4": 1.541},
    24: {"A2": 0.118, "D3": 0.350, "D4": 1.593, "A3": 0.753, "B3": 0.473, "B4": 1.534},
    25: {"A2": 0.111, "D3": 0.352, "D4": 1.588, "A3": 0.746, "B3": 0.479, "B4": 1.528},
}

D2 = {2:1.128, 3:1.693, 4:2.059, 5:2.326, 6:2.534, 7:2.704, 8:2.847, 9:2.970,
      10:3.078, 11:3.173, 12:3.252, 13:3.322, 14:3.384, 15:3.440, 16:3.492,
      17:3.538, 18:3.581, 19:3.619, 20:3.655, 21:3.685, 22:3.713, 23:3.737,
      24:3.761, 25:3.780}

C4 = {2:0.7979, 3:0.8862, 4:0.9213, 5:0.9400, 6:0.9515, 7:0.9594, 8:0.9650,
      9:0.9693, 10:0.9727, 11:0.9754, 12:0.9776, 13:0.9793, 14:0.9806, 15:0.9818,
      16:0.9828, 17:0.9836, 18:0.9843, 19:0.9849, 20:0.9854, 21:0.9859, 22:0.9863,
      23:0.9866, 24:0.9869, 25:0.9871}


def auto_select_chart_type(n: int) -> str:
    if n < 9:
        return 'xbar_r'
    return 'xbar_s'


def calculate_xbar_r(values: np.ndarray, n: int) -> dict:
    c = CONSTANTS[n]
    data = values[:(len(values) // n) * n].reshape(-1, n)
    xbar = data.mean(axis=1)
    R = data.max(axis=1) - data.min(axis=1)
    xbar_bar = xbar.mean()
    R_bar = R.mean()
    return {
        'xbar': xbar,
        'sub_stat': R,
        'xbar_bar': xbar_bar,
        'UCL_xbar': xbar_bar + c["A2"] * R_bar,
        'LCL_xbar': xbar_bar - c["A2"] * R_bar,
        'UCL_R': c["D4"] * R_bar,
        'LCL_R': c["D3"] * R_bar,
        'sigma_st': R_bar / D2[n],
        'sub_label': 'Range (R)',
    }


def calculate_xbar_s(values: np.ndarray, n: int) -> dict:
    c = CONSTANTS[n]
    data = values[:(len(values) // n) * n].reshape(-1, n)
    xbar = data.mean(axis=1)
    s = data.std(axis=1, ddof=1)
    xbar_bar = xbar.mean()
    s_bar = s.mean()
    return {
        'xbar': xbar,
        'sub_stat': s,
        'xbar_bar': xbar_bar,
        'UCL_xbar': xbar_bar + c["A3"] * s_bar,
        'LCL_xbar': xbar_bar - c["A3"] * s_bar,
        'UCL_R': c["B4"] * s_bar,
        'LCL_R': c["B3"] * s_bar,
        'sigma_st': s_bar / C4[n],
        'sub_label': 'Standard Deviation (S)',
    }


def calculate_imr(values: np.ndarray) -> dict:
    R = np.abs(np.diff(values))
    xbar_bar = values.mean()
    R_bar = R.mean()
    return {
        'xbar': values,
        'sub_stat': R,
        'xbar_bar': xbar_bar,
        'UCL_xbar': xbar_bar + 2.66 * R_bar,
        'LCL_xbar': xbar_bar - 2.66 * R_bar,
        'UCL_R': 3.267 * R_bar,
        'LCL_R': 0.0,
        'sigma_st': R_bar / D2[2],
        'sub_label': 'Moving Range (MR)',
    }


def calculate_capability(values: np.ndarray, xbar_bar: float, sigma_st: float,
                          USL: float, LSL: float) -> dict:
    sigma_lt = np.std(values, ddof=1)
    return {
        'Cp':  (USL - LSL) / (6 * sigma_st),
        'Cpk': min(USL - xbar_bar, xbar_bar - LSL) / (3 * sigma_st),
        'Pp':  (USL - LSL) / (6 * sigma_lt),
        'Ppk': min(USL - xbar_bar, xbar_bar - LSL) / (3 * sigma_lt),
        'sigma_st': sigma_st,
        'sigma_lt': sigma_lt,
    }
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_spc_utils.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add spc_utils.py tests/test_spc_utils.py
git commit -m "feat: add spc_utils calculation module with tests"
```

---

### Task 3: Streamlit App (`app.py`)

**Files:**
- Create: `app.py`

- [ ] **Step 1: Create `app.py`**

```python
import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import streamlit as st
import openpyxl
from openpyxl.drawing.image import Image as XLImage

from spc_utils import (
    auto_select_chart_type,
    calculate_xbar_r,
    calculate_xbar_s,
    calculate_imr,
    calculate_capability,
)

st.set_page_config(page_title="SPC Control Chart Tool", layout="wide")
st.title("SPC Control Chart Tool")

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    delimiter = st.selectbox("CSV Delimiter", [",", ";", "\\t"], index=0)

if uploaded_file is None:
    st.info("Upload a CSV file to get started.")
    st.stop()

sep = "\t" if delimiter == "\\t" else delimiter
df = pd.read_csv(uploaded_file, sep=sep)
numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

if not numeric_cols:
    st.error("No numeric columns found in the uploaded file.")
    st.stop()

with st.sidebar:
    column = st.selectbox("Select Column", numeric_cols)
    subgroup_size = st.slider("Subgroup Size (n)", min_value=2, max_value=25, value=5)
    default_chart = auto_select_chart_type(subgroup_size)
    chart_type = st.selectbox(
        "Chart Type",
        ["xbar_r", "xbar_s", "im_r"],
        index=["xbar_r", "xbar_s", "im_r"].index(default_chart),
        help="Auto-selected based on subgroup size. Override manually if needed.",
    )
    USL = st.number_input("USL (Upper Spec Limit)", value=float(df[column].mean() + 3 * df[column].std()))
    LSL = st.number_input("LSL (Lower Spec Limit)", value=float(df[column].mean() - 3 * df[column].std()))

values = df[column].dropna().values

# --- Calculate stats ---
if chart_type == "xbar_r":
    stats = calculate_xbar_r(values, subgroup_size)
elif chart_type == "xbar_s":
    stats = calculate_xbar_s(values, subgroup_size)
else:
    stats = calculate_imr(values)

cap = calculate_capability(values, stats["xbar_bar"], stats["sigma_st"], USL, LSL)

# --- Capability metric cards ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Cp",  f"{cap['Cp']:.3f}")
col2.metric("Cpk", f"{cap['Cpk']:.3f}")
col3.metric("Pp",  f"{cap['Pp']:.3f}")
col4.metric("Ppk", f"{cap['Ppk']:.3f}")

# --- Chart ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7))

xbar = stats["xbar"]
sub_stat = stats["sub_stat"]
xbar_bar = stats["xbar_bar"]
x = range(len(xbar))
x2 = range(len(sub_stat))

ax1.plot(x, xbar, marker="o", color="#0078E6", markersize=4, label=column)
ax1.axhline(xbar_bar,           color="green",   linewidth=1.5, label="CL")
ax1.axhline(stats["UCL_xbar"],  color="red",     linewidth=1.5, linestyle="--", label="UCL")
ax1.axhline(stats["LCL_xbar"],  color="red",     linewidth=1.5, linestyle="--", label="LCL")
ax1.axhline(USL,                color="darkred", linewidth=2,   linestyle="-",  label="USL")
ax1.axhline(LSL,                color="darkred", linewidth=2,   linestyle="-",  label="LSL")
ax1.fill_between(x, stats["LCL_xbar"], stats["UCL_xbar"], alpha=0.08, color="green")
ax1.fill_between(x, stats["UCL_xbar"], USL,               alpha=0.08, color="yellow")
ax1.fill_between(x, LSL,               stats["LCL_xbar"], alpha=0.08, color="yellow")
ax1.set_title(f"X-bar Chart — {column} ({chart_type})")
ax1.set_ylabel(column)
ax1.legend(loc="upper right", fontsize=7)

stats_text = (f"n={subgroup_size}  Cp={cap['Cp']:.3f}  Cpk={cap['Cpk']:.3f}\n"
              f"Pp={cap['Pp']:.3f}  Ppk={cap['Ppk']:.3f}")
ax1.text(0.01, 0.97, stats_text, transform=ax1.transAxes, fontsize=8,
         verticalalignment="top", bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

ax2.plot(x2, sub_stat, marker="o", color="purple", markersize=4, label=stats["sub_label"])
ax2.axhline(np.nanmean(sub_stat), color="green", linewidth=1.5, label="CL")
ax2.axhline(stats["UCL_R"],       color="red",   linewidth=1.5, linestyle="--", label="UCL")
ax2.axhline(stats["LCL_R"],       color="red",   linewidth=1.5, linestyle="--", label="LCL")
ax2.set_title(f"{stats['sub_label']} Chart")
ax2.set_ylabel(stats["sub_label"])
ax2.legend(loc="upper right", fontsize=7)

plt.tight_layout()
st.pyplot(fig)

# --- Excel export ---
def build_excel(fig, stats, cap, column, chart_type, subgroup_size, USL, LSL):
    buf_img = io.BytesIO()
    fig.savefig(buf_img, format="png", dpi=150, bbox_inches="tight")
    buf_img.seek(0)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "SPC Report"

    rows = [
        ["Column", column],
        ["Chart Type", chart_type],
        ["Subgroup Size", subgroup_size],
        ["CL (X-bar)", round(stats["xbar_bar"], 4)],
        ["UCL", round(stats["UCL_xbar"], 4)],
        ["LCL", round(stats["LCL_xbar"], 4)],
        ["USL", USL],
        ["LSL", LSL],
        ["Sigma (ST)", round(cap["sigma_st"], 4)],
        ["Sigma (LT)", round(cap["sigma_lt"], 4)],
        ["Cp",  round(cap["Cp"],  4)],
        ["Cpk", round(cap["Cpk"], 4)],
        ["Pp",  round(cap["Pp"],  4)],
        ["Ppk", round(cap["Ppk"], 4)],
    ]
    for row in rows:
        ws.append(row)

    ws2 = wb.create_sheet("Data")
    ws2.append(["Subgroup", "X-bar", stats["sub_label"]])
    for i, (xb, ss) in enumerate(zip(stats["xbar"], stats["sub_stat"])):
        ws2.append([i + 1, round(float(xb), 4), round(float(ss), 4)])

    img = XLImage(buf_img)
    img.anchor = "D1"
    ws.add_image(img)

    buf_out = io.BytesIO()
    wb.save(buf_out)
    buf_out.seek(0)
    return buf_out

excel_buf = build_excel(fig, stats, cap, column, chart_type, subgroup_size, USL, LSL)
st.download_button(
    label="Download Excel Report",
    data=excel_buf,
    file_name="spc_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
```

- [ ] **Step 2: Run the app locally to verify it works**

```bash
streamlit run app.py
```

Expected: browser opens, sidebar shows file uploader, uploading a CSV populates all controls, chart renders, Download button appears.

Test with the included demo file by pointing at the wine dataset or any CSV with numeric columns.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add streamlit SPC app"
```

---

### Task 4: Update README and Deploy Instructions

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add Streamlit section to README**

Add after the existing Features section:

```markdown
## Run the Streamlit App

```bash
pip install -r requirements.txt
streamlit run app.py
```

Upload any CSV with numeric columns. The app auto-selects the chart type based on subgroup size and generates a downloadable Excel report.

### Deploy free on Streamlit Cloud

1. Push this repo to GitHub (already done)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account and select this repo
4. Set **Main file path** to `app.py`
5. Click Deploy — anyone with the link can use it instantly, no install required
```

- [ ] **Step 2: Commit and push everything**

```bash
git add README.md docs/
git commit -m "docs: add streamlit run instructions and deploy guide"
git push
```

---

## Self-Review

**Spec coverage:**
- ✅ File upload (CSV with delimiter choice)
- ✅ Column selector (numeric columns only)
- ✅ Chart type auto-select (xbar_r n<9, xbar_s n≥9, im_r manual)
- ✅ Subgroup size slider
- ✅ USL / LSL inputs
- ✅ X-bar + R/S/MR dual chart
- ✅ Cp, Cpk, Pp, Ppk metrics
- ✅ Excel download
- ✅ Tests for calculation logic
- ✅ Deploy instructions

**Placeholder scan:** None found — all steps have complete code.

**Type consistency:** `calculate_*` functions all return the same dict shape with identical keys (`xbar`, `sub_stat`, `xbar_bar`, `UCL_xbar`, `LCL_xbar`, `UCL_R`, `LCL_R`, `sigma_st`, `sub_label`). `app.py` consumes them consistently.
