import numpy as np


def generate_inferences(stats: dict, cap: dict, USL: float, LSL: float) -> dict:
    bullets = []
    narrative_parts = []

    cpk = cap.get("Cpk")
    cp = cap.get("Cp")
    ppk = cap.get("Ppk")

    # Rule 1 — Capability (Cpk)
    if cpk is None:
        bullets.append({"icon": "ℹ️", "text": "Capability could not be calculated — check spec limits"})
        narrative_parts.append("Capability could not be assessed (spec limits may equal control limits).")
    elif cpk >= 1.33:
        bullets.append({"icon": "✅", "text": f"Process is capable — Cpk = {cpk:.3f} meets the 1.33 benchmark"})
        narrative_parts.append(f"This process is capable with a Cpk of {cpk:.3f}, meeting the 1.33 benchmark.")
    elif cpk >= 1.0:
        bullets.append({"icon": "⚠️", "text": f"Process is marginally capable — Cpk = {cpk:.3f} (target ≥ 1.33)"})
        narrative_parts.append(f"This process is marginally capable (Cpk = {cpk:.3f}), falling short of the 1.33 target.")
    else:
        bullets.append({"icon": "❌", "text": f"Process is not capable — Cpk = {cpk:.3f}, defects are likely"})
        narrative_parts.append(f"This process is not capable (Cpk = {cpk:.3f}), and defects are likely.")

    # Rule 2 — Centering (Cp vs Cpk)
    if cp is None or cpk is None:
        bullets.append({"icon": "ℹ️", "text": "Centering could not be assessed — spec limits required"})
        narrative_parts.append("Centering could not be assessed.")
    elif cp - cpk > 0.10:
        bullets.append({"icon": "⚠️", "text": f"Process is off-center — Cp ({cp:.3f}) is notably higher than Cpk ({cpk:.3f}), mean is shifted toward one spec limit"})
        narrative_parts.append(f"The process mean is shifted off-center (Cp = {cp:.3f} vs Cpk = {cpk:.3f}).")
    else:
        bullets.append({"icon": "✅", "text": "Process is well-centered within spec limits"})
        narrative_parts.append("The process is well-centered within spec limits.")

    # Rule 3 — Stability (out-of-control points on X-bar chart)
    xbar = np.asarray(stats.get("xbar", []))
    UCL = stats.get("UCL_xbar", float("inf"))
    LCL = stats.get("LCL_xbar", float("-inf"))
    sigma_st = cap.get("sigma_st")
    if len(xbar) == 0 or sigma_st is None:
        bullets.append({"icon": "ℹ️", "text": "Stability could not be assessed"})
        narrative_parts.append("Stability could not be assessed.")
    else:
        ooc = int(np.sum((xbar > UCL) | (xbar < LCL)))
        if ooc == 0:
            bullets.append({"icon": "✅", "text": "Process is stable — no points outside control limits"})
            narrative_parts.append("No out-of-control points were detected on the control chart.")
        elif ooc <= 2:
            bullets.append({"icon": "⚠️", "text": f"{ooc} point(s) outside control limits — investigate for assignable causes"})
            narrative_parts.append(f"{ooc} point(s) outside control limits suggest occasional instability worth investigating.")
        else:
            bullets.append({"icon": "❌", "text": f"{ooc} points outside control limits — process is unstable"})
            narrative_parts.append(f"{ooc} points outside control limits indicate the process is unstable.")

    # Rule 4 — Long-term drift (Cpk vs Ppk)
    if cpk is None or ppk is None:
        bullets.append({"icon": "ℹ️", "text": "Long-term drift could not be assessed"})
        narrative_parts.append("Long-term drift could not be assessed.")
    elif cpk - ppk > 0.15:
        bullets.append({"icon": "⚠️", "text": f"Long-term performance (Ppk = {ppk:.3f}) is notably worse than short-term (Cpk = {cpk:.3f}) — process may have drifted over time"})
        narrative_parts.append(f"Long-term performance (Ppk = {ppk:.3f}) is notably worse than short-term capability (Cpk = {cpk:.3f}), suggesting the process may have drifted.")
    else:
        bullets.append({"icon": "✅", "text": f"Short-term and long-term performance are consistent (Cpk = {cpk:.3f}, Ppk = {ppk:.3f})"})
        narrative_parts.append(f"Short and long-term performance are consistent (Cpk = {cpk:.3f}, Ppk = {ppk:.3f}).")

    return {"bullets": bullets, "narrative": " ".join(narrative_parts)}
