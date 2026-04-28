import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from report_utils import build_pdf
from spc_inferences import generate_inferences


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
