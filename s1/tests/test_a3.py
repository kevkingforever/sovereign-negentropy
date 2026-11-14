"""Tests for the D2 adapter and the A3 constants. Synthetic data only."""
import io, json, os, zipfile, tempfile

import numpy as np
import pandas as pd

from s1 import freeze_a3 as fz
from s1.adapters import EXPECTED_HEADER, read_d2_day, sha256_file, verify_manifest
from s1.config import Config

COLS = EXPECTED_HEADER.split(",")


def make_day_zip(path, arr_ms, inc_ms):
    n = len(arr_ms)
    df = pd.DataFrame({c: np.zeros(n, dtype="int64") for c in COLS})
    df["timestamp_ms"] = arr_ms
    df["hash"] = "0xabc"
    df["included_block_timestamp_ms"] = inc_ms
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(os.path.basename(path).replace(".zip", ""), buf.getvalue())


def synth(n_days=4, rate=2.0, seed=3):
    rng = np.random.default_rng(seed)
    t0 = 1_790_000_000.0 - (1_790_000_000.0 % 86400)
    n = int(n_days * 86400 * rate)
    arr = np.sort(t0 + rng.uniform(0, n_days * 86400, n))
    lat = rng.lognormal(1.0, 0.8, n)
    comp = arr + lat
    comp[rng.random(n) < 0.03] = np.nan
    neg = rng.random(n) < 0.005
    comp[neg] = arr[neg] - 0.3
    return arr, comp, t0


def test_read_day_empty_zero_and_units():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "2026-10-16.csv.zip")
    make_day_zip(p, [1_000, 2_000, 3_000, 4_000], [1_500, np.nan, 0, 4_250])
    r = read_d2_day(p)
    assert r["n"] == 4 and r["n_empty"] == 1 and r["n_nonpositive"] == 1
    assert np.allclose(r["arr"], [1.0, 2.0, 3.0, 4.0])
    assert np.isclose(r["comp"][0], 1.5) and np.isnan(r["comp"][1]) and np.isnan(r["comp"][2]) and np.isclose(r["comp"][3], 4.25)


def test_unresolved_tables_add_up():
    arr, comp, _ = synth()
    days, hours = fz.unresolved_tables(arr, comp)
    assert sum(x["rows"] for x in days) == len(arr) == sum(x["rows"] for x in hours)
    assert sum(x["unresolved"] for x in days) == int((~np.isfinite(comp)).sum())
    assert len(hours) == 24


def test_constants_are_sane():
    arr, comp, _ = synth()
    cfg = Config()
    r = fz.compute(arr, comp, cfg)
    assert r["W_seconds"] in cfg.w_candidates_s
    e = np.array(r["bin_edges_seconds"])
    assert len(e) == cfg.k_bins + 1 and np.all(np.diff(e) > 0)
    assert r["n_clipped_training_rows"] > 0
    assert r["train_end"] < r["val_end"] < r["t1"]


def test_constants_do_not_use_validation_or_test_outcomes():
    """Change every completion for rows that arrive after the training end, and every completion that
    falls after the training end. W and the bin edges must not move."""
    arr, comp, _ = synth()
    cfg = Config()
    base = fz.compute(arr, comp, cfg)
    te = base["train_end"]
    comp2 = comp.copy()
    late_arrival = arr >= te
    comp2[late_arrival] = arr[late_arrival] + 5000.0
    after = np.isfinite(comp2) & (comp2 > te) & ~late_arrival
    comp2[after] = comp2[after] + 40000.0          # inside the 24 hour horizon or beyond, all after train end
    other = fz.compute(arr, comp2, cfg)
    assert other["W_seconds"] == base["W_seconds"]
    assert other["bin_edges_seconds"] == base["bin_edges_seconds"]


def test_manifest_mismatch_is_caught_and_main_stops():
    arr, comp, t0 = synth(n_days=2, rate=0.5)
    d = tempfile.mkdtemp()
    entries = []
    for i in range(2):
        m = (arr >= t0 + i * 86400) & (arr < t0 + (i + 1) * 86400)
        p = os.path.join(d, f"2026-10-{16 + i}.csv.zip")
        inc = np.where(np.isfinite(comp[m]), comp[m] * 1000.0, np.nan)
        make_day_zip(p, (arr[m] * 1000).astype("int64"), inc)
        entries.append(dict(file=os.path.basename(p), sha256=sha256_file(p)))
    man = dict(files=entries)
    assert verify_manifest(d, man) == []
    man["files"][1]["sha256"] = "0" * 64
    assert verify_manifest(d, man) == [entries[1]["file"]]
    mp = os.path.join(d, "man.json")
    json.dump(man, open(mp, "w"))
    assert fz.main(["--folder", d, "--manifest", mp, "--out", os.path.join(d, "out")]) == 2


def test_end_to_end_on_synthetic_files():
    arr, comp, t0 = synth(n_days=3, rate=2.0)
    d = tempfile.mkdtemp()
    entries = []
    for i in range(3):
        m = (arr >= t0 + i * 86400) & (arr < t0 + (i + 1) * 86400)
        p = os.path.join(d, f"2026-10-{16 + i}.csv.zip")
        inc = np.where(np.isfinite(comp[m]), np.round(comp[m] * 1000.0), np.nan)
        make_day_zip(p, np.round(arr[m] * 1000).astype("int64"), inc)
        entries.append(dict(file=os.path.basename(p), sha256=sha256_file(p)))
    mp = os.path.join(d, "man.json")
    json.dump(dict(files=entries), open(mp, "w"))
    out = os.path.join(d, "a3")
    assert fz.main(["--folder", d, "--manifest", mp, "--out", out]) == 0
    r = json.load(open(out + ".json"))
    assert r["W_seconds"] in Config().w_candidates_s and r["n_rows"] == len(arr)
    assert os.path.exists(out + "_unresolved_by_day.csv") and os.path.exists(out + "_unresolved_by_hour.csv")
    assert set(r["code_sha256"]) == {"adapters.py", "freeze_a3.py", "windows.py", "config.py"}
