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

## Limits

The load is synthetic. It ran on a single shared machine with two cores. The tests show that the pipeline takes no write locks and did not slow writers in this workload and has a constant cost per event. They do not show how any particular production system behaves. Repeat the lock test on your own replica before relying on it.

The pipeline does not read amounts, balances, names, phone numbers or account numbers, and it contains no economic layer. Check 11 scans the source for imports and names. It is not a privacy or security review. Transaction identifiers must be pseudonymised by the operator before they reach the pipeline.

Licence: MIT.
