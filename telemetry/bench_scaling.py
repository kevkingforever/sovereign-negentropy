"""Per event cost of the Phase 1 pipeline at increasing stream sizes. Standard library only.
Run: python3 bench_scaling.py  (writes results/scaling.json)
"""
import json, os, sys, time, resource
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as pl, synthetic as syn

out = []
for n_tx in (10_000, 40_000, 160_000, 640_000):
    evs = list(syn.stream(n_tx, seed=5))
    best = None
    for _ in range(3):
        p = pl.Pipeline(window_s=10.0)
        t0 = time.perf_counter()
        for tx, code, ts, r, f in evs:
            p.process(tx, code, ts, r, f)
        dt = time.perf_counter() - t0
        best = dt if best is None else min(best, dt)
    out.append({"transactions": n_tx, "events": len(evs), "us_per_event": best / len(evs) * 1e6,
                "open_after": p.open_transactions, "windows": len(p.window_ids())})
    print(out[-1])
    del evs
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "scaling.json"), "w"), indent=1)
