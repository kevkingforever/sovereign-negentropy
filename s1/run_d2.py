"""The registered S1 run on D2 (Ethereum), and a rehearsal on training days only.

Two modes.
  run        The single registered run. Reads the 28 files that Amendment A2 fixes, checks them and the A3 file
             against their registered SHA256 values, takes the window length and bin edges from Amendment A3,
             recomputes them and stops if they differ, then fits G1 and G2, scores the test period and applies the
             registered decision rule. Refuses to start unless the code carries the freeze tag.
  rehearsal  Runs the same code on the first N days only, all of which lie inside the training period, cut into
             their own training, validation and test pieces. It exists to find file, memory and runtime problems.
             Its output says REHEARSAL and is not a result. Only bugs may be fixed after it. No setting changes.

Usage
  python3 -m s1.run_d2 --mode rehearsal --days 14 --folder FOLDER --manifest M --a3 A3 --out OUT
  python3 -m s1.run_d2 --mode run --folder FOLDER --manifest M --a3 A3 --out OUT
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time

import numpy as np

from . import windows as wd
from .adapters import load_d2, sha256_file, verify_manifest
from .config import Config
from .limits import format_limits
from .run import decide, run_dataset

FREEZE_TAG = "s1-code-freeze-v1"
REGISTERED_MANIFEST_SHA256 = "12ca0cb8ee24cdd164a05bc247048682a8467151a36d9b889c42b22cdbf01148"   # Amendment A2
REGISTERED_A3_SHA256 = "9d036dec92621e3060ae234b202f374e12faeb0619e44c196115df615bb7ea5b"         # Amendment A3


def _clean(x):
    if isinstance(x, dict):
        return {str(k): _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if isinstance(x, np.ndarray):
        return [_clean(v) for v in x.tolist()]
    if isinstance(x, (np.floating, float)):
        return float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    return x


def summary(r: dict) -> dict:
    keep = ("W", "n_train", "n_val", "n_test", "loss_g1", "loss_g2", "R", "ci", "p_raw", "block", "eligible",
            "params_g1", "params_g2", "baselines", "log_scale", "surge", "brier")
    s = {k: r[k] for k in keep}
    s["limits"] = {k: r["limits"][k] for k in ("warnings", "collapsed", "mean_rel_diff", "constant_features",
                                               "unresolved_share")}
    return _clean(s)


def run_all(arr, comp, val, cfg: Config, a3: dict | None, rehearsal: bool = False, log=print) -> dict:
    """arr and comp in seconds, comp nan when unresolved. a3: the registered constants (None in a rehearsal)."""
    clipped = np.isfinite(comp) & (comp < arr + cfg.latency_floor_s)
    comp_c, n_clip = wd.clip_negative(arr, comp, cfg.latency_floor_s)
    fixed = None if a3 is None else dict(w=a3["W_seconds"], edges=a3["bin_edges_seconds"], check=not rehearsal)
    fixed_loose = None if fixed is None else dict(fixed, check=False)
    out = dict(n_rows=int(len(arr)), n_clipped=int(n_clip), clipped_share=float(n_clip / len(arr)))

    t = time.time()
    rows = wd.Rows(arr, comp_c, val=val)
    log("primary run ...")
    primary = run_dataset(rows, cfg, fixed=fixed)
    out["primary"] = primary
    out["decision"] = _clean(decide({"D2": primary}, cfg))
    log(f"  done in {time.time() - t:.0f} s")

    sens = {}

    def secondary(name, fn):
        """A secondary run must never stop the report of the primary run. A failure is recorded, not hidden."""
        t0_ = time.time(); log(f"secondary: {name} ...")
        try:
            sens[name] = summary(fn())
        except Exception as e:                      # noqa: BLE001
            sens[name] = dict(error=f"{type(e).__name__}: {e}")
        log(f"  done in {time.time() - t0_:.0f} s")

    keep = ~clipped
    r2 = wd.Rows(arr[keep], comp_c[keep], val=None if val is None else val[keep])
    secondary("drop_clipped_rows", lambda: run_dataset(r2, cfg, fixed=fixed_loose))
    secondary("unresolved_as_24h", lambda: run_dataset(rows, cfg, use_unresolved_target=True, fixed=fixed_loose))
    if val is not None:
        secondary("value_weighted_entropy", lambda: run_dataset(rows, cfg, h_key="hw", fixed=fixed_loose))
    out["secondary"] = sens
    return out


def report(out: dict, label: str) -> str:
    p = out["primary"]
    L = [f"=== {label} ===",
         f"rows {out['n_rows']}, clipped to the latency floor {out['n_clipped']} ({out['clipped_share']:.2%})",
         f"W {p['W']:.0f} s, windows: train {p['n_train']}, validation {p['n_val']}, test {p['n_test']}, "
         f"block {p['block']} windows, eligible {p['eligible']}",
         f"pinball loss at 0.99 (original scale): G1 {p['loss_g1']:.4f}, G2 {p['loss_g2']:.4f}",
         f"R = {p['R']:+.4f}   95% interval ({p['ci'][0]:+.4f}, {p['ci'][1]:+.4f})   one sided DM p = {p['p_raw']:.4f}",
         "baselines (mean pinball): " + ", ".join(f"{k} {v:.4f}" for k, v in p["baselines"].items()),
         f"log scale: R {p['log_scale']['R']:+.4f}, p {p['log_scale']['p']:.4f}",
         f"surge windows: {p['surge']}",
         f"Brier (binary forecast): {p['brier']}",
         f"DECISION: {out['decision']}",
         format_limits(p["limits"]),
         "secondary runs (no decision rule):"]
    for k, s in out.get("secondary", {}).items():
        if "error" in s:
            L.append(f"  {k}: could not be computed: {s['error']}")
            continue
        L.append(f"  {k}: R {s['R']:+.4f}, interval ({s['ci'][0]:+.4f}, {s['ci'][1]:+.4f}), p {s['p_raw']:.4f}, "
                 f"test windows {s['n_test']}")
    return "\n".join(L)


def _git(args):
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        return subprocess.run(["git"] + args, cwd=here, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        return ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mode", choices=("run", "rehearsal"), required=True)
    ap.add_argument("--folder", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--a3", required=True)
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    cfg = Config()

    if sha256_file(a.manifest) != REGISTERED_MANIFEST_SHA256:
        print("STOP: the manifest differs from the one registered in Amendment A2."); return 2
    if sha256_file(a.a3) != REGISTERED_A3_SHA256:
        print("STOP: the A3 file differs from the one registered in Amendment A3."); return 2
    manifest = json.load(open(a.manifest)); a3 = json.load(open(a.a3))
    tag = _git(["describe", "--tags", "--exact-match", "HEAD"])
    commit = _git(["rev-parse", "HEAD"])
    if a.mode == "run" and tag != FREEZE_TAG:
        print(f"STOP: the code is not at the tag {FREEZE_TAG} (found '{tag}'). The registered run uses frozen code only."); return 3
    sub = dict(files=manifest["files"][:a.days]) if a.mode == "rehearsal" else manifest
    bad = verify_manifest(a.folder, sub)
    if bad:
        print("STOP: files missing or not matching the manifest:", bad); return 2
    print("files match the manifest:", len(sub["files"]))
    d = load_d2(a.folder, sub, with_value=True)
    arr, comp, val = d["arr"], d["comp"], d["val"]
    if a.mode == "rehearsal":
        if arr.max() >= a3["train_end"]:
            print("STOP: the rehearsal would reach past the end of the training period."); return 4
        out = run_all(arr, comp, val, cfg, None, rehearsal=True)
        label = f"REHEARSAL on the first {a.days} days, training period only. NOT A RESULT"
    else:
        out = run_all(arr, comp, val, cfg, a3)
        label = "S1 RUN on D2 (Ethereum)"
    txt = report(out, label)
    print(); print(txt)
    res = dict(label=label, mode=a.mode, created_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               git_tag=tag, git_commit=commit,
               code_sha256={n: sha256_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), n))
                            for n in ("run_d2.py", "run.py", "windows.py", "adapters.py", "models.py", "stats.py",
                                      "queueing.py", "limits.py", "config.py")},
               manifest_sha256=REGISTERED_MANIFEST_SHA256, a3_sha256=REGISTERED_A3_SHA256,
               n_rows=out["n_rows"], n_clipped=out["n_clipped"], decision=out["decision"],
               primary=summary(out["primary"]), secondary=out["secondary"], report=txt)
    with open(a.out + ".json", "w") as f:
        json.dump(res, f, indent=2)
    with open(a.out + ".txt", "w") as f:
        f.write(txt + "\n")
    print("\nwrote", a.out + ".json", "and", a.out + ".txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
