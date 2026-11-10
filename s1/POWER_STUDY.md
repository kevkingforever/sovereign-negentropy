# Power study on synthetic data (draft, 10 November 2026)

Script: `python3 -m s1.power OUT.jsonl REPS HOURS STRENGTH ...`. Synthetic data only. The planted
signal is invented, so this says nothing about the real world. It tests the machinery and the
registered rule.

Setup: 24 hours of synthetic arrivals, window 30 seconds, 576 test windows, registered rule
(one sided Diebold Mariano p below 0.05, R at least 0.05, bootstrap interval above zero).

| Planted strength | Replicates | Registered rule says Supported | Raw p below 0.05 | Mean R |
|:---|:---|:---|:---|:---|
| 0 (none) | 12 | 1 of 12 | 1 of 12 | +0.027 |
| 0.5 | 12 | 4 of 12 | 5 of 12 | +0.086 |
| 1.0 | 12 | 1 of 12 | 2 of 12 | +0.020 |
| 1.5 | 12 | 2 of 12 | 2 of 12 | minus 0.056 |

A second run of 8 replicates at strength 0 and 1.0 scored the same forecasts on the log scale as a
secondary, descriptive check: no signal 0 of 8 below p 0.05, signal 4 of 8 (raw scale 0 of 8 and 2 of 8).

## What this shows

1. No planted signal: the rule said Supported in 1 of 12 runs. That is about what a 5 percent test
   gives, and the sample is small.
2. Detection is unreliable and does not rise with signal strength. With this much data, even a strong
   planted signal is caught in only a minority of runs. Adding the entropy inputs also adds noise.
3. The loss on the raw latency scale is dominated by a few very large values. The log scale
   check hints at better sensitivity, with 8 replicates per row, which is too few to be sure.

## What it does not show

It does not show how much data the real test needs. It does not show that the registered rule works
well on real data. 12 replicates per row give wide error bars. A larger study is needed before any
claim about power, and the real datasets have different shapes from this one.

## Consequences for S1

Report limits next to every result. Do not read a "not supported" outcome from a small dataset as
evidence against the idea. The Ethereum dataset (more windows) is the better chance of a clear answer.
