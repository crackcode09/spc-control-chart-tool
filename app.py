import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from spc_utils import (
    auto_select_chart_type,
    calculate_xbar_r,
    calculate_xbar_s,
    calculate_imr,
    calculate_capability,
)
from report_utils import build_excel, build_pdf
from spc_inferences import generate_inferences

st.set_page_config(page_title="SPC Control Chart Tool", layout="wide")
st.title("SPC Control Chart Tool")

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")
    uploaded_file = st.file_uploader("Upload File", type=["csv", "xlsx", "xls"])
    is_excel = uploaded_file is not None and uploaded_file.name.lower().endswith((".xlsx", ".xls"))
    if not is_excel:
        delimiter = st.selectbox("CSV Delimiter", [",", ";", "\\t"], index=0)

if uploaded_file is None:
    st.markdown("""
## What is this tool?

This is a **Statistical Process Control (SPC) Chart Tool**. SPC is a method used in manufacturing and quality engineering to monitor a process over time and determine whether it is operating within expected variation — or showing signs of a problem.

Upload your process data and this tool will automatically:
- Plot a **control chart** showing whether your process is stable
- Calculate **control limits** (UCL/LCL) based on your data
- Compute **process capability indices** (Cp, Cpk, Pp, Ppk) against your specification limits
- Generate **process inferences** — 4-rule diagnostic checks (capability, centering, stability, ST vs LT consistency)
- Generate **downloadable Excel and PDF reports** with the chart, stats summary, and inferences

---

## How to get started

| Step | What to do |
| --- | --- |
| **1. Upload your data** | Use the sidebar to upload a CSV or Excel file containing your measurements |
| **2. Select a column** | Pick the numeric column you want to analyze |
| **3. Set subgroup size** | Choose how many measurements make up one subgroup — the chart type auto-selects |
| **4. Enter spec limits** | Enter your USL (upper) and LSL (lower) specification limits |
| **5. Set report title** | Optionally enter a custom heading shown on the PDF and Excel reports |
| **6. Read the chart** | Points outside the red dashed lines (UCL/LCL) indicate an out-of-control condition |
| **7. Review inferences** | Read the bullet diagnostics and narrative summary below the stats |
| **8. Download report** | Click Excel or PDF to save a formatted report |

---

## Chart types

| Chart | Used when | Subgroup size |
| --- | --- | --- |
| **X-bar / R** | Tracking subgroup averages and ranges | n = 2–8 |
| **X-bar / S** | Tracking subgroup averages and std deviation | n ≥ 9 |
| **I-MR** | Individual measurements, no subgrouping | Manual selection |

---

## What do Cp and Cpk mean?

- **Cp ≥ 1.33** — process spread fits within spec with margin (capable)
- **Cpk ≥ 1.33** — process is both capable *and* centered within spec
- **Cp > Cpk** — process is capable but the mean is shifted off-center
- **Cp or Cpk < 1.0** — process is not capable; defects are likely

> **Pp and Ppk** use the same formulas but with long-term (overall) variation instead of short-term — they reflect actual historical performance rather than potential capability.
""")
    st.stop()

try:
    if is_excel:
        xl = pd.ExcelFile(uploaded_file)
        sheet_names = xl.sheet_names
        with st.sidebar:
            sheet = st.selectbox("Sheet", sheet_names) if len(sheet_names) > 1 else sheet_names[0]
        df = xl.parse(sheet)
    else:
        sep = "\t" if delimiter == "\\t" else delimiter
        df = pd.read_csv(uploaded_file, sep=sep)
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()
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
    if chart_type == "im_r":
        st.caption("Subgroup size is not used for I-MR charts.")
    _col_mean = df[column].mean()
    _col_std = df[column].std()
    _usl_default = (
        float(_col_mean + 3 * _col_std)
        if np.isfinite(_col_mean) and np.isfinite(_col_std)
        else 0.0
    )
    _lsl_default = (
        float(_col_mean - 3 * _col_std)
        if np.isfinite(_col_mean) and np.isfinite(_col_std)
        else 0.0
    )
    USL = st.number_input("USL (Upper Spec Limit)", value=_usl_default)
    LSL = st.number_input("LSL (Lower Spec Limit)", value=_lsl_default)
    report_title = st.text_input("Report Title", value="SPC Control Chart Report")

values = df[column].dropna().values

# --- Calculate stats ---
try:
    if chart_type == "xbar_r":
        stats = calculate_xbar_r(values, subgroup_size)
    elif chart_type == "xbar_s":
        stats = calculate_xbar_s(values, subgroup_size)
    else:
        stats = calculate_imr(values)
except ValueError as e:
    st.error(f"Cannot compute chart: {e}")
    st.stop()

if len(stats["xbar"]) == 0:
    st.error(
        "Not enough data to form even one complete subgroup. Reduce the subgroup size or upload more rows."
    )
    st.stop()

try:
    cap = calculate_capability(values, stats["xbar_bar"], stats["sigma_st"], USL, LSL)
except ValueError as e:
    st.error(f"Capability error: {e}")
    cap = {
        "Cp": None,
        "Cpk": None,
        "Pp": None,
        "Ppk": None,
        "sigma_st": stats["sigma_st"],
        "sigma_lt": None,
    }


def fmt_cap(v):
    return f"{v:.3f}" if v is not None else "N/A"


# --- Stats rows ---
st.caption("CAPABILITY INDICES")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Cp",  fmt_cap(cap["Cp"]))
col2.metric("Cpk", fmt_cap(cap["Cpk"]))
col3.metric("Pp",  fmt_cap(cap["Pp"]))
col4.metric("Ppk", fmt_cap(cap["Ppk"]))

st.divider()
st.caption("PROCESS STATISTICS")
s1, s2, s3, s4, s5, s6 = st.columns(6)
s1.metric("Mean (X̄)",    f"{stats['xbar_bar']:.4f}")
s2.metric("Sigma ST",     fmt_cap(cap["sigma_st"]))
s3.metric("Sigma LT",     fmt_cap(cap["sigma_lt"]))
s4.metric("Min",          f"{values.min():.4f}")
s5.metric("Max",          f"{values.max():.4f}")
s6.metric("Observations", str(len(values)))
st.divider()

inferences = generate_inferences(stats, cap, USL, LSL)
st.caption("PROCESS INFERENCES")
for b in inferences["bullets"]:
    st.markdown(f"{b['icon']} {b['text']}")
st.info(inferences["narrative"])
st.divider()

# --- Chart ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7))

xbar = stats["xbar"]
sub_stat = stats["sub_stat"]
xbar_bar = stats["xbar_bar"]
x = range(len(xbar))
x2 = range(len(sub_stat))

ax1.plot(x, xbar, marker="o", color="#0078E6", markersize=4, label=column)
ax1.axhline(xbar_bar, color="green", linewidth=1.5, label="CL")
ax1.axhline(stats["UCL_xbar"], color="red", linewidth=1.5, linestyle="--", label="UCL")
ax1.axhline(stats["LCL_xbar"], color="red", linewidth=1.5, linestyle="--", label="LCL")
ax1.axhline(USL, color="darkred", linewidth=2, linestyle="-", label="USL")
ax1.axhline(LSL, color="darkred", linewidth=2, linestyle="-", label="LSL")
ax1.fill_between(x, stats["LCL_xbar"], stats["UCL_xbar"], alpha=0.08, color="green")
ax1.fill_between(x, stats["UCL_xbar"], USL, alpha=0.08, color="yellow")
ax1.fill_between(x, LSL, stats["LCL_xbar"], alpha=0.08, color="yellow")
_chart_title = {
    "xbar_r": "X-bar / R Chart",
    "xbar_s": "X-bar / S Chart",
    "im_r": "Individuals / Moving Range (I-MR) Chart",
}
ax1.set_title(f"{_chart_title[chart_type]} — {column}")
ax1.set_ylabel(column)
ax1.legend(loc="upper right", fontsize=7)

stats_text = (
    f"n={subgroup_size} Cp={fmt_cap(cap['Cp'])}  Cpk={fmt_cap(cap['Cpk'])}\n"
    f"Pp={fmt_cap(cap['Pp'])}  Ppk={fmt_cap(cap['Ppk'])}"
)
ax1.text(
    0.01,
    0.97,
    stats_text,
    transform=ax1.transAxes,
    fontsize=8,
    verticalalignment="top",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
)

ax2.plot(
    x2, sub_stat, marker="o", color="purple", markersize=4, label=stats["sub_label"]
)
ax2.axhline(np.nanmean(sub_stat), color="green", linewidth=1.5, label="CL")
ax2.axhline(stats["UCL_R"], color="red", linewidth=1.5, linestyle="--", label="UCL")
ax2.axhline(stats["LCL_R"], color="red", linewidth=1.5, linestyle="--", label="LCL")
ax2.set_title(f"{stats['sub_label']} Chart")
ax2.set_ylabel(stats["sub_label"])
ax2.legend(loc="upper right", fontsize=7)

plt.tight_layout()
st.pyplot(fig)


try:
    excel_buf = build_excel(
        fig, stats, cap, column, chart_type, subgroup_size, USL, LSL, report_title
    )
except Exception as e:
    st.warning(f"Excel export unavailable: {e}")
    excel_buf = None

try:
    pdf_buf = build_pdf(
        fig, stats, cap, column, chart_type, subgroup_size, USL, LSL, values, inferences, report_title
    )
except Exception as e:
    st.warning(f"PDF export unavailable: {e}")
    pdf_buf = None

st.divider()
st.markdown("#### Download Reports")
_, dl_col1, dl_col2, _ = st.columns([1, 2, 2, 1])
if excel_buf:
    dl_col1.download_button(
        label="📊  Download Excel Report",
        data=excel_buf,
        file_name="spc_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
if pdf_buf:
    dl_col2.download_button(
        label="📄  Download PDF Report",
        data=pdf_buf,
        file_name="spc_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

st.divider()
st.markdown(
    "<div style='text-align: center; color: #98B1BE; font-size: 0.85rem;'>"
    "Built by <strong>Nidhin Dileepkumar</strong> · Open Source · "
    "Questions or feedback? "
    "<a href='https://github.com/crackcode09/spc-control-chart-tool' style='color: #0078E6;'>View on GitHub</a>"
    "</div>",
    unsafe_allow_html=True,
)
