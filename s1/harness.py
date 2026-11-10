"""Machinery check on synthetic data. Run from the repository root: python3 -m s1.harness 48"""
import sys, time
from s1.config import Config
from s1.run import run_dataset, decide
from s1.synth import generate

cfg = Config(horizon_s=1800.0, block_s=7200.0, n_boot=2000, min_resolved_per_window=300,
             w_candidates_s=(30.0, 60.0, 300.0, 600.0, 1800.0))
hours = float(sys.argv[1]) if len(sys.argv) > 1 else 48
for planted in (False, True):
    res = {}
    for i, seed in enumerate((11, 12)):
        t = time.time()
        rows = generate(seed, hours=hours, planted=planted)
        r = run_dataset(rows, cfg)
        res[f"D{i+1}"] = r
        print(f"planted={planted} D{i+1}: W={r['W']:.0f}s test={r['n_test']} R={r['R']:+.3f} "
              f"CI=({r['ci'][0]:+.3f},{r['ci'][1]:+.3f}) p={r['p_raw']:.4f} "
              f"G1={r['loss_g1']:.2f} G2={r['loss_g2']:.2f} base={ {k: round(v,1) for k,v in r['baselines'].items()} } "
              f"[{time.time()-t:.0f}s]")
    print("  decision:", decide(res, cfg))
