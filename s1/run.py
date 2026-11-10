"""Run the registered S1 comparison on one dataset (Sections 4 to 7)."""
import numpy as np

from . import windows as wd
from .config import Config
from .limits import limits as _limits
from .models import fit_select
from .queueing import ewma
from .stats import (block_length, circular_block_ci, dataset_support, dm_one_sided, holm,
                    overall_outcome, pinball, rel_improvement)


def make_design(rows: wd.Rows, cfg: Config, use_unresolved_target: bool = False):
    t0 = float(rows.arr.min())
    t1 = float(rows.arr.max())
    span = t1 - t0
    train_end = t0 + cfg.train_frac * span
    val_end = t0 + (cfg.train_frac + cfg.val_frac) * span
    data_end = float(max(t1, np.nanmax(rows.comp)))
    w = wd.choose_w(rows, cfg, train_end)
    edges = wd.bin_edges(rows, cfg, train_end)
    raw = wd.build(rows, cfg, w, edges, t0=t0)
    tgt_series = raw["target_unres"] if use_unresolved_target else raw["target"]

    keys1 = keys2 = None
    X1, X2, y, split, ends, p0, p1 = [], [], [], [], [], [], []
    h = cfg.horizon_s if cfg.purge else 0.0
    for k in range(cfg.lags - 1, raw["n"] - 1):
        tk = tgt_series[k + 1]
        if not np.isfinite(tk):
            continue
        start = t0 + (k + 1) * w
        end = start + w
        if end <= train_end - h:
            s = "train"
        elif start >= train_end and end <= val_end - h:
            s = "val"
        elif start >= val_end and end + cfg.horizon_s <= data_end:
            s = "test"
        else:
            continue
        g1, g2 = wd.features(raw, cfg, k)
        if keys1 is None:
            keys1, keys2 = list(g1), list(g2)
        X1.append([g1[c] for c in keys1]); X2.append([g2[c] for c in keys2])
        y.append(tk); split.append(s); ends.append(end)
        p0.append(raw["q99"][k]); p1.append(ewma(raw["q99"][:k + 1], cfg.ewma_weight))
    return dict(X1=np.array(X1), X2=np.array(X2), y=np.array(y), split=np.array(split),
                keys1=keys1, keys2=keys2, p0=np.array(p0), p1=np.array(p1), w=w, edges=edges,
                raw=raw, t0=t0, train_end=train_end, val_end=val_end, data_end=data_end,
                q1=np.array([r[keys1.index("q1")] for r in X1]),
                q2=np.array([r[keys1.index("q2")] for r in X1]))


def run_dataset(rows: wd.Rows, cfg: Config, use_unresolved_target: bool = False) -> dict:
    d = make_design(rows, cfg, use_unresolved_target)
    s = d["split"]
    tr, va, te = s == "train", s == "val", s == "test"
    if te.sum() < 5 or tr.sum() < 20 or va.sum() < 5:
        raise ValueError(f"too few windows: train {tr.sum()}, val {va.sum()}, test {te.sum()}")
    m1, p1, v1 = fit_select(d["X1"][tr], d["y"][tr], d["X1"][va], d["y"][va], cfg)
    m2, p2, v2 = fit_select(d["X2"][tr], d["y"][tr], d["X2"][va], d["y"][va], cfg)
    f1, f2 = m1.predict(d["X1"][te]), m2.predict(d["X2"][te])
    y = d["y"][te]
    l1, l2 = pinball(y, f1, cfg.tau), pinball(y, f2, cfg.tau)
    r = rel_improvement(l1, l2)
    dm = dm_one_sided(l1, l2)
    bl = block_length(d["w"], cfg)
    lo, hi = circular_block_ci(l1, l2, bl, cfg.n_boot, cfg.alpha, cfg.seed)
    lat = wd.latency(rows, cfg)
    unres = float(np.mean(~np.isfinite(lat)))
    all_usable = int(np.sum([np.isfinite(v) for v in d["raw"]["target"][cfg.lags:]]))
    lim = _limits(unres, d, te, tr, f1, f2, p1, p2, bl, int(te.sum()), max(0, all_usable - len(d["y"])))
    # secondary, descriptive only: the same forecasts scored on the natural log scale
    ll1 = pinball(np.log(y), np.log(np.maximum(f1, 1e-9)), cfg.tau)
    ll2 = pinball(np.log(y), np.log(np.maximum(f2, 1e-9)), cfg.tau)
    log_scale = dict(R=rel_improvement(ll1, ll2), p=dm_one_sided(ll1, ll2)["p"])
    base = {}
    for name, f in (("P0", d["p0"]), ("P1", d["p1"]), ("Q1", d["q1"]), ("Q2", d["q2"])):
        f = f[te]
        ok = np.isfinite(f)
        base[name] = float(pinball(y[ok], f[ok], cfg.tau).mean()) if ok.any() else float("nan")
    return dict(W=d["w"], n_train=int(tr.sum()), n_val=int(va.sum()), n_test=int(te.sum()),
                loss_g1=float(l1.mean()), loss_g2=float(l2.mean()), R=r, ci=(lo, hi),
                dm=dm, p_raw=dm["p"], block=bl, params_g1=p1, params_g2=p2, baselines=base,
                l1=l1, l2=l2, limits=lim, log_scale=log_scale)


def decide(results: dict, cfg: Config) -> dict:
    """results: dataset name to run_dataset output. Applies Holm across datasets, then the three part rule."""
    adj = holm({k: v["p_raw"] for k, v in results.items()})
    support = {k: dataset_support(adj[k], v["R"], v["ci"][0], cfg) for k, v in results.items()}
    return dict(holm_p=adj, support=support, outcome=overall_outcome(support))
