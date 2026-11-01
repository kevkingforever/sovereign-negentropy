"""Self checks for the Phase 1 pipeline. Run: python3 check_pipeline.py

Each check prints PASS or FAIL with the numbers behind it. These checks test that the
pipeline recovers known ground truth from synthetic logs and has no dependence on any
economic layer. They do not test any real payment system.
"""
from __future__ import annotations

import ast
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as pl  # noqa: E402
import synthetic as syn  # noqa: E402

results = []


def check(label: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(("PASS" if ok else "FAIL") + " | " + label + (" | " + detail if detail else ""))


def exact_quantile(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]


# ---------------------------------------------------------------- build one long run
N_TX = 120_000
p = pl.Pipeline(window_s=1e9, k_min=50)  # one window holding the whole run
raw = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}}
for tx, code, ts, retries, failed in syn.stream(N_TX, seed=7, retry_p=0.05, fail_p=0.01):
    raw[code][tx] = ts
    p.process(tx, code, ts, retries, failed)

rep = p.report(p.window_ids()[0])

# ---------------------------------------------------------------- C1 streaming equals batch
bins = p.bins
batch_hist = [0] * bins.n
for tx, t4 in raw[4].items():
    batch_hist[bins.index(t4 - raw[0][tx])] += 1
stream_hist = p._windows[p.window_ids()[0]].hist[4]
check("C1 streaming end to end histogram equals batch histogram", batch_hist == stream_hist,
      f"{sum(stream_hist)} transactions")

# ---------------------------------------------------------------- C2 entropy matches batch computation
h_batch = pl.entropy_nats(batch_hist)
check("C2 H_L equals batch entropy", abs(h_batch - rep["H_L"]) < 1e-12, f"H_L={rep['H_L']:.6f}")

# ---------------------------------------------------------------- C3 quantiles close to exact batch quantiles
worst = 0.0
for s in range(4):
    durs = [raw[s + 1][tx] - raw[s][tx] for tx in raw[4]]
    for q, key in ((0.5, "p50"), (0.99, "p99")):
        ex = exact_quantile(durs, q)
        got = rep[pl.STAGE_NAMES[s]][key]
        worst = max(worst, abs(got - ex) / ex)
check("C3 stage p50 and p99 within bin resolution of exact batch quantiles", worst < 0.045,
      f"worst relative error={worst:.4f}")

# ---------------------------------------------------------------- C4 recovery of analytic ground truth
worst_true = 0.0
for s in range(4):
    got50 = rep[pl.STAGE_NAMES[s]]["p50"]
    # retries inflate durations slightly, so the median is compared with a wider tolerance
    worst_true = max(worst_true, abs(got50 - syn.true_median(s)) / syn.true_median(s))
check("C4 stage medians recover the generating medians (5 percent retries injected)", worst_true < 0.20,
      f"worst relative error={worst_true:.4f}")

# ---------------------------------------------------------------- C5 cleaner stream recovers p99 tightly
q = pl.Pipeline(window_s=1e9, k_min=50)
for tx, code, ts, retries, failed in syn.stream(150_000, seed=11):
    q.process(tx, code, ts, retries, failed)
r2 = q.report(q.window_ids()[0])
worst99 = max(abs(r2[pl.STAGE_NAMES[s]]["p99"] - syn.true_quantile(s)) / syn.true_quantile(s) for s in range(4))
check("C5 stage p99 recovers the analytic lognormal p99 (no retries)", worst99 < 0.08,
      f"worst relative error={worst99:.4f}")

# ---------------------------------------------------------------- C6 conservation of time
bad = 0
for tx, t4 in raw[4].items():
    parts = sum(raw[s + 1][tx] - raw[s][tx] for s in range(4))
    if abs(parts - (t4 - raw[0][tx])) > 1e-6:
        bad += 1
check("C6 stage durations sum to end to end latency for every transaction", bad == 0, f"violations={bad}")

# ---------------------------------------------------------------- C7 retries and failures counted
check("C7 retry and failure counters are populated", rep["retries"] > 0 and rep["failures"] > 0,
      f"retries={rep['retries']} failures={rep['failures']}")

# ---------------------------------------------------------------- C8 cell suppression
small = pl.Pipeline(window_s=1e9, k_min=50)
for tx, code, ts, retries, failed in syn.stream(30, seed=3):
    small.process(tx, code, ts, retries, failed)
rs = small.report(small.window_ids()[0])
check("C8 windows with fewer than 50 transactions are suppressed", rs["suppressed"] and "p99" not in str(rs),
      f"completed={rs['completed']}")

# ---------------------------------------------------------------- C9 robustness to bad input
rb = pl.Pipeline()
rb.process("a", 3, 1.0)       # unknown transaction
rb.process("b", 0, 1.0)
rb.process("b", 2, 2.0)       # skipped stage
rb.process("b", 1, 0.5)       # time going backwards
check("C9 unknown, skipped and backwards events are counted as anomalies, not crashes",
      rb.anomalies == 3, f"anomalies={rb.anomalies}")

# ---------------------------------------------------------------- C10 memory bounded
check("C10 no open transactions remain after all complete", p.open_transactions <= N_TX * 0.0 + 0,
      f"open={p.open_transactions}")

# ---------------------------------------------------------------- C11 independence from any economic layer
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline.py")
tree = ast.parse(open(src_path).read())
imports = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imports |= {a.name.split(".")[0] for a in node.names}
    elif isinstance(node, ast.ImportFrom) and node.module:
        imports.add(node.module.split(".")[0])
names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
econ_words = {"demurrage", "token", "balance", "fee", "amount", "wallet", "currency", "yield"}
hits = sorted(w for w in names if any(e in w.lower() for e in econ_words))
check("C11 pipeline imports only the standard library and references no economic quantity",
      imports <= {"__future__", "math"} and not hits, f"imports={sorted(imports)} economic_names={hits}")

# ---------------------------------------------------------------- C12 constant cost per event
def per_event_cost(n):
    pp = pl.Pipeline(window_s=10.0)
    evs = list(syn.stream(n // 5, seed=5))
    t0 = time.perf_counter()
    for tx, code, ts, r, f in evs:
        pp.process(tx, code, ts, r, f)
    dt = time.perf_counter() - t0
    return dt / len(evs)


small_cost = min(per_event_cost(20_000) for _ in range(3))
large_cost = min(per_event_cost(400_000) for _ in range(2))
ratio = large_cost / small_cost
check("C12 cost per event at 400,000 events is within 1.5 times the cost at 20,000 events", ratio < 1.5,
      f"per event microseconds: {small_cost*1e6:.2f} then {large_cost*1e6:.2f}, ratio={ratio:.2f}")

n_pass = sum(results)
print(f"\n{n_pass} of {len(results)} checks passed")
sys.exit(0 if n_pass == len(results) else 1)
