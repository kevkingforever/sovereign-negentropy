"""Synthetic lifecycle generator with known ground truth.

Stage delays are lognormal with fixed parameters, so true quantiles are known exactly.
Used by the self checks and by the database benchmark. Standard library only.
"""
from __future__ import annotations

import math
import random

# Median seconds and log scale (sigma) for authentication, routing and transit,
# clearing wait, settlement confirmation.
MEDIANS = (0.05, 0.20, 0.80, 0.15)
SIGMAS = (0.40, 0.50, 0.70, 0.40)
Z99 = 2.3263478740408408  # standard normal 0.99 quantile


def true_quantile(stage: int, q_z: float = Z99) -> float:
    return MEDIANS[stage] * math.exp(SIGMAS[stage] * q_z)


def true_median(stage: int) -> float:
    return MEDIANS[stage]


def lifecycle(rng: random.Random, t0: float, retry_p: float = 0.0, fail_p: float = 0.0):
    """Return a list of (code, ts, retries, failed) for one transaction."""
    events = [(0, t0, 0, False)]
    t = t0
    for s in range(4):
        d = rng.lognormvariate(math.log(MEDIANS[s]), SIGMAS[s])
        retries = 0
        while retry_p > 0.0 and rng.random() < retry_p and retries < 3:
            retries += 1
            d += rng.lognormvariate(math.log(MEDIANS[s]), SIGMAS[s])
        t += d
        failed = (s == 3) and (rng.random() < fail_p)
        events.append((s + 1, t, retries, failed))
    return events


def stream(n_tx: int, rate_per_s: float = 250.0, seed: int = 1, retry_p: float = 0.0, fail_p: float = 0.0):
    """Yield events in order of their timestamp for n_tx transactions arriving as a Poisson process."""
    rng = random.Random(seed)
    t = 0.0
    all_events = []
    for tx in range(n_tx):
        t += rng.expovariate(rate_per_s)
        for code, ts, retries, failed in lifecycle(rng, t, retry_p, fail_p):
            all_events.append((ts, tx, code, retries, failed))
    all_events.sort()
    for ts, tx, code, retries, failed in all_events:
        yield tx, code, ts, retries, failed
