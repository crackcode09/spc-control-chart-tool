import numpy as np
import pytest

from spc_inferences import generate_inferences


def _stats(xbar=None, UCL_xbar=10.5, LCL_xbar=9.5):
    return {
        "xbar": np.array(xbar if xbar is not None else [10.0, 10.1, 9.9, 10.2, 10.0]),
        "xbar_bar": 10.0,
        "UCL_xbar": UCL_xbar,
        "LCL_xbar": LCL_xbar,
    }


def _cap(Cp=1.5, Cpk=1.45, Pp=1.42, Ppk=1.42, sigma_st=0.2, sigma_lt=0.25):
    return {"Cp": Cp, "Cpk": Cpk, "Pp": Pp, "Ppk": Ppk, "sigma_st": sigma_st, "sigma_lt": sigma_lt}


# Rule 1 — Capability

def test_rule1_capable():
    result = generate_inferences(_stats(), _cap(Cpk=1.45), 11.0, 9.0)
    assert result["bullets"][0]["icon"] == "✅"
    assert "capable" in result["bullets"][0]["text"].lower()


def test_rule1_marginal():
    result = generate_inferences(_stats(), _cap(Cpk=1.10), 11.0, 9.0)
    assert result["bullets"][0]["icon"] == "⚠️"
    assert "marginal" in result["bullets"][0]["text"].lower()


def test_rule1_not_capable():
    result = generate_inferences(_stats(), _cap(Cpk=0.85), 11.0, 9.0)
    assert result["bullets"][0]["icon"] == "❌"


def test_rule1_none_cpk():
    cap = {"Cp": None, "Cpk": None, "Pp": None, "Ppk": None, "sigma_st": 0.2, "sigma_lt": None}
    result = generate_inferences(_stats(), cap, 11.0, 9.0)
    assert result["bullets"][0]["icon"] == "ℹ️"


# Rule 2 — Centering

def test_rule2_off_center():
    result = generate_inferences(_stats(), _cap(Cp=1.6, Cpk=1.4), 11.0, 9.0)
    assert result["bullets"][1]["icon"] == "⚠️"
    assert "center" in result["bullets"][1]["text"].lower()


def test_rule2_centered():
    result = generate_inferences(_stats(), _cap(Cp=1.5, Cpk=1.46), 11.0, 9.0)
    assert result["bullets"][1]["icon"] == "✅"


def test_rule2_none():
    cap = {"Cp": None, "Cpk": None, "Pp": 1.3, "Ppk": 1.2, "sigma_st": 0.2, "sigma_lt": 0.25}
    result = generate_inferences(_stats(), cap, 11.0, 9.0)
    assert result["bullets"][1]["icon"] == "ℹ️"


# Rule 3 — Stability

def test_rule3_stable():
    result = generate_inferences(_stats(xbar=[10.0, 10.1, 9.9, 10.2, 10.3]), _cap(), 11.0, 9.0)
    assert result["bullets"][2]["icon"] == "✅"


def test_rule3_warning_1_to_2():
    # one point above UCL=10.5
    result = generate_inferences(_stats(xbar=[10.0, 10.7, 9.9, 10.1, 10.0]), _cap(), 11.0, 9.0)
    assert result["bullets"][2]["icon"] == "⚠️"


def test_rule3_unstable_3plus():
    # three points outside limits
    result = generate_inferences(_stats(xbar=[11.0, 10.7, 9.2, 10.1, 10.0]), _cap(), 11.0, 9.0)
    assert result["bullets"][2]["icon"] == "❌"


# Rule 4 — Long-term drift

def test_rule4_drift():
    result = generate_inferences(_stats(), _cap(Cpk=1.45, Ppk=1.20), 11.0, 9.0)
    assert result["bullets"][3]["icon"] == "⚠️"
    assert "long-term" in result["bullets"][3]["text"].lower()


def test_rule4_consistent():
    result = generate_inferences(_stats(), _cap(Cpk=1.45, Ppk=1.43), 11.0, 9.0)
    assert result["bullets"][3]["icon"] == "✅"


# Edge cases

def test_all_none_cap_no_exception():
    cap = {"Cp": None, "Cpk": None, "Pp": None, "Ppk": None, "sigma_st": None, "sigma_lt": None}
    result = generate_inferences(_stats(xbar=[]), cap, 11.0, 9.0)
    assert len(result["bullets"]) == 4
    assert all(b["icon"] == "ℹ️" for b in result["bullets"])


def test_narrative_is_nonempty_string():
    result = generate_inferences(_stats(), _cap(), 11.0, 9.0)
    assert isinstance(result["narrative"], str)
    assert len(result["narrative"]) > 20


def test_returns_four_bullets():
    result = generate_inferences(_stats(), _cap(), 11.0, 9.0)
    assert len(result["bullets"]) == 4
