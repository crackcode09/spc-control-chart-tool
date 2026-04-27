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
