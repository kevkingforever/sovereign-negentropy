import numpy as np

from s1.config import Config
from s1.stats import (circular_block_ci, dm_one_sided, holm, overall_outcome, pinball,
                      rel_improvement)


def test_pinball_known_values():
    assert np.isclose(pinball([10.0], [8.0], 0.99)[0], 1.98)
    assert np.isclose(pinball([8.0], [10.0], 0.99)[0], 0.02)


def test_r_sign():
    assert np.isclose(rel_improvement([2.0, 2.0], [1.0, 1.0]), 0.5)


def test_holm():
    adj = holm({"D1": 0.01, "D2": 0.03})
    assert np.isclose(adj["D1"], 0.02) and np.isclose(adj["D2"], 0.03)
    adj = holm({"D1": 0.04, "D2": 0.03})
    assert np.isclose(adj["D2"], 0.06) and np.isclose(adj["D1"], 0.06)


def test_dm_detects_and_rejects():
    rng = np.random.default_rng(1)
    l1 = rng.exponential(1.0, 400)
    assert dm_one_sided(l1, l1 * 0.8)["p"] < 0.001          # G2 clearly better
    assert dm_one_sided(l1 * 0.8, l1)["p"] > 0.99           # G2 clearly worse
    ps = [dm_one_sided(l1, rng.permutation(l1))["p"] for _ in range(1)]
    assert 0.0 <= ps[0] <= 1.0


def test_dm_size_under_null():
    rng = np.random.default_rng(2)
    rej = 0
    for _ in range(400):
        d = rng.standard_normal(200)
        l1 = 5 + d; l2 = 5 + rng.standard_normal(200)
        rej += dm_one_sided(l1, l2)["p"] < 0.05
    assert rej / 400 < 0.10                                  # nominal 0.05, allow slack


def test_bootstrap_interval_covers_truth():
    rng = np.random.default_rng(3)
    l1 = rng.exponential(1.0, 300)
    l2 = l1 * 0.9
    lo, hi = circular_block_ci(l1, l2, 10, 2000, 0.05, 20261031)
    assert lo < 0.1 < hi or np.isclose(lo, 0.1)
    assert lo > 0.05


def test_outcomes():
    assert overall_outcome({"D1": True, "D2": True}) == "Supported"
    assert overall_outcome({"D1": False, "D2": False}) == "Not supported"
    assert overall_outcome({"D1": True, "D2": False}) == "Inconclusive"


def test_ineligible_dataset_cannot_support_and_is_left_out():
    from s1.run import decide
    cfg = Config()
    good = dict(p_raw=0.001, R=0.2, ci=(0.1, 0.3), eligible=True)
    bad = dict(p_raw=0.0001, R=0.5, ci=(0.4, 0.6), eligible=False)
    out = decide({"D1": bad, "D2": good}, cfg)
    assert out["outcome"] == "Supported" and out["ineligible"] == ["D1"] and "D1" not in out["support"]
    assert decide({"D1": bad}, cfg)["outcome"] == "Not testable"


def test_clip_negative_keeps_rows():
    import numpy as np
    from s1.windows import clip_negative
    comp, n = clip_negative([10.0, 10.0, 10.0], [9.0, 10.0005, 12.0])
    assert n == 2 and np.allclose(comp, [10.001, 10.001, 12.0])
