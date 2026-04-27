import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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

try:
    cap = calculate_capability(values, stats["xbar_bar"], stats["sigma_st"], USL, LSL)
except ValueError as e:
    st.error(f"Capability error: {e}")
    cap = {'Cp': None, 'Cpk': None, 'Pp': None, 'Ppk': None, 'sigma_st': stats["sigma_st"], 'sigma_lt': None}

def fmt_cap(v):
    return f"{v:.3f}" if v is not None else "N/A"

# --- Capability metric cards ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Cp",  fmt_cap(cap['Cp']))
col2.metric("Cpk", fmt_cap(cap['Cpk']))
col3.metric("Pp",  fmt_cap(cap['Pp']))
col4.metric("Ppk", fmt_cap(cap['Ppk']))

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

stats_text = (f"n={subgroup_size}  Cp={fmt_cap(cap['Cp'])}  Cpk={fmt_cap(cap['Cpk'])}\n"
              f"Pp={fmt_cap(cap['Pp'])}  Ppk={fmt_cap(cap['Ppk'])}")
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
        ws2.append([i + 1, round(float(xb), 4), round(float(ss), 4) if not np.isnan(ss) else ""])

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
