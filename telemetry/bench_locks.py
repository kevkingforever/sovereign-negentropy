"""Write lock experiment against a real PostgreSQL server.

Question: does the Phase 1 pipeline create write locks or slow the ledger's writers?

Design
    A small ledger (accounts, transactions, lifecycle events) is loaded by several writer
    processes at a fixed offered rate. Each ledger transaction updates two hot account rows
    and inserts five lifecycle events, so writers genuinely contend for row locks.
    Latency is measured from the scheduled arrival time, so queueing delay is counted.

    Three conditions, run in random order, several repetitions each:
      baseline          writers only
      pipeline          writers plus the Phase 1 pipeline, reading the event table once per
                        second inside a read only, repeatable read snapshot
      blocking_control  a deliberately bad design: a reader that takes a table lock (SHARE
                        mode) and holds it while it computes. It shows that this test can
                        detect locking when it exists.

    Measured: writer latency quantiles, throughput, samples of backends waiting on locks
    (every 50 ms), deadlocks, lock modes held by the pipeline session, pipeline processor
    time and memory, and whether the pipeline recovered the lifecycle statistics.

Limits
    One small shared container, a synthetic workload, direct reads from the primary (the
    conservative case: production would read a replica or a log export). It shows the
    mechanism and relative effects. It does not predict any operator's production numbers.
"""
from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import os
import platform
import random
import resource
import statistics
import sys
import threading
import time

import psutil
import psycopg

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pipeline as pl  # noqa: E402
import synthetic as syn  # noqa: E402

N_ACCOUNTS = 50
SETUP_SQL = [
    "DROP TABLE IF EXISTS tx_event",
    "DROP TABLE IF EXISTS tx",
    "DROP TABLE IF EXISTS account",
    "CREATE TABLE account (id int PRIMARY KEY, balance numeric(18,2) NOT NULL)",
    f"INSERT INTO account SELECT g, 1000000 FROM generate_series(1,{N_ACCOUNTS}) g",
    "CREATE TABLE tx (id bigserial PRIMARY KEY, src int, dst int, status smallint, "
    "created_at timestamptz DEFAULT clock_timestamp())",
    "CREATE TABLE tx_event (id bigserial PRIMARY KEY, tx_id bigint NOT NULL, code smallint NOT NULL, "
    "ts double precision NOT NULL, inserted_at timestamptz DEFAULT clock_timestamp())",
]
RESET_SQL = [
    "TRUNCATE tx_event, tx RESTART IDENTITY",
    "UPDATE account SET balance = 1000000",
]

READ_SQL = (
    "SELECT id, tx_id, code, ts FROM tx_event "
    "WHERE id > %s AND inserted_at <= clock_timestamp() - interval '1 second' "
    "ORDER BY id LIMIT 20000"
)


def writer(uri, wid, rate, warm, duration, seed, out_q):
    rng = random.Random(seed)
    conn = psycopg.connect(uri, autocommit=False)
    cur = conn.cursor()
    cur.execute("SET synchronous_commit = off")
    conn.commit()
    t_start = time.perf_counter()
    end = t_start + warm + duration
    t_sched = t_start
    lats, n, dl = [], 0, 0
    while True:
        t_sched += rng.expovariate(rate)
        if t_sched >= end:
            break
        now = time.perf_counter()
        if t_sched > now:
            time.sleep(t_sched - now)
        a = min(N_ACCOUNTS, 1 + int(rng.expovariate(1.0 / 6.0)))
        b = min(N_ACCOUNTS, 1 + int(rng.expovariate(1.0 / 6.0)))
        if a == b:
            b = a % N_ACCOUNTS + 1
        lo, hi = (a, b) if a < b else (b, a)
        evs = syn.lifecycle(rng, time.time())
        try:
            cur.execute("INSERT INTO tx(src,dst,status) VALUES (%s,%s,0) RETURNING id", (lo, hi))
            txid = cur.fetchone()[0]
            cur.execute("UPDATE account SET balance = balance - 10 WHERE id = %s", (lo,))
            cur.execute("UPDATE account SET balance = balance + 10 WHERE id = %s", (hi,))
            params = []
            for code, ts, _, _ in evs:
                params += [txid, code, ts]
            cur.execute("INSERT INTO tx_event(tx_id,code,ts) VALUES " + ",".join(["(%s,%s,%s)"] * len(evs)), params)
            conn.commit()
        except psycopg.errors.DeadlockDetected:
            conn.rollback()
            dl += 1
            continue
        done = time.perf_counter()
        if t_sched - t_start >= warm:
            lats.append(done - t_sched)
        n += 1
    conn.close()
    out_q.put(("writer", wid, lats, n, dl))


def reader(uri, mode, stop_evt, out_q, hold_s, poll_s):
    conn = psycopg.connect(uri, autocommit=True)
    pipe = pl.Pipeline(window_s=5.0, k_min=50)
    me = psutil.Process()
    cpu0 = me.cpu_times()
    watermark = 0
    lock_seen = {}
    polls = 0
    consumed = 0
    last_nonempty = time.time()
    while True:
        stopping = stop_evt.is_set()
        if mode == "pipeline":
            conn.execute("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY")
        else:
            conn.execute("BEGIN")
            conn.execute("LOCK TABLE tx_event IN SHARE MODE")
        rows = conn.execute(READ_SQL, (watermark,)).fetchall()
        if polls % 5 == 0:
            for lt, md, c in conn.execute(
                "SELECT locktype, mode, count(*) FROM pg_locks WHERE pid = pg_backend_pid() GROUP BY 1,2"
            ).fetchall():
                lock_seen[f"{lt}:{md}"] = max(lock_seen.get(f"{lt}:{md}", 0), c)
        for rid, tx_id, code, ts in rows:
            pipe.process(tx_id, code, ts)
        if mode != "pipeline":
            time.sleep(hold_s)  # stands in for a long analytic job that keeps its table lock
        conn.execute("COMMIT")
        if rows:
            watermark = rows[-1][0]
            consumed += len(rows)
            last_nonempty = time.time()
        polls += 1
        if stopping and (not rows) and time.time() - last_nonempty > 1.5:
            break
        time.sleep(poll_s)
    cpu1 = me.cpu_times()
    pooled = pipe.pooled()
    out_q.put((
        "reader", mode, consumed, polls, lock_seen,
        (cpu1.user - cpu0.user) + (cpu1.system - cpu0.system),
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0,
        pooled, pipe.anomalies, pipe.open_transactions,
    ))


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]


def run_condition(uri, cond, args, rep):
    with psycopg.connect(uri, autocommit=True) as c:
        for s in RESET_SQL:
            c.execute(s)
        c.execute("VACUUM account")
        dl0 = c.execute("SELECT deadlocks FROM pg_stat_database WHERE datname = current_database()").fetchone()[0]

    q = mp.Queue()
    stop_evt = mp.Event()
    procs = []
    rd = None
    if cond != "baseline":
        rd = mp.Process(target=reader, args=(uri, cond, stop_evt, q, args.hold_ms / 1000.0, args.poll_s))
        rd.start()
    per_w_rate = args.rate / args.writers
    for w in range(args.writers):
        p = mp.Process(target=writer, args=(uri, w, per_w_rate, args.warm, args.duration, 1000 * rep + w, q))
        procs.append(p)
    # sampler of lock waits
    waits = {}
    samples = [0]
    stop_s = threading.Event()

    def sample():
        sc = psycopg.connect(uri, autocommit=True)
        while not stop_s.is_set():
            for we, n in sc.execute(
                "SELECT wait_event, count(*) FROM pg_stat_activity WHERE datname = current_database() "
                "AND pid <> pg_backend_pid() AND wait_event_type = 'Lock' GROUP BY 1"
            ).fetchall():
                waits[we] = waits.get(we, 0) + n
            samples[0] += 1
            time.sleep(0.05)
        sc.close()

    th = threading.Thread(target=sample)
    th.start()
    for p in procs:
        p.start()
    out = []
    for _ in procs:  # drain results before joining, so large payloads cannot block the children
        out.append(q.get(timeout=300))
    for p in procs:
        p.join()
    time.sleep(2.0)
    stop_evt.set()
    if rd:
        out.append(q.get(timeout=300))
        rd.join()
    stop_s.set()
    th.join()

    lats, n_tx, deadlocks_w = [], 0, 0
    reader_out = None
    for item in out:
        if item[0] == "writer":
            lats += item[2]
            n_tx += item[3]
            deadlocks_w += item[4]
        else:
            reader_out = item
    with psycopg.connect(uri, autocommit=True) as c:
        dl1 = c.execute("SELECT deadlocks FROM pg_stat_database WHERE datname = current_database()").fetchone()[0]
        written = c.execute("SELECT count(*) FROM tx_event").fetchone()[0]
        rows = c.execute("SELECT tx_id, code, ts FROM tx_event ORDER BY id").fetchall()
    res = {
        "condition": cond,
        "rep": rep,
        "tx_committed": n_tx,
        "p50_ms": pct(lats, 0.50) * 1000,
        "p95_ms": pct(lats, 0.95) * 1000,
        "p99_ms": pct(lats, 0.99) * 1000,
        "p999_ms": pct(lats, 0.999) * 1000,
        "max_ms": max(lats) * 1000,
        "throughput_tx_s": n_tx / (args.warm + args.duration),
        "lock_wait_samples": dict(waits),
        "sampler_ticks": samples[0],
        "deadlocks_db": dl1 - dl0,
        "deadlocks_writers": deadlocks_w,
        "events_written": written,
    }
    if reader_out:
        (_, mode, consumed, polls, lock_seen, cpu_s, rss_mb, pooled, anomalies, open_tx) = reader_out
        res["reader"] = {
            "events_consumed": consumed,
            "polls": polls,
            "locks_held_by_reader": lock_seen,
            "cpu_seconds": cpu_s,
            "max_rss_mb": rss_mb,
            "anomalies": anomalies,
            "open_transactions_at_end": open_tx,
        }
        if mode == "pipeline":
            # exact batch statistics from the stored events, compared with the pipeline output
            by_tx = {}
            for tx_id, code, ts in rows:
                by_tx.setdefault(tx_id, {})[code] = ts
            full = [d for d in by_tx.values() if len(d) == 5]
            rec = {}
            worst_vs_exact, worst_vs_true = 0.0, 0.0
            for s in range(4):
                durs = sorted(d[s + 1] - d[s] for d in full)
                ex99 = durs[min(len(durs) - 1, int(0.99 * len(durs)))]
                ex50 = durs[len(durs) // 2]
                got99 = pooled[pl.STAGE_NAMES[s]]["p99"]
                got50 = pooled[pl.STAGE_NAMES[s]]["p50"]
                rec[pl.STAGE_NAMES[s]] = {
                    "pipeline_p50": got50, "exact_p50": ex50, "true_p50": syn.true_median(s),
                    "pipeline_p99": got99, "exact_p99": ex99, "true_p99": syn.true_quantile(s),
                }
                worst_vs_exact = max(worst_vs_exact, abs(got99 - ex99) / ex99, abs(got50 - ex50) / ex50)
                worst_vs_true = max(worst_vs_true, abs(got99 - syn.true_quantile(s)) / syn.true_quantile(s))
            res["recovery"] = {
                "complete_transactions": len(full),
                "stage_statistics": rec,
                "worst_relative_error_vs_exact": worst_vs_exact,
                "worst_p99_relative_error_vs_analytic": worst_vs_true,
                "completeness": consumed / max(1, written),
            }
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=4)
    ap.add_argument("--duration", type=float, default=30.0)
    ap.add_argument("--warm", type=float, default=3.0)
    ap.add_argument("--rate", type=float, default=250.0, help="total offered transactions per second")
    ap.add_argument("--writers", type=int, default=4)
    ap.add_argument("--hold-ms", dest="hold_ms", type=float, default=150.0)
    ap.add_argument("--poll-s", dest="poll_s", type=float, default=1.0)
    ap.add_argument("--conds", default="baseline,pipeline,blocking_control")
    ap.add_argument("--out", default=os.path.join(HERE, "results", "locks_raw.json"))
    ap.add_argument("--pgdir", default="")
    args = ap.parse_args()

    import pixeltable_pgserver as pgserver
    import tempfile
    pgdir = args.pgdir or tempfile.mkdtemp(prefix="pgbench_")
    os.makedirs(pgdir, exist_ok=True)
    srv = pgserver.get_server(pgdir, cleanup_mode=None)
    uri = srv.get_uri()
    with psycopg.connect(uri, autocommit=True) as c:
        for s in SETUP_SQL:
            c.execute(s)
        version = c.execute("select version()").fetchone()[0]

    conds = args.conds.split(",")
    rng = random.Random(20261031)
    results = []
    for rep in range(args.reps):
        order = conds[:]
        rng.shuffle(order)
        for cond in order:
            t0 = time.time()
            r = run_condition(uri, cond, args, rep)
            results.append(r)
            print(f"rep {rep} {cond:17s} p50={r['p50_ms']:.2f} p99={r['p99_ms']:.2f} p99.9={r['p999_ms']:.2f} "
                  f"tx/s={r['throughput_tx_s']:.0f} lockwait={r['lock_wait_samples']} dl={r['deadlocks_db']} "
                  f"({time.time()-t0:.0f}s)", flush=True)
            os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
            json.dump({"meta": {
                "postgres": version, "python": platform.python_version(), "cpus": os.cpu_count(),
                "args": vars(args), "note": "single shared container, synthetic workload"},
                "runs": results}, open(args.out, "w"), indent=1)
    srv.cleanup()


if __name__ == "__main__":
    main()
