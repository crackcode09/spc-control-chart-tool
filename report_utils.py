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
