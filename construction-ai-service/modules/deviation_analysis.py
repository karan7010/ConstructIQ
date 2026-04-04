def analyze_deviation(estimate: dict, logs: list) -> dict:
    """
    Compare estimated quantities vs aggregated logs.
    
    Args:
        estimate: Material estimation from Phase 4.
        logs: List of log entries from Phase 5.
        
    Returns:
        Analysis results with deviation percentages and alerts.
    """
    # 1. Aggregate usage from logs
    actual = {
        "cement": 0.0,
        "sand": 0.0,
        "bricks": 0.0,
        "labor": 0.0
    }
    
    for log in logs:
        mat = log.get("materialUsage", {})
        actual["cement"] += mat.get("cement", 0)
        actual["sand"] += mat.get("sand", 0)
        actual["bricks"] += mat.get("bricks", 0)
        actual["labor"] += log.get("laborHours", 0)
        
    # 2. Compare with estimate
    est_cement = estimate.get("cementBags", 1) # Avoid div by zero
    est_sand = estimate.get("sandM3", 1)
    est_bricks = estimate.get("bricksCount", 1)
    
    deviations = {
        "cement": round(((actual["cement"] - est_cement) / est_cement) * 100, 2),
        "sand": round(((actual["sand"] - est_sand) / est_sand) * 100, 2),
        "bricks": round(((actual["bricks"] - est_bricks) / est_bricks) * 100, 2)
    }
    
    # 3. Determine status
    status = "normal"
    alerts = []
    
    for material, dev in deviations.items():
        if dev > 20:
            status = "critical"
            alerts.append(f"CRITICAL OVERRUN: {material.capitalize()} usage is {dev}% over estimate!")
        elif dev > 10 and status != "critical":
            status = "warning"
            alerts.append(f"WARNING: {material.capitalize()} usage is {dev}% over estimate.")

    return {
        "actualUsage": actual,
        "deviations": deviations,
        "status": status,
        "alerts": alerts,
        "efficiencyScore": _calculate_efficiency(deviations)
    }

import numpy as np
from typing import Dict, List

def calculate_deviation(estimated: float, actual: float, historical_actuals: List[float]) -> dict:
    if estimated == 0:
        return {
            "estimated": 0,
            "actual": actual,
            "deviationPct": 0,
            "zScore": 0,
            "flagged": False
        }

    deviation_pct = ((actual - estimated) / estimated) * 100

    # Z-score against historical logs for this material
    if len(historical_actuals) >= 3:
        mean = np.mean(historical_actuals)
        std = np.std(historical_actuals)
        z_score = (actual - mean) / std if std > 0 else 0.0
    else:
        z_score = 0.0  # Not enough history yet

    # Flag if EITHER threshold exceeded
    flagged = (abs(deviation_pct) > 20.0) or (z_score > 2.0)

    return {
        "estimated": estimated,
        "actual": actual,
        "deviationPct": round(deviation_pct, 2),
        "zScore": round(z_score, 2),
        "flagged": flagged
    }

def classify_severity(deviations: dict) -> str:
    flagged_count = sum(
        1 for key, val in deviations.items()
        if isinstance(val, dict) and val.get("flagged", False)
    )
    # Critical if any single deviation exceeds 50%
    any_critical = any(
        abs(val.get("deviationPct", 0)) > 50
        for val in deviations.values()
        if isinstance(val, dict)
    )

    if any_critical or flagged_count >= 3:
        return "critical"
    elif flagged_count >= 1:
        return "warning"
    else:
        return "normal"

def check_equipment_idle(hours_used: float, hours_idle: float) -> dict:
    total = hours_used + hours_idle
    ratio = hours_idle / total if total > 0 else 0.0
    return {
        "value": round(ratio, 3),
        "threshold": 0.4,
        "flagged": ratio > 0.4
    }

def analyze_resource_usage(planned: Dict[str, float], actual: Dict[str, float], history: Dict[str, List[float]] = None) -> Dict[str, any]:
    history = history or {}
    results = {}
    for res, planned_val in planned.items():
        actual_val = actual.get(res, 0.0)
        res_history = history.get(res, [])
        results[res] = calculate_deviation(planned_val, actual_val, res_history)
        
    idle_data = check_equipment_idle(actual.get("labor_hours", 0), actual.get("idle_hours", 0))
    results["equipment_idle"] = idle_data
    
    return {
        "overallSeverity": classify_severity(results),
        "breakdown": results
    }

def _calculate_efficiency(deviations: dict) -> int:
    """Returns a score from 0-100 based on resource utilization."""
    avg_dev = sum(abs(v) for v in deviations.values()) / len(deviations)
    score = max(0, 100 - int(avg_dev))
    return score
