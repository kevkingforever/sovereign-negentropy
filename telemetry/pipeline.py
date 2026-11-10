"""Phase 1 telemetry pipeline: streaming aggregation of transaction lifecycle timestamps.

Version 0.3, revised after external reviews on 4 and 9 November 2026 (see REVIEWERS.md).

What it does
    Reads lifecycle events (transaction id, stage code, timestamp) and maintains, per time
    window, latency histograms for each stage and end to end, retry and failure counts, the
    entropy of the end to end latency distribution (H_L) and the entropy of the durations
    booked at stage exit (H_exit, see below). A published number is suppressed whenever fewer
    than k_min transactions contributed to it, stage by stage.

What it does not do
    It never writes to the source system. It holds no amounts, balances, tokens, fees or
    names. It has no economic layer. It depends only on the Python standard library.
    It does not pseudonymise: transaction identifiers are held in memory while a transaction
    is open and in a bounded recent window for replay detection. The operator must supply
    pseudonymised identifiers.

Contracts (v0.3)
    Windows. A stage duration is booked in the window containing the stage exit time. End to
    end latency is booked in the window containing settlement. Stage quantiles in one report
    therefore describe different transaction cohorts, and stage p99 values must not be added.
    H_exit is the entropy of the stage durations booked at exit in the window. It is NOT the
    value weighted in flight occupancy statistic of the registered pre registration (Section
    4.4). That statistic needs window overlap accounting and weights, and is not implemented.
    Duplicates. A start event for a transaction that is already open, or that finished
    recently, is rejected and counted. The original start is kept. Replay detection covers the
    most recent `dedup_capacity` finished identifiers only. A durable deduplication strategy
    belongs in the ingestion adapter.
    Retries and failures. `retries` is the number of retries since the previous event of the
    same transaction (not a running total). `failed` marks a failed attempt at that stage; the
    lifecycle continues. Failure counts are failed events, not unique failed transactions.
    Retry and failure fields on start events are ignored. Rates are not reported.
    Unfinished transactions. A transaction with no event for `expire_after_s` seconds of event
    time is dropped and counted as unresolved in the window of its start. Windows older than
    `retain_windows` windows behind the newest window are evicted. Event time is the largest
    timestamp seen among accepted events, so events must arrive roughly in time order. Rejected
    events never move event time. Expiry runs when a transaction starts; call `flush()` or
    `advance_watermark(ts)` at the end of a polling batch or stream to expire the rest.
    Histogram range. Durations at or below `lo` and at or above `hi` are counted in separate
    underflow and overflow counters. A quantile that falls in an edge bin with such counts is
    reported with a flag saying it is a bound, not an estimate.

Cost
    Each event costs a few dictionary operations, one logarithm and a few integer increments.
    That cost does not depend on how many events came before. Memory is bounded by the
    transactions currently in flight, the recent identifier window and the retained windows.

Licence: MIT (see LICENSE in the repository root).
"""
from __future__ import annotations

import math
from collections import OrderedDict

STAGE_NAMES = (
    "authentication",
    "routing_transit",
    "clearing_wait",
    "settlement_confirmation",
)
# Event codes: 0 received, 1 authenticated, 2 routed, 3 cleared, 4 settled.
LAST_CODE = len(STAGE_NAMES)

REASONS = (
    "unknown_transaction",
    "skipped_or_repeated_stage",
    "time_backwards",
    "duplicate_start",
    "replayed_transaction",
    "nonfinite_timestamp",
    "invalid_code",
    "invalid_retries",
)


class LogBins:
    """Fixed logarithmic bins over [lo, hi] seconds. Index lookup is constant time."""

    def __init__(self, lo: float = 1e-3, hi: float = 1e3, per_decade: int = 40):
        if not (math.isfinite(lo) and math.isfinite(hi) and lo > 0.0 and hi > lo):
            raise ValueError("LogBins needs finite 0 < lo < hi")
        if not isinstance(per_decade, int) or isinstance(per_decade, bool) or per_decade < 1:
            raise ValueError("LogBins needs per_decade as an integer of at least 1")
        self.lo = lo
        self.hi = hi
        self.n = max(1, int(round(math.log10(hi / lo) * per_decade)))
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
    __slots__ = ("hist", "stage_time", "stage_n", "under", "over", "n_completed",
                 "retries", "failures", "unresolved")

    def __init__(self, n_bins: int):
        # one histogram per stage, plus one for end to end latency
        self.hist = [[0] * n_bins for _ in range(LAST_CODE + 1)]
        self.stage_time = [0.0] * LAST_CODE
        self.stage_n = [0] * LAST_CODE      # transactions contributing to each stage cell
        self.under = [0] * (LAST_CODE + 1)  # durations at or below the lowest edge
        self.over = [0] * (LAST_CODE + 1)   # durations at or above the highest edge
        self.n_completed = 0
        self.retries = 0
        self.failures = 0
        self.unresolved = 0


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

    def __init__(self, window_s: float = 10.0, bins: LogBins | None = None, k_min: int = 50,
                 expire_after_s: float = 86400.0, retain_windows: int = 8640,
                 dedup_capacity: int = 100_000):
        if not (isinstance(window_s, (int, float)) and math.isfinite(window_s) and window_s > 0.0):
            raise ValueError("window_s must be a finite positive number")
        if not isinstance(k_min, int) or isinstance(k_min, bool) or k_min < 1:
            raise ValueError("k_min must be an integer of at least 1")
        if not (isinstance(expire_after_s, (int, float)) and expire_after_s > 0.0):
            raise ValueError("expire_after_s must be positive")
        if not isinstance(retain_windows, int) or retain_windows < 1:
            raise ValueError("retain_windows must be an integer of at least 1")
        if not isinstance(dedup_capacity, int) or dedup_capacity < 0:
            raise ValueError("dedup_capacity must be an integer of at least 0")
        self.window_s = window_s
        self.bins = bins or LogBins()
        self.k_min = k_min
        self.expire_after_s = expire_after_s
        self.retain_windows = retain_windows
        self.dedup_capacity = dedup_capacity
        self._open: OrderedDict = OrderedDict()    # tx id -> [last code, last ts, start ts]
        self._recent: OrderedDict = OrderedDict()  # recently finished ids, bounded
        self._windows: dict[int, _Window] = {}
        self._max_ts = float("-inf")
        self._max_window = None
        self.events_seen = 0
        self.anomalies = 0  # total rejected events
        self.reasons = {r: 0 for r in REASONS}
        self.unresolved_total = 0

    # ------------------------------------------------------------------ ingest
    def _reject(self, reason: str) -> None:
        self.anomalies += 1
        self.reasons[reason] += 1

    def _window(self, ts: float) -> _Window:
        w = int(ts // self.window_s)
        win = self._windows.get(w)
        if win is None:
            win = _Window(self.bins.n)
            self._windows[w] = win
            if self._max_window is None or w > self._max_window:
                self._max_window = w
                self._evict()
        return win

    def _evict(self) -> None:
        cutoff = self._max_window - self.retain_windows
        old = [w for w in self._windows if w <= cutoff]
        for w in old:
            del self._windows[w]

    def _expire(self) -> None:
        horizon = self._max_ts - self.expire_after_s
        open_ = self._open
        while open_:
            tx_id = next(iter(open_))
            st = open_[tx_id]
            if st[1] >= horizon:
                break
            del open_[tx_id]
            self.unresolved_total += 1
            self._window(st[2]).unresolved += 1

    def _advance_clock(self, ts: float) -> None:
        if ts > self._max_ts:
            self._max_ts = ts

    def advance_watermark(self, ts: float) -> None:
        """Move event time forward without an event, then expire stale transactions.

        Call it when a polling batch ends or when the input stream closes, so that
        unfinished transactions are counted as unresolved even if no new transaction
        starts. A non finite timestamp is rejected and changes nothing.
        """
        try:
            finite = math.isfinite(ts)
        except TypeError:
            finite = False
        if not finite:
            return self._reject("nonfinite_timestamp")
        self._advance_clock(ts)
        self._expire()

    def flush(self) -> None:
        """Run expiry at the current event time. Use at the end of a batch or stream."""
        self._expire()

    def process(self, tx_id, code, ts, retries=0, failed=False) -> None:
        self.events_seen += 1
        # validate everything before any state changes
        if type(code) is not int or not 0 <= code <= LAST_CODE:
            return self._reject("invalid_code")
        try:
            finite = math.isfinite(ts)
        except TypeError:
            finite = False
        if not finite:
            return self._reject("nonfinite_timestamp")
        if type(retries) is not int or retries < 0:
            return self._reject("invalid_retries")
        if code == 0:
            if tx_id in self._open:
                return self._reject("duplicate_start")
            if tx_id in self._recent:
                return self._reject("replayed_transaction")
            self._advance_clock(ts)  # only an accepted event moves event time
            self._open[tx_id] = [0, ts, ts]
            self._expire()
            return
        st = self._open.get(tx_id)
        if st is None or code != st[0] + 1:
            return self._reject("unknown_transaction" if st is None else "skipped_or_repeated_stage")
        d = ts - st[1]
        if d < 0.0:
            return self._reject("time_backwards")
        self._advance_clock(ts)  # only an accepted event moves event time
        win = self._window(ts)
        stage = code - 1
        lo, hi = self.bins.lo, self.bins.hi
        win.hist[stage][self.bins.index(d)] += 1
        win.stage_n[stage] += 1
        if d <= lo:
            win.under[stage] += 1
        elif d >= hi:
            win.over[stage] += 1
        win.stage_time[stage] += d
        win.retries += retries
        if failed:
            win.failures += 1
        if code == LAST_CODE:
            e2e = ts - st[2]
            win.hist[LAST_CODE][self.bins.index(e2e)] += 1
            if e2e <= lo:
                win.under[LAST_CODE] += 1
            elif e2e >= hi:
                win.over[LAST_CODE] += 1
            win.n_completed += 1
            del self._open[tx_id]
            if self.dedup_capacity:
                self._recent[tx_id] = None
                if len(self._recent) > self.dedup_capacity:
                    self._recent.popitem(last=False)
        else:
            st[0] = code
            st[1] = ts
            self._open.move_to_end(tx_id)  # keep the open table ordered by last activity

    # ------------------------------------------------------------------ report
    @property
    def open_transactions(self) -> int:
        return len(self._open)

    def window_ids(self):
        return sorted(self._windows)

    def _quantile(self, hist, q: float, under: int = 0, over: int = 0):
        """Return (value, bound) where bound is None, 'lower' or 'upper'."""
        n = sum(hist)
        if n == 0:
            return None, None
        target = q * n
        cum = 0
        idx = len(hist) - 1
        for i, c in enumerate(hist):
            cum += c
            if cum >= target:
                idx = i
                break
        bound = None
        if idx == len(hist) - 1 and over > 0:
            bound = "lower"
        elif idx == 0 and under > 0:
            bound = "upper"
        return self.bins.centre(idx), bound

    def _stage_cell(self, win: _Window, idx: int, n: int) -> dict:
        if n < self.k_min:
            return {"suppressed": True}
        h = win.hist[idx]
        cell = {"n": n}
        for key, q in (("p50", 0.50), ("p90", 0.90), ("p99", 0.99)):
            v, b = self._quantile(h, q, win.under[idx], win.over[idx])
            cell[key] = v
            if b:
                cell[key + "_bound"] = b
        cell["underflow"] = win.under[idx]
        cell["overflow"] = win.over[idx]
        return cell

    def _report_window(self, win: _Window, start) -> dict:
        n = win.n_completed
        if n < self.k_min:
            # Nothing but the fact of suppression leaves a suppressed window.
            return {"window_start": start, "suppressed": True}
        out = {"window_start": start, "suppressed": False, "completed": n}
        for idx, name in enumerate(STAGE_NAMES):
            out[name] = self._stage_cell(win, idx, win.stage_n[idx])
        out["end_to_end"] = self._stage_cell(win, LAST_CODE, n)
        out["retries"] = win.retries
        out["failures"] = win.failures
        out["unresolved"] = win.unresolved
        out["H_L"] = entropy_nats(win.hist[LAST_CODE])
        out["H_exit"] = entropy_nats(win.stage_time)
        return out

    def report(self, window_id: int) -> dict:
        return self._report_window(self._windows[window_id], window_id * self.window_s)

    def pooled(self, window_ids=None) -> dict:
        """Merge several windows into one report (used for long runs). window_start is None."""
        ids = window_ids if window_ids is not None else self.window_ids()
        merged = _Window(self.bins.n)
        for w in ids:
            src = self._windows[w]
            for s in range(LAST_CODE + 1):
                hs, hm = src.hist[s], merged.hist[s]
                for i, c in enumerate(hs):
                    if c:
                        hm[i] += c
                merged.under[s] += src.under[s]
                merged.over[s] += src.over[s]
            for s in range(LAST_CODE):
                merged.stage_time[s] += src.stage_time[s]
                merged.stage_n[s] += src.stage_n[s]
            merged.n_completed += src.n_completed
            merged.retries += src.retries
            merged.failures += src.failures
            merged.unresolved += src.unresolved
        return self._report_window(merged, None)
