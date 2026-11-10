"""Whole pipeline on synthetic null data: runs, returns finite numbers, gives no support."""
import numpy as np

from s1.config import Config
from s1.run import decide, run_dataset
from s1.synth import generate

CFG = Config(horizon_s=1800.0, block_s=7200.0, n_boot=500, min_resolved_per_window=300,
             w_candidates_s=(30.0, 60.0, 300.0))


def test_null_gives_no_support():
    res = {f"D{i}": run_dataset(generate(40 + i, hours=30), CFG) for i in (1, 2)}
    for r in res.values():
        assert np.isfinite(r["R"]) and np.isfinite(r["loss_g1"]) and r["n_test"] > 100
    out = decide(res, CFG)
    assert out["outcome"] == "Not supported"
