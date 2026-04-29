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
    11: {"A2": 0.285, "D3": 0.256, "D4": 1.744, "A3": 0.928, "B3": 0.322, "B4": 1.678},
    12: {"A2": 0.266, "D3": 0.283, "D4": 1.717, "A3": 0.886, "B3": 0.354, "B4": 1.646},
    13: {"A2": 0.250, "D3": 0.307, "D4": 1.693, "A3": 0.849, "B3": 0.380, "B4": 1.620},
    14: {"A2": 0.237, "D3": 0.328, "D4": 1.672, "A3": 0.818, "B3": 0.400, "B4": 1.600},
    15: {"A2": 0.225, "D3": 0.347, "D4": 1.653, "A3": 0.789, "B3": 0.420, "B4": 1.580},
    16: {"A2": 0.215, "D3": 0.363, "D4": 1.637, "A3": 0.763, "B3": 0.436, "B4": 1.564},
    17: {"A2": 0.206, "D3": 0.378, "D4": 1.622, "A3": 0.740, "B3": 0.450, "B4": 1.550},
    18: {"A2": 0.197, "D3": 0.391, "D4": 1.609, "A3": 0.719, "B3": 0.462, "B4": 1.538},
    19: {"A2": 0.190, "D3": 0.403, "D4": 1.597, "A3": 0.699, "B3": 0.473, "B4": 1.527},
    20: {"A2": 0.184, "D3": 0.415, "D4": 1.585, "A3": 0.681, "B3": 0.482, "B4": 1.518},
    21: {"A2": 0.178, "D3": 0.425, "D4": 1.575, "A3": 0.664, "B3": 0.491, "B4": 1.509},
    22: {"A2": 0.172, "D3": 0.434, "D4": 1.566, "A3": 0.649, "B3": 0.498, "B4": 1.502},
    23: {"A2": 0.167, "D3": 0.443, "D4": 1.557, "A3": 0.634, "B3": 0.504, "B4": 1.496},
    24: {"A2": 0.163, "D3": 0.451, "D4": 1.549, "A3": 0.621, "B3": 0.509, "B4": 1.491},
    25: {"A2": 0.159, "D3": 0.459, "D4": 1.541, "A3": 0.608, "B3": 0.513, "B4": 1.487},
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
    if n not in CONSTANTS:
        raise ValueError(f"Subgroup size n={n} must be between 2 and 25.")
    if len(values) < n:
        raise ValueError(f"Not enough data: need at least {n} values for subgroup size {n}.")
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
    if n not in CONSTANTS:
        raise ValueError(f"Subgroup size n={n} must be between 2 and 25.")
    if len(values) < n:
        raise ValueError(f"Not enough data: need at least {n} values for subgroup size {n}.")
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
    if len(values) < 2:
        raise ValueError("Need at least 2 values for I-MR chart.")
    R = np.concatenate([[np.nan], np.abs(np.diff(values))])
    xbar_bar = values.mean()
    R_bar = np.nanmean(R)
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
    if len(values) < 2:
        raise ValueError("Need at least 2 values to compute capability.")
    if USL <= LSL:
        raise ValueError(f"USL ({USL}) must be greater than LSL ({LSL}).")
    sigma_lt = np.std(values, ddof=1)
    if sigma_st == 0 or sigma_lt == 0:
        return {'Cp': None, 'Cpk': None, 'Pp': None, 'Ppk': None,
                'sigma_st': sigma_st, 'sigma_lt': sigma_lt}
    return {
        'Cp':  (USL - LSL) / (6 * sigma_st),
        'Cpk': min(USL - xbar_bar, xbar_bar - LSL) / (3 * sigma_st),
        'Pp':  (USL - LSL) / (6 * sigma_lt),
        'Ppk': min(USL - xbar_bar, xbar_bar - LSL) / (3 * sigma_lt),
        'sigma_st': sigma_st,
        'sigma_lt': sigma_lt,
    }
