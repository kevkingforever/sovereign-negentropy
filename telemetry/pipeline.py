"""Phase 1 telemetry pipeline: streaming aggregation of transaction lifecycle timestamps.

What it does
    Reads lifecycle events (transaction id, stage code, timestamp) and maintains, per time
    window, latency histograms for each stage and end to end, retry and failure counts, the
    entropy of the end to end latency distribution (H_L) and the entropy of stage occupancy
    (H_S). Cells with fewer than k_min transactions are suppressed in reports.

What it does not do
    It never writes to the source system. It holds no amounts, balances, tokens, fees or
    identities. It has no economic layer. It depends only on the Python standard library.

Cost
    Each event costs one dictionary lookup, one logarithm and a few integer increments.
    That cost does not depend on how many events came before. Memory is bounded by the
    number of transactions currently in flight plus the number of retained windows.

Licence: MIT (see LICENSE in the repository root).
"""
from __future__ import annotations

import math

STAGE_NAMES = (
    "authentication",
    "routing_transit",
    "clearing_wait",
    "settlement_confirmation",
)
# Event codes: 0 received, 1 authenticated, 2 routed, 3 cleared, 4 settled.
LAST_CODE = len(STAGE_NAMES)


class LogBins:
    """Fixed logarithmic bins over [lo, hi] seconds. Index lookup is constant time."""

    def __init__(self, lo: float = 1e-3, hi: float = 1e3, per_decade: int = 40):
        self.lo = lo
        self.hi = hi
        self.n = int(round(math.log10(hi / lo) * per_decade))
        self.per_decade = per_decade
        self._k = per_decade / math.log(10.0)

    def index(self, x: float) -> int:
        if x <= self.lo:
            return 0
        if x >= self.hi:
            return self.n - 1
        i = int(math.log(x / self.lo) * self._k)
        return i if i < self.n else self.n - 1

    def centre(self, i: int) -> float:
        """Geometric centre of bin i."""
        return self.lo * 10.0 ** ((i + 0.5) / self.per_decade)


class _Window:
    __slots__ = ("hist", "stage_time", "n_completed", "retries", "failures")

    def __init__(self, n_bins: int):
        # one histogram per stage, plus one for end to end latency
        self.hist = [[0] * n_bins for _ in range(LAST_CODE + 1)]
        self.stage_time = [0.0] * LAST_CODE
        self.n_completed = 0
        self.retries = 0
        self.failures = 0


def entropy_nats(weights) -> float:
    """Shannon entropy in nats of a non negative weight vector, with 0 ln(1/0) taken as 0."""
    total = float(sum(weights))
    if total <= 0.0:
        return 0.0
    h = 0.0
    for w in weights:
        if w > 0.0:
            p = w / total
            h += p * math.log(1.0 / p)
    return h


class Pipeline:
    """Streaming aggregator. Feed events in arrival order with process()."""

    def __init__(self, window_s: float = 10.0, bins: LogBins | None = None, k_min: int = 50):
        self.window_s = window_s
        self.bins = bins or LogBins()
        self.k_min = k_min
        self._open: dict = {}
        self._windows: dict[int, _Window] = {}
        self.events_seen = 0
        self.anomalies = 0  # unknown transaction, repeated or out of order stage event

    # ------------------------------------------------------------------ ingest
    def _window(self, ts: float) -> _Window:
        w = int(ts // self.window_s)
        win = self._windows.get(w)
        if win is None:
            win = _Window(self.bins.n)
            self._windows[w] = win
        return win

    def process(self, tx_id, code: int, ts: float, retries: int = 0, failed: bool = False) -> None:
        self.events_seen += 1
        if code == 0:
            self._open[tx_id] = [0, ts, ts]
            return
        st = self._open.get(tx_id)
        if st is None or code != st[0] + 1:
            self.anomalies += 1
            return
        d = ts - st[1]
        if d < 0.0:
            self.anomalies += 1
            return
        win = self._window(ts)
        stage = code - 1
        win.hist[stage][self.bins.index(d)] += 1
        win.stage_time[stage] += d
        win.retries += retries
        if failed:
            win.failures += 1
        if code == LAST_CODE:
            win.hist[LAST_CODE][self.bins.index(ts - st[2])] += 1
            win.n_completed += 1
            del self._open[tx_id]
        else:
            st[0] = code
            st[1] = ts

    # ------------------------------------------------------------------ report
    @property
    def open_transactions(self) -> int:
        return len(self._open)

    def window_ids(self):
        return sorted(self._windows)

    def _quantile(self, hist, q: float):
        n = sum(hist)
        if n == 0:
            return None
        target = q * n
        cum = 0
        for i, c in enumerate(hist):
            cum += c
            if cum >= target:
                return self.bins.centre(i)
        return self.bins.centre(len(hist) - 1)

    def report(self, window_id: int) -> dict:
        win = self._windows[window_id]
        n = win.n_completed
        out = {
            "window_start": window_id * self.window_s,
            "completed": n,
            "suppressed": n < self.k_min,
        }
        if out["suppressed"]:
            return out
        names = STAGE_NAMES + ("end_to_end",)
        for idx, name in enumerate(names):
            h = win.hist[idx]
            out[name] = {
                "p50": self._quantile(h, 0.50),
                "p90": self._quantile(h, 0.90),
                "p99": self._quantile(h, 0.99),
            }
        out["retries"] = win.retries
        out["failures"] = win.failures
        out["H_L"] = entropy_nats(win.hist[LAST_CODE])
        out["H_S"] = entropy_nats(win.stage_time)
        return out

    def pooled(self, window_ids=None) -> dict:
        """Merge several windows into one set of histograms (used for long runs)."""
        ids = window_ids if window_ids is not None else self.window_ids()
        merged = _Window(self.bins.n)
        for w in ids:
            src = self._windows[w]
            for s in range(LAST_CODE + 1):
                hs, hm = src.hist[s], merged.hist[s]
                for i, c in enumerate(hs):
                    if c:
                        hm[i] += c
            for s in range(LAST_CODE):
                merged.stage_time[s] += src.stage_time[s]
            merged.n_completed += src.n_completed
            merged.retries += src.retries
            merged.failures += src.failures
        self._windows[-10**9] = merged
        try:
            return self.report(-10**9)
        finally:
            del self._windows[-10**9]
