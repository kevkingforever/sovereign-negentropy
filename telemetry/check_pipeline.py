"""Self checks for the Phase 1 pipeline. Run: python3 check_pipeline.py

Each check prints PASS or FAIL with the numbers behind it. These checks test that the
pipeline recovers known ground truth from synthetic logs and has no dependence on any
economic layer. They do not test any real payment system. Each check label says what it does and does not
establish. Revised 5 November 2026 after an external review (see REVIEWERS.md).
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
inj_retries = 0
inj_failures = 0
for tx, code, ts, retries, failed in syn.stream(N_TX, seed=7, retry_p=0.05, fail_p=0.01):
    raw[code][tx] = ts
    inj_retries += retries
    inj_failures += 1 if failed else 0
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
check("C6 the synthetic timestamps are self consistent: stage durations sum to end to end latency (does not test the pipeline window allocation)", bad == 0, f"violations={bad}")

# ---------------------------------------------------------------- C7 retries and failures counted
check("C7 retry and failure totals equal the injected totals (failures here occur at the settlement event)",
      rep["retries"] == inj_retries and rep["failures"] == inj_failures,
      f"retries={rep['retries']} of {inj_retries} failures={rep['failures']} of {inj_failures}")

# ---------------------------------------------------------------- C8 cell suppression
small = pl.Pipeline(window_s=1e9, k_min=50)
for tx, code, ts, retries, failed in syn.stream(30, seed=3):
    small.process(tx, code, ts, retries, failed)
rs = small.report(small.window_ids()[0])
check("C8 a whole window with fewer than 50 completions is suppressed and exposes no count", rs["suppressed"] and "p99" not in str(rs) and "completed" not in rs,
      f"report={rs}")

# ---------------------------------------------------------------- C9 robustness to bad input
rb = pl.Pipeline()
rb.process("a", 3, 1.0)       # unknown transaction
rb.process("b", 0, 1.0)
rb.process("b", 2, 2.0)       # skipped stage
rb.process("b", 1, 0.5)       # time going backwards
check("C9 unknown, skipped and backwards events are counted as anomalies, not crashes",
      rb.anomalies == 3, f"anomalies={rb.anomalies}")

# ---------------------------------------------------------------- C10 memory bounded
check("C10 no open transactions remain after fully completed lifecycles (abandoned transactions are tested in C16)", p.open_transactions == 0,
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
check("C11 source scan: standard library imports only and no economic names (this is not a privacy or security test)",
      imports <= {"__future__", "math", "collections"} and not hits, f"imports={sorted(imports)} economic_names={hits}")

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
check("C12 short timing comparison: cost per event at 400,000 events is within 1.5 times the cost at 20,000 events (not a worst case guarantee)", ratio < 1.5,
      f"per event microseconds: {small_cost*1e6:.2f} then {large_cost*1e6:.2f}, ratio={ratio:.2f}")

# ---------------------------------------------------------------- C13 per stage suppression
# Window 1 holds 51 completions, but only one of them has its authentication exit inside window 1.
ps = pl.Pipeline(window_s=10.0, k_min=50)
for i in range(51):
    ps.process(f"x{i}", 0, 0.0)
    ps.process(f"x{i}", 1, 11.0 if i == 0 else 9.0)
    ps.process(f"x{i}", 2, 11.5)
    ps.process(f"x{i}", 3, 12.0)
    ps.process(f"x{i}", 4, 13.0)
r1 = ps.report(1)
check("C13 a stage with fewer than 50 contributing transactions is suppressed even when the window is not",
      (not r1["suppressed"]) and r1["completed"] == 51 and r1["authentication"] == {"suppressed": True}
      and "p99" in r1["end_to_end"],
      f"completed={r1['completed']} authentication={r1['authentication']}")

# ---------------------------------------------------------------- C14 duplicate start keeps the original
pd = pl.Pipeline()
for c, t in ((0, 0), (0, 5), (1, 6), (2, 7), (3, 8), (4, 10)):
    pd.process("d", c, float(t))
wd = pd._windows[pd.window_ids()[-1]]
e2e_bin = [i for i, c in enumerate(wd.hist[4]) if c]
check("C14 a duplicate start is rejected and the original start is kept (end to end stays 10 s)",
      pd.reasons["duplicate_start"] == 1 and wd.n_completed == 1 and e2e_bin == [pd.bins.index(10.0)],
      f"reasons={ {k: v for k, v in pd.reasons.items() if v} }")

# ---------------------------------------------------------------- C15 replay of a finished transaction
pr = pl.Pipeline()
for c, t in ((0, 0), (1, 1), (2, 2), (3, 3), (4, 4)):
    pr.process("r", c, float(t))
pr.process("r", 0, 100.0)
check("C15 replaying a finished transaction id is rejected, not counted twice",
      pr.reasons["replayed_transaction"] == 1 and sum(w.n_completed for w in pr._windows.values()) == 1,
      f"reasons={ {k: v for k, v in pr.reasons.items() if v} }")

# ---------------------------------------------------------------- C16 memory bounded under abandoned transactions
pa = pl.Pipeline(window_s=10.0, expire_after_s=100.0, retain_windows=50)
for i in range(5000):
    pa.process(f"a{i}", 0, i * 10.0)
check("C16 abandoned transactions expire and old windows are evicted (state stays bounded)",
      pa.open_transactions <= 11 and len(pa._windows) <= 51 and pa.unresolved_total >= 4980,
      f"open={pa.open_transactions} windows={len(pa._windows)} unresolved={pa.unresolved_total}")

# ---------------------------------------------------------------- C17 overflow and underflow are counted and flagged
po = pl.Pipeline(window_s=1e9, k_min=50)
for i in range(60):
    po.process(i, 0, 0.0)
    po.process(i, 1, 1.0)
    po.process(i, 2, 2.0)
    po.process(i, 3, 3.0)
    po.process(i, 4, 8 * 3600.0)   # eight hours of settlement wait, far above the 1,000 s ceiling
ro = po.report(po.window_ids()[0])
e2e = ro["end_to_end"]
check("C17 durations above the histogram ceiling are counted as overflow and the quantile is flagged as a lower bound",
      e2e["overflow"] == 60 and e2e["p99_bound"] == "lower",
      f"overflow={e2e['overflow']} p99={e2e['p99']:.1f} bound={e2e.get('p99_bound')}")

# ---------------------------------------------------------------- C18 invalid input is rejected before state changes
pv = pl.Pipeline()
pv.process("v", 0, float("nan"))
pv.process("v", 0, float("inf"))
pv.process("v", 9, 1.0)
pv.process("v", 0, 1.0, retries=-1)
pv.process("v", 0, "x")
ok_cfg = True
for bad_kwargs in ({"window_s": 0}, {"window_s": float("nan")}, {"k_min": 0}):
    try:
        pl.Pipeline(**bad_kwargs)
        ok_cfg = False
    except ValueError:
        pass
check("C18 non finite timestamps, bad codes, negative retries and bad configuration are rejected with reasons, before any state changes",
      pv.open_transactions == 0 and pv.anomalies == 5 and ok_cfg,
      f"reasons={ {k: v for k, v in pv.reasons.items() if v} }")

# ---------------------------------------------------------------- C19 pooled report does not touch the window table
before = dict(p._windows)
pooled = p.pooled()
check("C19 pooled() leaves the window table unchanged and reports no fake window start",
      p._windows == before and pooled["window_start"] is None, f"windows={len(p._windows)}")

# ---------------------------------------------------------------- C20 lifecycle stall is visible
pst = pl.Pipeline(window_s=10.0, expire_after_s=50.0, k_min=1)
for i in range(3):
    pst.process(f"s{i}", 0, 0.0)
pst.process("late", 0, 1000.0)
check("C20 stalled transactions are counted as unresolved in the window where they started",
      pst._windows[0].unresolved == 3 and pst.unresolved_total == 3,
      f"unresolved_total={pst.unresolved_total}")

n_pass = sum(results)
print(f"\n{n_pass} of {len(results)} checks passed")
sys.exit(0 if n_pass == len(results) else 1)
