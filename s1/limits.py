"""Limits report. Every run states what it can and cannot show.

The thresholds below are REPORTING thresholds. They never change the registered
decision rule. They only put a plain warning next to the result.
"""
import numpy as np

from .models import GRID

MIN_TRAIN_WINDOWS = 1000
MIN_TEST_WINDOWS = 200
COLLAPSE_REL_DIFF = 0.01     # mean |G1 - G2| / G1 below this: the two models agree
NEAR_CONSTANT_CV = 0.05      # sd / mean of a model's forecasts below this: near constant


def limits(rows_unresolved_share: float, d: dict, te: np.ndarray, tr: np.ndarray, f1, f2,
           params1: dict, params2: dict, block: int, n_test: int, n_dropped_purge: int) -> dict:
    warnings = []
    n_train = int(tr.sum())
    if n_train < MIN_TRAIN_WINDOWS:
        warnings.append(f"low training size: {n_train} windows (reporting threshold {MIN_TRAIN_WINDOWS})")
    if n_test < MIN_TEST_WINDOWS:
        warnings.append(f"low test size: {n_test} windows (reporting threshold {MIN_TEST_WINDOWS})")
    if n_test < 3 * block:
        warnings.append(f"test period spans {n_test / block:.1f} bootstrap blocks ({block} windows each): "
                        "fewer than 3, so the dataset is ineligible under amendment A1")
    rel = float(np.mean(np.abs(f1 - f2) / np.maximum(f1, 1e-12)))
    collapsed = rel < COLLAPSE_REL_DIFF
    if collapsed:
        warnings.append(f"G1 and G2 forecasts nearly identical (mean relative difference {rel:.4f}): collapsed")
    for name, f in (("G1", f1), ("G2", f2)):
        cv = float(np.std(f) / np.mean(f))
        if cv < NEAR_CONSTANT_CV:
            warnings.append(f"{name} forecasts are near constant (sd over mean {cv:.3f})")
    const = []
    for keys, X in ((d["keys1"], d["X1"]), (d["keys2"], d["X2"])):
        for j, c in enumerate(keys):
            col = X[tr][:, j]
            ok = np.isfinite(col)
            if (not ok.any()) or np.nanstd(col) == 0:
                const.append(c)
    const = sorted(set(const))
    if const:
        warnings.append("constant or empty features in training: " + ", ".join(const))
    edge = []
    for tag, p in (("G1", params1), ("G2", params2)):
        for k in ("max_iter", "learning_rate"):
            vals = GRID[k]
            if p[k] in (min(vals), max(vals)):
                edge.append(f"{tag}.{k}={p[k]}")
    if edge:
        warnings.append("selected at the edge of the grid: " + ", ".join(edge))
    if rows_unresolved_share > 0.05:
        warnings.append(f"unresolved share {rows_unresolved_share:.1%}: run the registered 24 hour sensitivity")
    if n_dropped_purge > 0:
        warnings.append(f"{n_dropped_purge} windows dropped by the purge rule")
    return dict(warnings=warnings, collapsed=bool(collapsed), mean_rel_diff=rel,
                constant_features=const, unresolved_share=rows_unresolved_share)


def format_limits(lim: dict) -> str:
    if not lim["warnings"]:
        return "Limits: no reporting warnings."
    return "Limits:\n" + "\n".join("  * " + w for w in lim["warnings"])
