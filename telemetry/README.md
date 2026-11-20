# Phase 1 telemetry reference pipeline

This folder holds the reference implementation of the Phase 1 measurement, and the tests that show what it does and does not do. It depends only on the Python standard library, apart from the lock benchmark (needs PostgreSQL, psycopg and pixeltable_pgserver) and the charts (needs matplotlib).

## What is here

* pipeline.py: streaming aggregation of lifecycle events into histograms, delay percentiles, retry and failure counts, H_L, and a descriptive entropy of stage durations booked at stage exit (H_exit, which is not the registered in flight occupancy statistic). Windows, and individual stage figures, under 50 contributing transactions are suppressed. See the contracts in the pipeline docstring.
* synthetic.py: a lifecycle generator with known ground truth.
* check_pipeline.py: 22 self checks. Run `python3 check_pipeline.py`.
* bench_scaling.py: cost per event at 50,000 to 3,200,000 events. Run `python3 bench_scaling.py`.
* bench_locks.py: a PostgreSQL test of write latency and lock waits with and without the pipeline, and with a deliberate lock as a control.
* make_charts.py: draws the two charts from the saved results.
* results/: the saved raw results and charts from the run described below.

## Results recorded on 5 November 2026 (pipeline version 0.2)

Check results: 22 of 22 pass (version 0.3, 9 November 2026; the 20 checks of version 0.2 plus C21 and C22). Version 0.1 (31 October 2026) passed 12 of 12 and recorded 0.58 to 0.67 microseconds per event and 2.75 ms against 2.92 ms. An external review on 4 November found eight weaknesses, which version 0.2 fixes or relabels. See REVIEWERS.md. The numbers below are a rerun on version 0.2 on a noisier machine session.

Cost per event: 0.95 to 1.35 microseconds, flat from 50,000 to 3,200,000 events.

Lock test: PostgreSQL 16.14, four writers, 800 transactions per second, five repetitions of 30 seconds each, median 99th percentile write latency.

| Condition | 99th percentile write latency | Deadlocks |
|:---|---:|---:|
| No pipeline | 3.20 ms | 0 |
| Read only pipeline | 3.33 ms | 0 |
| Deliberate table lock (control) | 159.74 ms | 0 |

Lock waits recorded without the pipeline and with it were writers waiting for other writers. The control run adds waits on the table itself, which shows the test can detect locking.

## Second run on Google Colab, 10 November 2026 (run by the author)

The same code was run on a different machine, using the notebook cells described in the repository history: 22 of 22 pipeline checks, 28 of 28 and 19 of 19 mathematics checks, and 13 S1 tests passed. The raw output is in `results/colab_run_20261110.log`.

Cost per event rose from 1.79 to 2.04 microseconds between 50,000 and 3,200,000 events. That machine is slower than the first one, and the cost stayed close to flat.

Lock test, 250 transactions per second, three repetitions of 20 seconds, median 99th percentile write latency:

| Condition | 99th percentile write latency | Deadlocks |
|:---|---:|---:|
| No pipeline | 3.99 ms (3.67 to 4.59) | 0 |
| Read only pipeline | 4.23 ms (4.10 to 4.31) | 0 |
| Deliberate table lock (control) | 151.89 ms (149.03 to 152.70) | 0 |

Table lock waits appeared only in the control. This was run by the author, so it shows the result repeats on a second machine. It is not an independent run.

## Cross check on real Ethereum data, 20 November 2026 (run by the author)

Script: engine_crosscheck.py. Notebook and results: results/. The 28 days of public Ethereum data (dataset D2, 25,155,158 transactions) were fed to this pipeline as lifecycle events: received at the arrival time, then the four later stage events at the inclusion time. Completion before arrival plus 1 ms was set to arrival plus 1 ms, as in Amendment A1.1. The end to end histogram of every five minute window was compared with an independent numpy calculation that uses the same bins and books each delay in the window of its completion time.

| Item | Pipeline | Independent |
|:---|---:|---:|
| Windows compared | 8,064 | 8,064 |
| Windows with identical histograms | 8,064 | |
| Completed transactions | 24,769,919 | 24,769,919 |
| Unresolved transactions | 385,239 | 385,239 |
| Events processed | 124,234,834 | |
| Events rejected as anomalies | 0 | |

Result: match in every window. The run took 417 seconds on Google Colab, including reading the files, so it is not a figure for cost per event.

What this shows: the streaming bookkeeping (window assignment, open transaction table, expiry, counting) is correct on 25 million real records. What it does not show: stage durations, retries, failures, webhooks and queue length, because the dataset has two timestamps only; and the choice of bins, because both calculations use the same bin formula.

## Limits

The load is synthetic. It ran on a single shared machine with two cores. The tests show that the pipeline takes no write locks and did not slow writers in this workload and has a constant cost per event. They do not show how any particular production system behaves. Repeat the lock test on your own replica before relying on it.

The pipeline does not read amounts, balances, names, phone numbers or account numbers, and it contains no economic layer. Check 11 scans the source for imports and names. It is not a privacy or security review. Transaction identifiers must be pseudonymised by the operator before they reach the pipeline.

Licence: MIT.
