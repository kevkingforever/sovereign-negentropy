"""Amendment A3 constants for S1 on D2: the window length and the bin edges, from the training period only,
and the unresolved share by day and by hour of day (Amendment A1.1).

What it reads: arrival and inclusion time of every row, from the 28 files that Amendment A2 fixes.
What it uses for the constants: only rows that arrive before the end of the training period
(first 60 percent of the span from the first to the last arrival), with completions at or before that end.
What it reports about all days: the share of rows with no inclusion time, by arrival day and by arrival hour.
No latency from the validation or test period is computed.

Usage:  python3 -m s1.freeze_a3 --folder FOLDER --manifest manifest_d2.json --out a3_constants
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys

import numpy as np

from . import windows as wd
from .adapters import load_d2, sha256_file, verify_manifest
from .config import Config


def _iso(t: float) -> str:
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def unresolved_tables(arr: np.ndarray, comp: np.ndarray):
    """Share of rows without an inclusion time, by arrival day and by arrival hour (UTC)."""
    unres = ~np.isfinite(comp)
    day = (arr // 86400).astype(np.int64)
    hour = ((arr % 86400) // 3600).astype(np.int64)
    d0 = int(day.min())
    nd = int(day.max()) - d0 + 1
    n_day = np.bincount(day - d0, minlength=nd)
    u_day = np.bincount(day - d0, weights=unres, minlength=nd)
    n_hr = np.bincount(hour, minlength=24)
    u_hr = np.bincount(hour, weights=unres, minlength=24)
    days = [dict(day=dt.datetime.fromtimestamp((d0 + i) * 86400, dt.timezone.utc).strftime("%Y-%m-%d"),
                 rows=int(n_day[i]), unresolved=int(u_day[i]),
                 share=float(u_day[i] / n_day[i]) if n_day[i] else float("nan")) for i in range(nd)]
    hours = [dict(hour=h, rows=int(n_hr[h]), unresolved=int(u_hr[h]),
                  share=float(u_hr[h] / n_hr[h]) if n_hr[h] else float("nan")) for h in range(24)]
    return days, hours


def compute(arr: np.ndarray, comp: np.ndarray, cfg: Config) -> dict:
    """The A3 constants from raw arrival and completion arrays (seconds)."""
    days, hours = unresolved_tables(arr, comp)
    t0, t1 = float(arr.min()), float(arr.max())
    span = t1 - t0
    train_end = t0 + cfg.train_frac * span
    val_end = t0 + (cfg.train_frac + cfg.val_frac) * span
    m = arr < train_end
    a_tr = arr[m]
    c_tr, n_clipped = wd.clip_negative(a_tr, comp[m], cfg.latency_floor_s)
    rows = wd.Rows(a_tr, c_tr)
    # medians per candidate W, as the registered rule reads them
    lat = wd.latency(rows, cfg)
    ok = np.isfinite(lat) & (rows.comp <= train_end)
    medians = {}
    for w in cfg.w_candidates_s:
        n = int(np.ceil((train_end - t0) / w))
        idx = np.floor((rows.arr[ok] - t0) / w).astype(int)
        medians[str(int(w))] = float(np.median(np.bincount(idx, minlength=n)))
    W = wd.choose_w(rows, cfg, train_end)
    edges = wd.bin_edges(rows, cfg, train_end)
    # calendar only: how many test windows the split leaves, no outcome used
    block = max(cfg.min_block, int(np.ceil(cfg.block_s / W)))
    n_test_est = int(max(0.0, (t1 - cfg.horizon_s - val_end)) // W)
    return dict(
        t0=t0, t1=t1, train_end=train_end, val_end=val_end,
        t0_utc=_iso(t0), t1_utc=_iso(t1), train_end_utc=_iso(train_end), val_end_utc=_iso(val_end),
        n_rows=int(len(arr)), n_train_rows=int(m.sum()),
        n_train_resolved_by_train_end=int(ok.sum()), n_clipped_training_rows=int(n_clipped),
        median_resolved_per_window=medians, W_seconds=float(W),
        bin_edges_seconds=[float(x) for x in edges],
        block_windows=int(block), min_blocks=cfg.min_blocks, test_windows_estimate=n_test_est,
        eligible_expected=bool(n_test_est >= cfg.min_blocks * block),
        unresolved_by_day=days, unresolved_by_hour=hours)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--folder", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", default="a3_constants")
    a = ap.parse_args(argv)
    cfg = Config()
    manifest = json.load(open(a.manifest))
    bad = verify_manifest(a.folder, manifest)
    if bad:
        print("STOP: these files are missing or do not match the manifest:", bad)
        return 2
    print("all", len(manifest["files"]), "files match the manifest")
    d = load_d2(a.folder, manifest)
    res = compute(d["arr"], d["comp"], cfg)
    here = os.path.dirname(os.path.abspath(__file__))
    res["code_sha256"] = {n: sha256_file(os.path.join(here, n))
                          for n in ("adapters.py", "freeze_a3.py", "windows.py", "config.py")}
    res["manifest_sha256"] = sha256_file(a.manifest)
    res["inclusion_field_counts"] = dict(
        empty=int(sum(f["n_empty"] for f in d["per_file"])),
        zero_or_negative=int(sum(f["n_nonpositive"] for f in d["per_file"])))
    res["created_utc"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(a.out + ".json", "w") as f:
        json.dump(res, f, indent=2)
    import csv
    with open(a.out + "_unresolved_by_day.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["day", "rows", "unresolved", "share"]); w.writeheader(); w.writerows(res["unresolved_by_day"])
    with open(a.out + "_unresolved_by_hour.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["hour", "rows", "unresolved", "share"]); w.writeheader(); w.writerows(res["unresolved_by_hour"])

    print()
    print("first arrival :", res["t0_utc"])
    print("last arrival  :", res["t1_utc"])
    print("training ends :", res["train_end_utc"])
    print("validation ends:", res["val_end_utc"])
    print("rows total    :", res["n_rows"], " training rows:", res["n_train_rows"])
    print("training rows clipped (completion before arrival):", res["n_clipped_training_rows"])
    print("median resolved per window, by candidate W (seconds):", res["median_resolved_per_window"])
    print("CHOSEN W (seconds):", res["W_seconds"])
    print("bin edges (seconds):", [round(x, 6) for x in res["bin_edges_seconds"]])
    print("block (windows):", res["block_windows"], " test windows (estimate):", res["test_windows_estimate"],
          " eligible expected:", res["eligible_expected"])
    print("inclusion field: empty", res["inclusion_field_counts"]["empty"],
          " zero or negative", res["inclusion_field_counts"]["zero_or_negative"])
    print()
    print("unresolved share by arrival day (UTC)")
    for r in res["unresolved_by_day"]:
        print(f'  {r["day"]}  rows {r["rows"]:>8}  unresolved {r["unresolved"]:>7}  share {r["share"]:.4f}')
    print("unresolved share by arrival hour (UTC)")
    for r in res["unresolved_by_hour"]:
        print(f'  {r["hour"]:02d}:00  rows {r["rows"]:>8}  unresolved {r["unresolved"]:>7}  share {r["share"]:.4f}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
