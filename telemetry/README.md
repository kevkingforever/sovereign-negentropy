# Phase 1 telemetry reference pipeline

This folder holds the reference implementation of the Phase 1 measurement, and the tests that show what it does and does not do. It depends only on the Python standard library, apart from the lock benchmark (needs PostgreSQL, psycopg and pixeltable_pgserver) and the charts (needs matplotlib).

## What is here

* pipeline.py: streaming aggregation of lifecycle events into histograms, delay percentiles, retry and failure counts, and the two entropy figures H_L and H_S. Windows under 50 completed transactions are suppressed.
* synthetic.py: a lifecycle generator with known ground truth.
* check_pipeline.py: 12 self checks. Run `python3 check_pipeline.py`.
* bench_scaling.py: cost per event at 50,000 to 3,200,000 events. Run `python3 bench_scaling.py`.
* bench_locks.py: a PostgreSQL test of write latency and lock waits with and without the pipeline, and with a deliberate lock as a control.
* make_charts.py: draws the two charts from the saved results.
* results/: the saved raw results and charts from the run described below.

## Results recorded on 31 October 2026

Check results: 12 of 12 pass.

Cost per event: 0.58 to 0.67 microseconds, flat from 50,000 to 3,200,000 events.

Lock test: PostgreSQL 16.14, four writers, 800 transactions per second, five repetitions of 30 seconds each, median 99th percentile write latency.

| Condition | 99th percentile write latency | Deadlocks |
|:---|---:|---:|
| No pipeline | 2.92 ms | 0 |
| Read only pipeline | 2.75 ms | 0 |
| Deliberate table lock (control) | 155.24 ms | 0 |

Lock waits recorded without the pipeline and with it were writers waiting for other writers. The control run adds waits on the table itself, which shows the test can detect locking.

## Limits

The load is synthetic. It ran on a single shared machine with two cores. The tests show that the design takes no write locks and has a constant cost per event. They do not show how any particular production system behaves. Repeat the lock test on your own replica before relying on it.

The pipeline does not read amounts, balances, names, phone numbers or account numbers, and it contains no economic layer. Check 11 enforces this by inspecting the source.

Licence: MIT.
