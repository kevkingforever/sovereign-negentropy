"""Power study on synthetic data. Run from the repository root:

    python3 -m s1.power OUT.jsonl REPS HOURS STRENGTH [STRENGTH ...]

Each line of OUT.jsonl is one replicate. Strength 0 means no planted signal. The study
measures how often the registered rule says Supported when there is no signal (false
support) and when there is one (power), at a given amount of data. It says nothing about
the real world: the signal here is invented.
"""
import json
import sys
import time

from .config import Config
from .run import run_dataset
from .synth import generate

CFG = Config(horizon_s=1800.0, block_s=7200.0, n_boot=1000, min_resolved_per_window=300,
             w_candidates_s=(30.0, 60.0, 300.0))


def one(seed: int, hours: float, strength: float, rate: float = 12.0) -> dict:
    rows = generate(seed, hours=hours, rate=rate, planted=strength > 0, d_ar=0.7, lead=1,
                    strength=max(strength, 1e-9))
    r = run_dataset(rows, CFG)
    ok = r["p_raw"] < CFG.alpha and r["R"] >= CFG.r_min and r["ci"][0] > 0
    return dict(seed=seed, hours=hours, strength=strength, W=r["W"], n_test=r["n_test"], R=r["R"],
                ci_lo=r["ci"][0], ci_hi=r["ci"][1], p=r["p_raw"], dataset_support=bool(ok),
                collapsed=r["limits"]["collapsed"], R_log=r["log_scale"]["R"], p_log=r["log_scale"]["p"], n_warnings=len(r["limits"]["warnings"]))


if __name__ == "__main__":
    out, reps, hours = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
    strengths = [float(x) for x in sys.argv[4:]]
    with open(out, "a") as fh:
        for s in strengths:
            for i in range(reps):
                t = time.time()
                rec = one(1000 * int(s * 10) + i + int(hours), hours, s)
                rec["sec"] = round(time.time() - t, 1)
                fh.write(json.dumps(rec) + "\n"); fh.flush()
                print(rec, flush=True)
