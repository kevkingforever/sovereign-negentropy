import numpy as np

from s1.config import Config
from s1.limits import format_limits
from s1.run import run_dataset
from s1.synth import generate

CFG = Config(horizon_s=1800.0, block_s=7200.0, n_boot=200, min_resolved_per_window=300,
             w_candidates_s=(30.0, 60.0, 300.0))


def test_limits_report_present_and_warns_on_small_data():
    r = run_dataset(generate(50, hours=12), CFG)
    lim = r["limits"]
    text = format_limits(lim)
    assert text.startswith("Limits")
    assert any("test size" in w or "training size" in w for w in lim["warnings"])


def test_collapse_is_flagged():
    from s1.limits import limits
    n = 300
    f = np.full(n, 100.0)
    d = dict(keys1=["a"], keys2=["a", "b"], X1=np.zeros((n, 1)), X2=np.zeros((n, 2)))
    tr = np.ones(n, bool)
    lim = limits(0.0, d, tr, tr, f, f * 1.001, {"max_iter": 150, "learning_rate": 0.05},
                 {"max_iter": 150, "learning_rate": 0.05}, 10, 300, 0)
    assert lim["collapsed"] and any("constant" in w for w in lim["warnings"])
