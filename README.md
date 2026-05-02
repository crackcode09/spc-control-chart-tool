# SPC Control Chart Tool

A browser-based Statistical Process Control (SPC) tool built with Streamlit. Upload a CSV file, configure your analysis, and instantly generate control charts with full process capability reporting — no software installation required.

Supports X-bar/R, X-bar/S, and Individuals/Moving Range (I-MR) charts with automatic chart type selection, configurable spec limits, and one-click Excel export.

---

## Live App

**[https://spcanalysistool.streamlit.app](https://spcanalysistool.streamlit.app)**

Open in any browser — no Python, no Jupyter, no installation needed.

---

## Features

- **Three SPC chart types** — X-bar/R, X-bar/S, and I-MR; auto-selected based on subgroup size
- **Dual-panel chart** — X-bar (or Individuals) chart on top, R/S/MR companion chart below
- **Control limit zones** — green shading within control limits, yellow shading in warning zones
- **Capability indices** — Cp, Cpk (short-term) and Pp, Ppk (long-term) calculated automatically
- **Anderson-Darling normality test** — A² statistic + p-value banner; Cp/Cpk hidden when data is non-normal (only Pp/Ppk shown), since Cp/Cpk assume normal distribution
- **Process inferences** — automated 5-rule diagnostics (capability, centering, stability, ST-vs-LT consistency, normality) with bullet verdicts and narrative summary
- **Process statistics** — mean, short- and long-term sigma, min, max, and observation count
- **Configurable spec limits** — USL and LSL inputs with sensible defaults (mean ± 3σ)
- **Excel + PDF export** — formatted `.xlsx` report with embedded chart and data table; `.pdf` report with chart, stats, and inferences
- **Graceful error handling** — clear messages for malformed files, insufficient data, or invalid inputs

---

## Chart Types

| Chart | Description | Auto-selected when |
| --- | --- | --- |
| X-bar / R | Subgroup means and ranges | n = 2–8 |
| X-bar / S | Subgroup means and standard deviations | n ≥ 9 |
| I-MR | Individual values and moving ranges | Manual selection only |

![Chart type selection guide](screenshots/chart_type.png)

---

## How to Use

1. **Open the app** at [https://spcanalysistool.streamlit.app](https://spcanalysistool.streamlit.app)
2. **Upload a file** using the sidebar — supports CSV (comma, semicolon, or tab delimited) and Excel (`.xlsx` / `.xls`). For multi-sheet Excel files, a sheet selector appears automatically
3. **Select the column** to analyze from the dropdown (numeric columns only)
4. **Set subgroup size** using the slider — chart type auto-selects based on n
5. **Adjust USL and LSL** if the defaults (mean ± 3σ) do not match your specification
6. The chart and statistics update instantly — **Download Excel Report** to save results

---

## App Output

### Capability Indices

| Metric | Description |
| --- | --- |
| **Cp** | Process capability — spread relative to tolerance (short-term sigma) |
| **Cpk** | Process capability accounting for mean centering (short-term sigma) |
| **Pp** | Process performance — spread relative to tolerance (long-term sigma) |
| **Ppk** | Process performance accounting for mean centering (long-term sigma) |

> **Note:** Cp/Cpk are hidden when the Anderson-Darling test reports non-normal data (p < 0.05), since these indices assume a normal distribution. Pp/Ppk remain shown.

### Normality Test (Anderson-Darling)

| Field | Description |
| --- | --- |
| **A²** | Anderson-Darling statistic |
| **p-value** | Stephens (1986) approximation; verdict at α = 0.05 |
| **Verdict** | NORMAL (p ≥ 0.05) → all capability indices shown; NON-NORMAL (p < 0.05) → only Pp/Ppk shown |

### Process Inferences

Five-rule diagnostic block printed below the metrics:

| Rule | Checks |
| --- | --- |
| 1. Capability | Cpk vs 1.33 / 1.0 thresholds |
| 2. Centering | Cp vs Cpk gap (off-center detection) |
| 3. Stability | Out-of-control points on the X-bar chart |
| 4. Drift | Cpk vs Ppk consistency |
| 5. Normality | Anderson-Darling verdict |

### Process Statistics

| Metric | Description |
| --- | --- |
| **Mean (X̄)** | Grand mean of all subgroup averages |
| **Sigma ST** | Short-term sigma estimated from within-subgroup variation |
| **Sigma LT** | Long-term sigma — overall standard deviation of all individual values |
| **Min / Max** | Minimum and maximum values in the dataset |
| **Observations** | Total number of data points used in the analysis |

### Control Chart

- Top panel: X-bar (or Individuals) chart with UCL, LCL, USL, LSL, and a stats annotation box
- Bottom panel: R, S, or MR companion chart with its own UCL and LCL

### Excel Export

The downloaded `.xlsx` report contains two sheets:

| Sheet | Contents |
| --- | --- |
| **SPC Report** | Stats summary table (chart type, control limits, spec limits, capability indices) + embedded chart image |
| **Data** | Per-subgroup X-bar and R/S/MR values |

### PDF Export

The downloaded `.pdf` report contains a single A4 page with:

- Report title, column name, chart type, and date header
- Embedded control chart (X-bar + companion panel)
- Three-column stats table — Capability, Process, Control Limits
- Process Inferences section (5-rule bullets + narrative summary)

---

## Local Development

### Requirements

```bash
pip install -r requirements.txt
```

| Package | Version | Purpose |
| --- | --- | --- |
| `streamlit` | ≥ 1.33.0 | Web app framework |
| `pandas` | ≥ 2.0.0 | CSV loading and data manipulation |
| `numpy` | ≥ 1.26.0 | Subgroup calculations and control limits |
| `scipy` | ≥ 1.11.0 | Anderson-Darling normality test |
| `matplotlib` | ≥ 3.8.0 | Chart rendering |
| `openpyxl` | ≥ 3.1.0 | Excel file export |
| `fpdf2` | ≥ 2.7.0 | PDF report export |
| `pytest` | ≥ 8.0.0 | Unit tests |

### Run locally

```bash
streamlit run app.py
```

> If `streamlit` is not on your PATH, use `python -m streamlit run app.py`.

### Run tests

```bash
pytest tests/ -v
```

### Deploy on Streamlit Cloud

1. Fork or push this repo to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account and select this repository
4. Set **Main file path** to `app.py`
5. Click **Deploy** — the app is live instantly at a public URL

---

## File Structure

```text
spc-control-chart-tool/
├── app.py                      # Streamlit app — UI, chart rendering, Excel/PDF export
├── spc_utils.py                # SPC calculation logic — chart stats, capability, Anderson-Darling
├── spc_inferences.py           # 5-rule diagnostic engine (capability, centering, stability, drift, normality)
├── report_utils.py             # Excel + PDF report builders
├── requirements.txt            # Python dependencies
├── spc_tool.ipynb              # Original Jupyter notebook version
├── sample_spc_report.xlsx      # Example Excel export output
├── .streamlit/
│   └── config.toml             # Streamlit theme configuration
├── tests/
│   ├── test_spc_utils.py       # Tests for SPC calculations + Anderson-Darling
│   ├── test_spc_inferences.py  # Tests for 5-rule inference engine
│   └── test_report_utils.py    # Tests for Excel/PDF builders
├── screenshots/
│   └── chart_type.png          # Chart type selection reference
└── docs/
    └── plans/                  # Implementation planning documents
```

---

## SPC Methodology

- **Short-term sigma (Cp/Cpk)** is estimated from within-subgroup variation using R-bar/d₂ (X-bar/R) or S-bar/c₄ (X-bar/S) — this reflects the process's inherent capability when operating in a stable state.
- **Long-term sigma (Pp/Ppk)** is the overall standard deviation of all individual measurements — this reflects actual process performance including shifts and drifts over time.
- **Subgroup truncation** — data is truncated to the nearest complete subgroup; incomplete trailing observations are excluded.
- **SPC constants** (A2, A3, D3, D4, B3, B4, d2, c4) are tabulated for subgroup sizes n = 2 through 25 per AIAG/Shewhart reference tables.
- **Anderson-Darling normality** — uses `scipy.stats.anderson` with the Stephens (1986) small-sample correction (`A²* = A² · (1 + 0.75/n + 2.25/n²)`) and piecewise p-value approximation. Minimum sample size: 8. When p < 0.05, Cp/Cpk are suppressed since their normal-distribution assumption no longer holds.

---

## Demo Dataset

The included demo uses the [UCI Wine dataset](https://archive.ics.uci.edu/dataset/109/wine) (178 observations, 13 chemical attributes). Replace with your own process or manufacturing data for real analysis.

---

## License

[MIT](LICENSE) — free to use, modify, and distribute.
