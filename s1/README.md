# S1 analysis code (draft v0.2, NOT FROZEN)

Code for the registered S1 comparison: does the entropy of the latency distribution
predict the next window's 99th percentile latency beyond a queueing based model.
It reads rows of arrival time and completion time. It has an adapter for D2 (adapters.py) and the script that sets the A3 constants (freeze_a3.py). There is no D1 adapter: D1 could not be retrieved (Amendment A2).

Status: public draft. Nothing here has touched real data. The registered S1 code is only the
version that the code freeze tag points to. Until that tag exists, this folder can change.
Every change is visible in the commit history.

## Layout

    config.py     every registered constant in one place
    windows.py    windows, frozen bins, H_L, G1 and G2 features, targets
    queueing.py   baselines P0, P1, Q1, Q2
    models.py     G1 and G2 learner, validation grid, seed
    stats.py      pinball loss, R, Diebold Mariano, block bootstrap, Holm
    run.py        split, purge, fit, test, decision rule
    synth.py      synthetic data for testing the machinery only
    limits.py     limits report printed with every run
    adapters.py   D2 files to arrival and completion times, with a manifest check
    freeze_a3.py  Amendment A3: window length, bin edges and unresolved share, from the training period only
    run_d2.py     the registered S1 run on D2 and a rehearsal mode on training days only
    tools/        fingerprint_files.py (names, sizes, SHA256, row counts only) and its 12 checks
    harness.py    null and planted runs on synthetic data
    tests/        25 tests

Run from the repository root:

    python3 -m pip install numpy scipy scikit-learn pytest
    python3 -m pytest -q s1/tests
    python3 -m s1.harness 48

Amendment A1 (preregistration/AMENDMENT_A1.md) adds two things to the code: a dataset is eligible
only if its test period spans at least 3 bootstrap blocks, and completion before arrival is clipped to a 1 millisecond
latency instead of dropping the row.

## What the tests prove

1. No lookahead. Deleting every arrival and completion after a forecast origin leaves
   all features for that origin unchanged (s1/tests/test_no_lookahead.py).
2. The statistics behave. Pinball values, Holm adjustment, one sided Diebold Mariano
   size under the null, bootstrap interval, and the three outcome labels.
3. A synthetic null produces no support, on two datasets, through the full path.

## What is not yet shown

Detection of a real signal. On planted synthetic data G2 sometimes beats G1 (R about
+0.04 to +0.06) and sometimes does not. The machinery can produce a positive R, but
power at realistic sizes is not demonstrated. A proper power study comes next.

## Findings that need decisions before the freeze

1. Overprediction. A 0.99 pinball loss barely punishes predicting too high. With a few
   hundred training windows, validation picks models that predict close to the maximum.
   D1 is the exposed dataset. The data freeze amendment should state the minimum number
   of training windows, and what is reported if G1 and G2 both collapse to a near
   constant.
2. Learner details (reviewer item 4). The learner is fitted to ln(target) and predictions
   are exponentiated. Loss is always computed on the original scale. Grid and refit rule
   (train only) are in models.py.
3. Queueing estimators (reviewer item 3). D1 and D2 record total latency, not service
   time. Two estimators are coded and the default is "sojourn". On public blockchain data
   Q1 and Q2 may become constant features.
4. Purge (reviewer item 5). Training and validation windows whose target is unresolved at
   the split edge are dropped when purge is on (default).
5. Negative latencies (reviewer item 2). windows.Rows refuses any row that completes
   before it arrives. The adapter must apply the registered rule first.

## Amendment A3 (training period constants)

Run in Colab with the 28 files that Amendment A2 fixes:

    python3 -m s1.freeze_a3 --folder FOLDER --manifest preregistration/manifests/manifest_d2.json --out a3_constants

It first checks every file against the manifest and stops if one differs. It then reads arrival and inclusion time
for all rows. The window length and bin edges use only rows that arrive before the end of the training period (the
first 60 percent of the span from the first to the last arrival), with completions at or before that end. For all days
it reports the share of rows with no inclusion time, by arrival day and by arrival hour in UTC (Amendment A1.1).
tests/test_a3.py shows that changing every validation and test outcome leaves the window length and bin edges unchanged.
The tools/ checks are run as scripts, not through pytest: `python3 s1/tools/test_fingerprint.py`.

## The run (run_d2.py)

    python3 -m s1.run_d2 --mode rehearsal --days 14 --folder FOLDER --manifest preregistration/manifests/manifest_d2.json --a3 preregistration/a3/a3_constants.json --out rehearsal
    python3 -m s1.run_d2 --mode run --folder FOLDER --manifest preregistration/manifests/manifest_d2.json --a3 preregistration/a3/a3_constants.json --out s1_result

The rehearsal runs the same code on the first N days only, all inside the training period, cut into their own pieces.
Its output says NOT A RESULT. Only bugs may be fixed after it, and no setting changes. The run mode refuses to start
unless the code is at the tag s1-code-freeze-v1, and stops if the manifest or the A3 file differs from the registered
SHA256, or if the window length and bin edges recomputed from the training period differ from Amendment A3.

Secondary results, reported with no decision rule, each in its own guarded step so that one cannot stop the report of the
primary: rows with negative latency dropped, the 24 hour latency treatment of unresolved transactions, and the value
weighted entropy (the registered weight is the transaction value column). The natural log scale, the surge windows and
the Brier score come with the primary run. Interpretations, fixed before any held out data are opened: surge windows are
test windows whose origin window has more arrivals than the 95th percentile of training windows; the Brier score is
computed for a binary forecast (the model forecast exceeds twice the training median of the target) against the event
(the realised value exceeds the same threshold).
