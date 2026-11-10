"""G1 and G2: gradient boosted quantile regression, pinball loss at 0.99 (Section 6).

Same learner, same grid, same seed for both. Hyperparameters are chosen on the
validation period, then the model is refit on the training period only.

Implementation detail to fix in the data freeze amendment (reviewer item 4):
the learner is fitted to ln(target) and predictions are exponentiated. The 0.99
quantile of ln(y) is ln of the 0.99 quantile of y, so the target is unchanged,
but boosting with a bounded quantile gradient cannot reach latencies of hundreds
of seconds in a few hundred steps on the raw scale. The pinball loss used for
selection and testing is always computed on the original scale.
"""
import itertools

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from .stats import pinball

GRID = {
    "learning_rate": (0.05, 0.15),
    "max_depth": (3, 5),
    "max_iter": (150, 400),
    "min_samples_leaf": (10, 30),
}


class LogQuantileGB:
    def __init__(self, params: dict, cfg):
        self.model = HistGradientBoostingRegressor(
            loss="quantile", quantile=cfg.tau, random_state=cfg.seed, early_stopping=False, **params)

    def fit(self, x, y):
        self.model.fit(x, np.log(np.maximum(y, 1e-9)))
        return self

    def predict(self, x):
        return np.exp(self.model.predict(x))


def fit_select(xtr, ytr, xva, yva, cfg):
    best = None
    keys = list(GRID)
    for vals in itertools.product(*[GRID[k] for k in keys]):
        params = dict(zip(keys, vals))
        mdl = LogQuantileGB(params, cfg).fit(xtr, ytr)
        loss = float(pinball(yva, mdl.predict(xva), cfg.tau).mean())
        if best is None or loss < best[0]:
            best = (loss, params, mdl)
    return best[2], best[1], best[0]
