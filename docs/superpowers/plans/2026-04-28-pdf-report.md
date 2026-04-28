# PDF Report Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a downloadable, printer-ready PDF report to the SPC Control Chart Tool Streamlit app alongside the existing Excel download.

**Architecture:** Extract both report-generation functions (`build_excel`, `build_pdf`) into a new `report_utils.py` module — clean separation from Streamlit UI code and easy to test without mocking Streamlit. `app.py` imports these functions and passes the already-computed chart/stats objects. Two side-by-side `st.download_button` calls replace the current single button.

**Tech Stack:** fpdf2 (PDF generation), matplotlib (chart → PNG BytesIO), openpyxl (existing Excel), pytest (tests)

---

### Task 1: Add fpdf2 dependency

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add fpdf2 to requirements.txt**

Open `requirements.txt`. Add `fpdf2>=2.7.0` as a new line. Full file should be:

```
streamlit>=1.33.0
pandas>=2.0.0
numpy>=1.26.0
matplotlib>=3.8.0
openpyxl>=3.1.0
pytest>=8.0.0
fpdf2>=2.7.0
```

- [ ] **Step 2: Install the dependency**

```bash
pip install fpdf2
```

Expected: `Successfully installed fpdf2-2.x.x`

- [ ] **Step 3: Verify the import works**

```bash
python -c "from fpdf import FPDF; print('fpdf2 OK')"
```

Expected output: `fpdf2 OK`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "config: add fpdf2 dependency for PDF report generation"
```

---

### Task 2: Create report_utils.py — move build_excel, add build_pdf stub

**Files:**
- Create: `report_utils.py`
- Modify: `app.py` (remove build_excel definition + openpyxl imports, add import from report_utils)

- [ ] **Step 1: Create report_utils.py**

Create `report_utils.py` in the project root:

```python
import datetime
import io

import numpy as np
import openpyxl
from fpdf import FPDF
from openpyxl.drawing.image import Image as XLImage


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
        ["Sigma (ST)", round(cap["sigma_st"], 4) if cap["sigma_st"] is not None else "N/A"],
        ["Sigma (LT)", round(cap["sigma_lt"], 4) if cap["sigma_lt"] is not None else "N/A"],
        ["Cp",  round(cap["Cp"],  4) if cap["Cp"]  is not None else "N/A"],
        ["Cpk", round(cap["Cpk"], 4) if cap["Cpk"] is not None else "N/A"],
        ["Pp",  round(cap["Pp"],  4) if cap["Pp"]  is not None else "N/A"],
        ["Ppk", round(cap["Ppk"], 4) if cap["Ppk"] is not None else "N/A"],
    ]
    for row in rows:
        ws.append(row)

    ws2 = wb.create_sheet("Data")
    ws2.append(["Subgroup", "X-bar", stats["sub_label"]])
    for i, (xb, ss) in enumerate(zip(stats["xbar"], stats["sub_stat"])):
        ws2.append([
            i + 1,
            round(float(xb), 4),
            round(float(ss), 4) if not np.isnan(ss) else "",
        ])

    img = XLImage(buf_img)
    img.anchor = "D1"
    ws.add_image(img)

    buf_out = io.BytesIO()
    wb.save(buf_out)
    buf_out.seek(0)
    return buf_out


def build_pdf(fig, stats, cap, column, chart_type, subgroup_size, USL, LSL, values):
    raise NotImplementedError
```

- [ ] **Step 2: Update app.py imports and remove build_excel**

In `app.py`:

1. Remove these two import lines:
```python
import openpyxl
from openpyxl.drawing.image import Image as XLImage
```

2. Add this import after the existing `from spc_utils import ...` block:
```python
from report_utils import build_excel, build_pdf
```

3. Delete the entire `build_excel()` function definition (lines from `def build_excel(...)` through the `return buf_out` and closing blank lines, approximately 50 lines).

The existing `build_excel(...)` call at the bottom of `app.py` stays exactly as-is.

- [ ] **Step 3: Verify report_utils imports cleanly**

```bash
python -c "from report_utils import build_excel, build_pdf; print('import OK')"
```

Expected: `import OK`

- [ ] **Step 4: Commit**

```bash
git add report_utils.py app.py
git commit -m "refactor: extract build_excel to report_utils.py, stub build_pdf"
```

---

### Task 3: Write failing tests for build_pdf

**Files:**
- Create: `tests/test_report_utils.py`

- [ ] **Step 1: Create the test file**

Create `tests/test_report_utils.py`:

```python
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from report_utils import build_pdf


def _make_fig():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))
    ax1.plot([1, 2, 3], [10.0, 10.1, 9.9])
    ax2.plot([1, 2, 3], [0.5, 0.4, 0.6])
    return fig


def _make_stats():
    return {
        "xbar": np.array([10.0, 10.1, 9.9]),
        "sub_stat": np.array([0.5, 0.4, 0.6]),
        "xbar_bar": 10.0,
        "UCL_xbar": 10.5,
        "LCL_xbar": 9.5,
        "UCL_R": 1.0,
        "LCL_R": 0.0,
        "sigma_st": 0.2,
        "sub_label": "R",
    }


def _make_cap():
    return {
        "Cp": 1.33,
        "Cpk": 1.25,
        "Pp": 1.30,
        "Ppk": 1.20,
        "sigma_st": 0.2,
        "sigma_lt": 0.25,
    }


def _make_values():
    return np.array([9.8, 10.0, 10.2, 9.9, 10.1, 10.0, 9.8, 10.3])


def test_build_pdf_returns_bytesio():
    fig = _make_fig()
    result = build_pdf(fig, _make_stats(), _make_cap(), "Diameter", "xbar_r", 5, 11.0, 9.0, _make_values())
    plt.close(fig)
    assert isinstance(result, io.BytesIO)


def test_build_pdf_produces_valid_pdf_bytes():
    fig = _make_fig()
    result = build_pdf(fig, _make_stats(), _make_cap(), "Diameter", "xbar_r", 5, 11.0, 9.0, _make_values())
    plt.close(fig)
    content = result.read()
    assert content[:4] == b"%PDF", "Output must start with PDF magic bytes"


def test_build_pdf_handles_none_capability():
    fig = _make_fig()
    cap = {"Cp": None, "Cpk": None, "Pp": None, "Ppk": None, "sigma_st": 0.2, "sigma_lt": None}
    result = build_pdf(fig, _make_stats(), cap, "Diameter", "xbar_r", 5, 11.0, 9.0, _make_values())
    plt.close(fig)
    content = result.read()
    assert content[:4] == b"%PDF"


def test_build_pdf_all_chart_types():
    for chart_type in ("xbar_r", "xbar_s", "im_r"):
        fig = _make_fig()
        result = build_pdf(
            fig, _make_stats(), _make_cap(), "Diameter", chart_type, 5, 11.0, 9.0, _make_values()
        )
        plt.close(fig)
        content = result.read()
        assert content[:4] == b"%PDF", f"Failed for chart_type={chart_type}"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_report_utils.py -v
```

Expected: 4 tests FAIL with `NotImplementedError`

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/test_report_utils.py
git commit -m "test: add failing tests for build_pdf (TDD red phase)"
```

---

### Task 4: Implement build_pdf — green phase

**Files:**
- Modify: `report_utils.py` (replace `build_pdf` stub)

- [ ] **Step 1: Replace the stub with the full implementation**

In `report_utils.py`, replace:
```python
def build_pdf(fig, stats, cap, column, chart_type, subgroup_size, USL, LSL, values):
    raise NotImplementedError
```

with:

```python
def build_pdf(fig, stats, cap, column, chart_type, subgroup_size, USL, LSL, values):
    buf_img = io.BytesIO()
    fig.savefig(buf_img, format="png", dpi=150, bbox_inches="tight")
    buf_img.seek(0)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    page_w = pdf.w - 30  # usable width: A4 210mm minus 15mm margins each side

    # Header
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "SPC Control Chart Report", new_x="LMARGIN", new_y="NEXT", align="C")

    _chart_label = {
        "xbar_r": "X-bar / R Chart",
        "xbar_s": "X-bar / S Chart",
        "im_r":   "Individuals / Moving Range (I-MR) Chart",
    }
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(
        0, 6,
        f"Column: {column}   |   Chart: {_chart_label[chart_type]}   |   Date: {datetime.date.today()}",
        new_x="LMARGIN", new_y="NEXT", align="C",
    )
    pdf.ln(3)

    # Chart image — full usable width
    pdf.image(buf_img, x=15, w=page_w)
    pdf.ln(4)

    # Stats table — 3 equal columns
    def _fmt(v):
        return "N/A" if v is None else f"{v:.4f}"

    col_w   = page_w / 3
    row_h   = 5
    label_w = col_w * 0.60
    val_w   = col_w * 0.40

    sections = [
        ("Capability", [
            ("Cp",  _fmt(cap["Cp"])),
            ("Cpk", _fmt(cap["Cpk"])),
            ("Pp",  _fmt(cap["Pp"])),
            ("Ppk", _fmt(cap["Ppk"])),
        ]),
        ("Process", [
            ("Mean (X-bar)", f"{stats['xbar_bar']:.4f}"),
            ("Sigma ST",     _fmt(cap["sigma_st"])),
            ("Sigma LT",     _fmt(cap["sigma_lt"])),
            ("Min",          f"{values.min():.4f}"),
            ("Max",          f"{values.max():.4f}"),
            ("Observations", str(len(values))),
            ("Subgroup Size", str(subgroup_size)),
        ]),
        ("Control Limits", [
            ("UCL (X-bar)", f"{stats['UCL_xbar']:.4f}"),
            ("CL (X-bar)",  f"{stats['xbar_bar']:.4f}"),
            ("LCL (X-bar)", f"{stats['LCL_xbar']:.4f}"),
            ("USL",         f"{USL:.4f}"),
            ("LSL",         f"{LSL:.4f}"),
        ]),
    ]

    # Section header row
    y_header = pdf.get_y()
    for i, (title, _) in enumerate(sections):
        pdf.set_xy(15 + i * col_w, y_header)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(col_w, row_h + 1, title, border=1, align="C")
    pdf.set_y(y_header + row_h + 1)

    # Data rows
    max_rows = max(len(rows) for _, rows in sections)
    for row_idx in range(max_rows):
        y = pdf.get_y()
        for i, (_, rows) in enumerate(sections):
            pdf.set_xy(15 + i * col_w, y)
            if row_idx < len(rows):
                label, value = rows[row_idx]
                pdf.set_font("Helvetica", "B", 8)
                pdf.cell(label_w, row_h, label, border=1)
                pdf.set_font("Helvetica", "", 8)
                pdf.cell(val_w, row_h, value, border=1)
            else:
                pdf.cell(col_w, row_h, "", border=1)
        pdf.set_y(y + row_h)

    # Footer
    pdf.set_y(pdf.h - 15)
    pdf.set_font("Helvetica", "I", 7)
    pdf.cell(0, 5, "Generated by SPC Control Chart Tool — Internal Use Only", align="R")

    buf_out = io.BytesIO()
    buf_out.write(pdf.output())
    buf_out.seek(0)
    return buf_out
```

- [ ] **Step 2: Run tests to verify they pass**

```bash
python -m pytest tests/test_report_utils.py -v
```

Expected: 4 tests PASS

- [ ] **Step 3: Commit**

```bash
git add report_utils.py
git commit -m "feat: implement build_pdf for printable SPC report (fpdf2)"
```

---

### Task 5: Update app.py — add PDF download button

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Find the existing download button block**

Locate this section near the bottom of `app.py`:

```python
try:
    excel_buf = build_excel(
        fig, stats, cap, column, chart_type, subgroup_size, USL, LSL
    )
except Exception as e:
    st.warning(f"Excel export unavailable: {e}")
    excel_buf = None

if excel_buf:
    st.download_button(
        label="Download Excel Report",
        data=excel_buf,
        file_name="spc_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
```

- [ ] **Step 2: Replace the entire block**

Replace everything found in Step 1 with:

```python
try:
    excel_buf = build_excel(
        fig, stats, cap, column, chart_type, subgroup_size, USL, LSL
    )
except Exception as e:
    st.warning(f"Excel export unavailable: {e}")
    excel_buf = None

try:
    pdf_buf = build_pdf(
        fig, stats, cap, column, chart_type, subgroup_size, USL, LSL, values
    )
except Exception as e:
    st.warning(f"PDF export unavailable: {e}")
    pdf_buf = None

dl_col1, dl_col2 = st.columns(2)
if excel_buf:
    dl_col1.download_button(
        label="Download Excel Report",
        data=excel_buf,
        file_name="spc_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
if pdf_buf:
    dl_col2.download_button(
        label="Download PDF Report",
        data=pdf_buf,
        file_name="spc_report.pdf",
        mime="application/pdf",
    )
```

- [ ] **Step 3: Run the full test suite**

```bash
python -m pytest -v
```

Expected: All 10 tests PASS (6 existing spc_utils tests + 4 new report_utils tests)

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: add PDF report download button alongside Excel in SPC tool"
```

---

### Task 6: Push to GitHub

- [ ] **Step 1: Push all commits**

```bash
git push
```

Expected: All commits pushed to `origin/main`.
