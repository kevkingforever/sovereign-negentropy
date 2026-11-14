"""Run script, A3 constants check and the secondary analyses. Synthetic data only."""
import numpy as np
import pytest

from s1 import run_d2 as rd
from s1 import windows as wd
from s1.config import Config
from s1.freeze_a3 import compute

CFG = Config(n_boot=300, w_candidates_s=(60.0, 300.0, 600.0, 1800.0, 3600.0))


def synth(n_days=6, rate=1.5, seed=5):
    rng = np.random.default_rng(seed)
    t0 = 1_790_000_000.0 - (1_790_000_000.0 % 86400)
    n = int(n_days * 86400 * rate)
    arr = np.sort(t0 + rng.uniform(0, n_days * 86400, n))
    lat = rng.lognormal(1.2, 0.9, n)
    comp = arr + lat
    comp[rng.random(n) < 0.02] = np.nan
    neg = rng.random(n) < 0.01
    comp[neg] = arr[neg] - 0.2
    val = rng.lognormal(10, 2, n)
    return arr, comp, val


def test_primary_run_with_registered_constants_and_secondaries():
    arr, comp, val = synth()
    a3 = compute(arr, comp, CFG)
    out = rd.run_all(arr, comp, val, CFG, a3, log=lambda *_: None)
    p = out["primary"]
    assert p["W"] == a3["W_seconds"]
    assert out["decision"]["outcome"] in ("Supported", "Not supported", "Inconclusive", "Not testable")
    assert set(out["secondary"]) == {"drop_clipped_rows", "unresolved_as_24h", "value_weighted_entropy"}
    assert "R" in p["surge"] or p["surge"]["n"] < 5
    assert 0.0 <= p["brier"]["G1"] <= 1.0 and 0.0 <= p["brier"]["G2"] <= 1.0
    assert out["n_clipped"] > 0
    assert "G1" in rd.report(out, "test")


def test_stops_if_recomputed_constants_differ_from_a3():
    arr, comp, val = synth()
    a3 = compute(arr, comp, CFG)
    a3["bin_edges_seconds"][3] *= 1.001
    with pytest.raises(ValueError, match="Amendment A3"):
        rd.run_all(arr, comp, val, CFG, a3, log=lambda *_: None)


def test_value_weighted_entropy_equals_plain_when_weights_equal():
    arr, comp, val = synth(n_days=2, rate=1.0)
    comp_c, _ = wd.clip_negative(arr, comp, 0.001)
    t0 = arr.min(); te = t0 + 0.6 * (arr.max() - t0)
    rows = wd.Rows(arr, comp_c, val=np.ones(len(arr)))
    cfg = Config(horizon_s=3600.0, w_candidates_s=(300.0,))
    w = 300.0
    edges = wd.bin_edges(rows, cfg, te)
    raw = wd.build(rows, cfg, w, edges, t0=t0)
    ok = np.isfinite(raw["h"])
    assert np.allclose(raw["h"][ok], raw["hw"][ok])


def test_main_refuses_run_without_freeze_tag(tmp_path):
    import json
    mp = tmp_path / "m.json"; mp.write_text(json.dumps(dict(files=[])))
    ap = tmp_path / "a.json"; ap.write_text("{}")
    assert rd.main(["--mode", "run", "--folder", str(tmp_path), "--manifest", str(mp), "--a3", str(ap),
                    "--out", str(tmp_path / "o")]) == 2     # wrong registered hashes are caught first


def test_value_weighted_features_have_no_lookahead():
    arr, comp, val = synth(n_days=2, rate=0.8)
    comp_c, _ = wd.clip_negative(arr, comp, 0.001)
    cfg = Config(horizon_s=3600.0, w_candidates_s=(300.0,))
    rows = wd.Rows(arr, comp_c, val=val)
    t0 = arr.min(); te = t0 + 0.6 * (arr.max() - t0)
    w = 300.0
    edges = wd.bin_edges(rows, cfg, te)
    full = wd.build(rows, cfg, w, edges, t0=t0)
    for k in (20, 60, full["n"] - 3):
        end = t0 + (k + 1) * w
        keep = arr < end
        comp_k = np.where(comp_c[keep] <= end, comp_c[keep], np.nan)
        part = wd.build(wd.Rows(arr[keep], comp_k, val=val[keep]), cfg, w, edges, t0=t0, n_windows=k + 1)
        a = wd.features(full, cfg, k, "hw")[1]; b = wd.features(part, cfg, k, "hw")[1]
        for key in a:
            assert (np.isnan(a[key]) and np.isnan(b[key])) or np.isclose(a[key], b[key], rtol=1e-9), (k, key)


def test_rehearsal_end_to_end_on_synthetic_files(tmp_path, monkeypatch):
    import io, json, os, zipfile
    import pandas as pd
    from s1.adapters import EXPECTED_HEADER, sha256_file
    cols = EXPECTED_HEADER.split(",")
    arr, comp, val = synth(n_days=10, rate=0.6, seed=9)
    t0 = arr.min() - (arr.min() % 86400)
    entries = []
    for i in range(10):
        m = (arr >= t0 + i * 86400) & (arr < t0 + (i + 1) * 86400)
        n = int(m.sum())
        df = pd.DataFrame({c: np.zeros(n, dtype="int64") for c in cols})
        df["timestamp_ms"] = np.round(arr[m] * 1000).astype("int64")
        df["hash"] = "0xab"
        df["value"] = val[m]
        df["included_block_timestamp_ms"] = np.where(np.isfinite(comp[m]), np.round(comp[m] * 1000), 0.0)
        buf = io.StringIO(); df.to_csv(buf, index=False)
        p = tmp_path / f"2026-10-{16 + i}.csv.zip"
        with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr(p.name[:-4], buf.getvalue())
        entries.append(dict(file=p.name, sha256=sha256_file(str(p))))
    mp = tmp_path / "manifest.json"; mp.write_text(json.dumps(dict(files=entries)))
    a3 = compute(arr, comp, Config())
    ap = tmp_path / "a3.json"; ap.write_text(json.dumps(a3))
    monkeypatch.setattr(rd, "REGISTERED_MANIFEST_SHA256", sha256_file(str(mp)))
    monkeypatch.setattr(rd, "REGISTERED_A3_SHA256", sha256_file(str(ap)))
    out = str(tmp_path / "reh")
    rc = rd.main(["--mode", "rehearsal", "--days", "10", "--folder", str(tmp_path), "--manifest", str(mp),
                  "--a3", str(ap), "--out", out])
    assert rc == 4          # ten days reach past the synthetic training end, so the guard stops it
    a3["train_end"] = float(arr.max() + 1)
    ap.write_text(json.dumps(a3))
    monkeypatch.setattr(rd, "REGISTERED_A3_SHA256", sha256_file(str(ap)))
    rc = rd.main(["--mode", "rehearsal", "--days", "10", "--folder", str(tmp_path), "--manifest", str(mp),
                  "--a3", str(ap), "--out", out])
    assert rc == 0
    res = json.load(open(out + ".json"))
    assert res["mode"] == "rehearsal" and "NOT A RESULT" in res["label"]
    assert set(res["secondary"]) == {"drop_clipped_rows", "unresolved_as_24h", "value_weighted_entropy"}
    # in run mode the freeze tag is required
    rc = rd.main(["--mode", "run", "--folder", str(tmp_path), "--manifest", str(mp), "--a3", str(ap), "--out", out])
    assert rc == 3
