"""Windowing, entropy and feature construction (Sections 4.2, 4.3, 6).

Information rule: the features for origin k use only arrivals before the end of
window k and completions with a timestamp at or before the end of window k.
tests/test_no_lookahead.py proves this by deleting everything after the origin.
"""
from dataclasses import dataclass

import numpy as np

from .config import Config
from .queueing import q1, q2


@dataclass
class Rows:
    arr: np.ndarray                 # arrival time, seconds
    comp: np.ndarray                # completion time, nan if none
    fee: np.ndarray | None = None   # optional fee rate at arrival

    def __post_init__(self):
        self.arr = np.asarray(self.arr, float)
        self.comp = np.asarray(self.comp, float)
        if self.fee is not None:
            self.fee = np.asarray(self.fee, float)
        bad = np.isfinite(self.comp) & (self.comp < self.arr)
        if bad.any():
            raise ValueError(f"{int(bad.sum())} rows complete before they arrive. "
                             "Apply the amendment A1 latency floor in the adapter (clip_negative).")


def clip_negative(arr, comp, floor_s: float = 0.001):
    """AMENDMENT A1. Completion before arrival is timestamp noise, not a faster transaction.
    The latency is set to floor_s instead of dropping the row, because dropping rows by the value
    of the outcome biases the distribution. Returns (comp, number_clipped)."""
    arr = np.asarray(arr, float); comp = np.asarray(comp, float)
    bad = np.isfinite(comp) & (comp < arr + floor_s)
    comp = np.where(bad, arr + floor_s, comp)
    return comp, int(bad.sum())


def latency(rows: Rows, cfg: Config):
    """Latency with unresolved (no completion or beyond horizon) set to nan."""
    lat = rows.comp - rows.arr
    lat = np.where(np.isfinite(lat) & (lat <= cfg.horizon_s), lat, np.nan)
    return lat


def choose_w(rows: Rows, cfg: Config, train_end: float) -> float:
    """Smallest candidate W whose median training window holds enough resolved transactions."""
    lat = latency(rows, cfg)
    t0 = rows.arr.min()
    m = (rows.arr < train_end) & np.isfinite(lat) & (rows.comp <= train_end)
    for w in cfg.w_candidates_s:
        n = int(np.ceil((train_end - t0) / w))
        idx = np.floor((rows.arr[m] - t0) / w).astype(int)
        counts = np.bincount(idx, minlength=n)
        if np.median(counts) >= cfg.min_resolved_per_window:
            return w
    return cfg.w_candidates_s[-1]


def bin_edges(rows: Rows, cfg: Config, train_end: float) -> np.ndarray:
    """K log spaced bins between the 0.1th and 99.9th percentiles of training latencies. Frozen once."""
    lat = latency(rows, cfg)
    m = (rows.arr < train_end) & np.isfinite(lat) & (rows.comp <= train_end)
    x = lat[m]
    x = x[x > 0]
    lo, hi = np.percentile(x, [cfg.bin_lo_pct, cfg.bin_hi_pct])
    return np.exp(np.linspace(np.log(lo), np.log(hi), cfg.k_bins + 1))


def entropy_nats(counts: np.ndarray) -> float:
    n = counts.sum()
    if n <= 0:
        return float("nan")
    p = counts[counts > 0] / n
    return float(-(p * np.log(p)).sum())


def _bin_index(x: np.ndarray, edges: np.ndarray) -> np.ndarray:
    k = len(edges) - 1
    return np.clip(np.searchsorted(edges, x, side="right") - 1, 0, k - 1)


def build(rows: Rows, cfg: Config, w: float, edges: np.ndarray, t0: float | None = None,
          n_windows: int | None = None) -> dict:
    """Per window raw series. Index k is window k, covering [t0 + k*w, t0 + (k+1)*w)."""
    if t0 is None:
        t0 = float(rows.arr.min())
    lat = latency(rows, cfg)
    ia = np.floor((rows.arr - t0) / w).astype(int)
    n = int(ia.max()) + 1 if n_windows is None else n_windows
    keep = (ia >= 0) & (ia < n)
    arrivals = np.bincount(ia[keep], minlength=n).astype(float)

    res = np.isfinite(rows.comp)
    ic = np.floor((rows.comp - t0) / w)
    ic = np.where(res & np.isfinite(ic), ic, -1).astype(int)
    comp_ok = np.isfinite(lat) & (ic >= 0) & (ic < n)

    completed = np.bincount(ic[comp_ok], minlength=n).astype(float)
    q50 = np.full(n, np.nan); q90 = q50.copy(); q99 = q50.copy()
    h = q50.copy(); mean_l = q50.copy(); m2_l = q50.copy()
    order = np.argsort(ic[comp_ok], kind="stable")
    li = lat[comp_ok][order]
    bounds = np.concatenate([[0], np.cumsum(completed.astype(int))])
    for k in range(n):
        x = li[bounds[k]:bounds[k + 1]]
        if x.size:
            q50[k], q90[k], q99[k] = np.quantile(x, [0.5, 0.9, 0.99])
            h[k] = entropy_nats(np.bincount(_bin_index(x, edges), minlength=len(edges) - 1))
            mean_l[k] = x.mean(); m2_l[k] = (x ** 2).mean()

    # pending at the end of window k: arrived by then, not completed by then
    pending = np.cumsum(arrivals) - np.cumsum(completed)

    fee50 = fee90 = None
    if rows.fee is not None:
        fee50 = np.full(n, np.nan); fee90 = fee50.copy()
        o = np.argsort(ia[keep], kind="stable")
        fv = rows.fee[keep][o]
        fb = np.concatenate([[0], np.cumsum(arrivals.astype(int))])
        for k in range(n):
            x = fv[fb[k]:fb[k + 1]]
            x = x[np.isfinite(x)]
            if x.size:
                fee50[k], fee90[k] = np.quantile(x, [0.5, 0.9])

    # target for window k: 0.99 quantile of latency among arrivals in window k, resolved only
    tgt = np.full(n, np.nan); tgt_unres = np.full(n, np.nan)
    oa = np.argsort(ia[keep], kind="stable")
    la = lat[keep][oa]
    ab = np.concatenate([[0], np.cumsum(arrivals.astype(int))])
    for k in range(n):
        x = la[ab[k]:ab[k + 1]]
        r = x[np.isfinite(x)]
        if r.size:
            tgt[k] = np.quantile(r, cfg.tau)
        if x.size:
            tgt_unres[k] = np.quantile(np.where(np.isfinite(x), x, cfg.horizon_s), cfg.tau)
    return dict(t0=t0, w=w, n=n, arrivals=arrivals, completed=completed, q50=q50, q90=q90,
                q99=q99, h=h, mean_l=mean_l, m2_l=m2_l, pending=pending, fee50=fee50,
                fee90=fee90, target=tgt, target_unres=tgt_unres)


def _lagged(x: np.ndarray, k: int, lags: int) -> np.ndarray:
    out = np.full(lags, np.nan)
    for j in range(lags):
        if k - j >= 0:
            out[j] = x[k - j]
    return out


def features(raw: dict, cfg: Config, k: int) -> tuple[dict, dict]:
    """G1 and G2 feature dicts for forecast origin k (end of window k)."""
    w = raw["w"]
    g1 = {}
    for name in ("arrivals", "completed", "q50", "q90", "q99"):
        for j, v in enumerate(_lagged(raw[name], k, cfg.lags)):
            g1[f"{name}_l{j}"] = v / w if name == "arrivals" else v
    g1["pending"] = raw["pending"][k]
    for name in ("fee50", "fee90"):
        if raw[name] is not None:
            for j, v in enumerate(_lagged(raw[name], k, cfg.lags)):
                g1[f"{name}_l{j}"] = v
    lo = max(0, k - cfg.lags + 1)
    lam = raw["arrivals"][lo:k + 1].sum() / (w * (k + 1 - lo))
    cnt = raw["completed"][lo:k + 1]
    tot = cnt.sum()
    if tot > 0:
        m = float(np.nansum(raw["mean_l"][lo:k + 1] * cnt) / tot)
        m2 = float(np.nansum(raw["m2_l"][lo:k + 1] * cnt) / tot)
    else:
        m = m2 = float("nan")
    g1["q1"] = q1(lam, m, cfg.horizon_s, cfg.q_estimator)
    g1["q2"] = q2(lam, m, m2, cfg.horizon_s)
    hl = _lagged(raw["h"], k, cfg.lags)
    g2 = dict(g1)
    for j, v in enumerate(hl):
        g2[f"h_l{j}"] = v
    g2["h_mean6"] = float(np.nanmean(hl)) if np.isfinite(hl).any() else float("nan")
    g2["h_diff"] = hl[0] - hl[1] if np.isfinite(hl[:2]).all() else float("nan")
    return g1, g2
