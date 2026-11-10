"""Synthetic data for testing the machinery. Never used for any claim about the world.

Arrivals are Poisson with a slow cycle and bursts. Latency is lognormal.
  null:    the tail depends only on things the queueing features can see.
  planted: a hidden dispersion state d_t (persistent) sets the lognormal sigma and
           also the NEXT hours' tail scale. Entropy of the latency distribution
           sees d_t before the p99 itself moves. G1 cannot see it.
"""
import numpy as np

from .windows import Rows


def generate(seed: int, hours: float = 24.0, rate: float = 8.0, planted: bool = False,
             step_s: float = 300.0, unresolved_share: float = 0.0,
             d_ar: float = 0.7, lead: int = 2, strength: float = 1.2) -> Rows:
    rng = np.random.default_rng(seed)
    n_steps = int(hours * 3600 / step_s)
    # hidden persistent AR(1) states per step
    z = np.zeros(n_steps); d = np.zeros(n_steps)
    for i in range(1, n_steps):
        z[i] = 0.9 * z[i - 1] + 0.3 * rng.standard_normal()
        d[i] = d_ar * d[i - 1] + 0.7 * rng.standard_normal()
    arr_list, lat_list = [], []
    for i in range(n_steps):
        cyc = 1.0 + 0.4 * np.sin(2 * np.pi * i / (n_steps / 2.0))
        lam = rate * cyc * (1.0 + 0.3 * z[i] ** 2 * 0 + 0.2 * (rng.random() < 0.05))
        n = rng.poisson(lam * step_s)
        a = i * step_s + rng.random(n) * step_s
        base = 60.0 * np.exp(0.5 * cyc + 0.5 * z[i] * 0)   # observable through arrivals and lags
        if planted:
            sigma = 0.6 + 0.5 * np.clip(d[i], -1.2, 1.2)    # dispersion visible in shape
            nxt = d[min(i + lead, n_steps - 1)]               # and drives tail scale shortly after
            scale = base * np.exp(strength * np.clip(nxt, -1.5, 1.5))
        else:
            sigma = 0.8
            scale = base
        lat = scale * np.exp(sigma * rng.standard_normal(n) - 0.5 * sigma ** 2)
        arr_list.append(a); lat_list.append(lat)
    arr = np.concatenate(arr_list); lat = np.concatenate(lat_list)
    comp = arr + lat
    if unresolved_share > 0:
        comp[rng.random(arr.size) < unresolved_share] = np.nan
    o = np.argsort(arr)
    return Rows(arr[o], comp[o])
