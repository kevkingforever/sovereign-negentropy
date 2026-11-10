"""Features at origin k must not change when everything after the origin is deleted."""
import numpy as np

from s1 import windows as wd
from s1.config import Config
from s1.synth import generate

CFG = Config(horizon_s=1800.0, block_s=1800.0, n_boot=200)


def test_no_lookahead():
    rows = generate(7, hours=12, planted=True)
    t0 = rows.arr.min()
    train_end = t0 + 0.6 * (rows.arr.max() - t0)
    w = wd.choose_w(rows, CFG, train_end)
    edges = wd.bin_edges(rows, CFG, train_end)
    full = wd.build(rows, CFG, w, edges, t0=t0)
    for k in (20, 60, 100, full["n"] - 3):
        end = t0 + (k + 1) * w
        keep = rows.arr < end
        comp = np.where(rows.comp[keep] <= end, rows.comp[keep], np.nan)  # future completions unknown
        cut = wd.Rows(rows.arr[keep], comp)
        part = wd.build(cut, CFG, w, edges, t0=t0, n_windows=k + 1)
        a1, a2 = wd.features(full, CFG, k)
        b1, b2 = wd.features(part, CFG, k)
        for key in a2:
            va, vb = a2[key], b2[key]
            assert (np.isnan(va) and np.isnan(vb)) or np.isclose(va, vb, rtol=1e-9), (k, key, va, vb)
