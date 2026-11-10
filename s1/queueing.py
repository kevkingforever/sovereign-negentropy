"""Baselines P0, P1, Q1, Q2 (Section 6).

DECISION NEEDED BEFORE FREEZE (reviewer item 3). The registration says arrival
and service rates are estimated from the last 6 windows but does not say how
service time is observed. D1 and D2 record only total latency, not service time.
Two estimators are implemented so the choice can be made and written down:

  "sojourn":  treat the mean observed latency m as the mean sojourn time.
              M/M/1 then gives mu - lambda = 1 / m, so Q1 = ln(100) * m.
  "service":  treat observed latency as the service time. Then mu = 1 / m and
              Q1 = ln(100) / (mu - lambda), with the horizon returned when
              lambda >= mu. On public blockchain data this is almost always the
              horizon, so it is usually a constant feature.

Q2 uses the Pollaczek Khinchine mean with service moments m and m2 taken from
observed latency, times ln(100); horizon when rho >= 1.
"""
import math

import numpy as np

LN100 = math.log(100.0)


def q1(lam: float, m: float, horizon: float, estimator: str = "sojourn") -> float:
    if not (m > 0) or not np.isfinite(m):
        return float("nan")
    if estimator == "sojourn":
        return min(LN100 * m, horizon)
    mu = 1.0 / m
    if lam >= mu:
        return horizon
    return min(LN100 / (mu - lam), horizon)


def q2(lam: float, m: float, m2: float, horizon: float) -> float:
    if not (m > 0) or not np.isfinite(m) or not np.isfinite(m2):
        return float("nan")
    rho = lam * m
    if rho >= 1.0:
        return horizon
    return min(LN100 * (m + lam * m2 / (2.0 * (1.0 - rho))), horizon)


def ewma(values, w: float) -> float:
    """P1. Exponentially weighted average, newest value last, weight w on the newest."""
    out = float("nan")
    for v in values:
        if not np.isfinite(v):
            continue
        out = v if not np.isfinite(out) else w * v + (1.0 - w) * out
    return out
