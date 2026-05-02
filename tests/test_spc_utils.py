import numpy as np
import pytest
from spc_utils import (
    anderson_darling_test,
    calculate_capability,
    calculate_imr,
    calculate_xbar_r,
    calculate_xbar_s,
)

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

def test_anderson_darling_normal_data_passes():
    rng = np.random.default_rng(42)
    data = rng.normal(loc=10.0, scale=2.0, size=200)
    result = anderson_darling_test(data)
    assert set(result.keys()) == {"A2", "A2_star", "p_value", "n", "alpha", "is_normal"}
    assert result["n"] == 200
    assert 0.0 <= result["p_value"] <= 1.0
    assert result["is_normal"] is True
    assert result["p_value"] > 0.05


def test_anderson_darling_non_normal_data_fails():
    rng = np.random.default_rng(7)
    data = rng.exponential(scale=1.0, size=200)
    result = anderson_darling_test(data)
    assert result["is_normal"] is False
    assert result["p_value"] < 0.05
    assert result["A2"] > 1.0


def test_anderson_darling_matches_screenshot_signal():
    # bimodal mixture -> strongly non-normal, should mirror banner: A^2 large, p<0.05
    rng = np.random.default_rng(123)
    data = np.concatenate([rng.normal(0, 1, 100), rng.normal(8, 1, 100)])
    result = anderson_darling_test(data)
    assert result["A2"] > 1.0
    assert result["p_value"] < 0.05
    assert result["is_normal"] is False


def test_anderson_darling_raises_on_small_sample():
    with pytest.raises(ValueError):
        anderson_darling_test(np.array([1.0, 2.0, 3.0]))


def test_anderson_darling_handles_nan():
    rng = np.random.default_rng(1)
    data = rng.normal(0, 1, 50)
    data_with_nan = np.concatenate([data, [np.nan, np.nan]])
    result = anderson_darling_test(data_with_nan)
    assert result["n"] == 50


def test_anderson_darling_runs_on_spc_values():
    result = anderson_darling_test(VALUES)
    assert "A2" in result
    assert "p_value" in result


def test_auto_select_chart_type():
    from spc_utils import auto_select_chart_type
    assert auto_select_chart_type(2) == 'xbar_r'
    assert auto_select_chart_type(8) == 'xbar_r'
    assert auto_select_chart_type(9) == 'xbar_s'
    assert auto_select_chart_type(15) == 'xbar_s'
