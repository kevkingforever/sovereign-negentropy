"""Loss, Diebold Mariano, circular block bootstrap, Holm (Section 7)."""
import math

import numpy as np
from scipy.stats import norm


def pinball(y, f, tau: float) -> np.ndarray:
    e = np.asarray(y, float) - np.asarray(f, float)
    return np.maximum(tau * e, (tau - 1.0) * e)


def rel_improvement(loss1, loss2) -> float:
    """R = 1 - mean(loss G2) / mean(loss G1)."""
    return 1.0 - float(np.mean(loss2)) / float(np.mean(loss1))


def newey_west_lrv(d: np.ndarray, bandwidth: int) -> float:
    d = d - d.mean()
    t = len(d)
    lrv = float(d @ d) / t
    for lag in range(1, min(bandwidth, t - 1) + 1):
        wgt = 1.0 - lag / (bandwidth + 1.0)
        lrv += 2.0 * wgt * float(d[lag:] @ d[:-lag]) / t
    return lrv


def dm_one_sided(loss1, loss2) -> dict:
    """H1: G2 has lower loss than G1. Bandwidth is ceil(4 * (T / 100) ** (2 / 9))."""
    d = np.asarray(loss1, float) - np.asarray(loss2, float)
    t = len(d)
    bw = int(math.ceil(4.0 * (t / 100.0) ** (2.0 / 9.0)))
    lrv = newey_west_lrv(d, bw)
    if lrv <= 0:
        return dict(stat=float("nan"), p=1.0, bandwidth=bw, T=t)
    stat = float(d.mean() / math.sqrt(lrv / t))
    return dict(stat=stat, p=float(1.0 - norm.cdf(stat)), bandwidth=bw, T=t)


def block_length(window_s: float, cfg) -> int:
    return max(cfg.min_block, int(math.ceil(cfg.block_s / window_s)))


def circular_block_ci(loss1, loss2, block: int, n_boot: int, alpha: float, seed: int) -> tuple:
    """Percentile interval for R from a circular block bootstrap of the paired losses."""
    l1 = np.asarray(loss1, float); l2 = np.asarray(loss2, float)
    t = len(l1)
    block = min(block, t)
    nb = int(math.ceil(t / block))
    rng = np.random.default_rng(seed)
    out = np.empty(n_boot)
    step = 2000
    offs = np.arange(block)
    for s in range(0, n_boot, step):
        m = min(step, n_boot - s)
        starts = rng.integers(0, t, size=(m, nb))
        idx = ((starts[:, :, None] + offs[None, None, :]) % t).reshape(m, -1)[:, :t]
        out[s:s + m] = 1.0 - l2[idx].mean(axis=1) / l1[idx].mean(axis=1)
    return float(np.quantile(out, alpha / 2)), float(np.quantile(out, 1 - alpha / 2))


def holm(pvals: dict) -> dict:
    """Holm step down adjusted p values."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    adj = {}
    run = 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        adj[k] = run
    return adj


def dataset_support(adj_p: float, r: float, ci_lo: float, cfg) -> bool:
    return bool(adj_p < cfg.alpha and r >= cfg.r_min and ci_lo > 0.0)


def overall_outcome(support: dict) -> str:
    n = sum(bool(v) for v in support.values())
    if n == len(support):
        return "Supported"
    if n == 0:
        return "Not supported"
    return "Inconclusive"
