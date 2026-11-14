# Power study on synthetic data (draft, updated 14 November 2026)

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

Note added after Amendment A1: these runs had a bootstrap block of 240 windows over 576 test windows, which is
2.4 blocks. Under A1 such a dataset is ineligible. So the study measures how often the rule fires on small
samples, not how often an eligible test would. A rerun at eligible sizes is needed.

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

## Rerun at eligible sizes (14 November 2026)

Setup: 72 hours of synthetic arrivals at rate 6 per second, window 30 seconds, block of 120 windows, about 1,700 scored test windows, so about 14 blocks. Every run is eligible under Amendment A1. The registered rule is unchanged. The script is `s1/power.py` run with these sizes. The planted signal is invented.

| Planted strength | Replicates | Registered rule says Supported | R at least 0.05 | Raw p below 0.05 | Interval lower bound above 0 | Mean R |
|:---|:---|:---|:---|:---|:---|:---|
| 0 (none) | 6 | 0 of 6 | 0 of 6 | 2 of 6 | 0 of 6 | +0.008 |
| 0.5 | 1 | 0 of 1 | 1 of 1 | 0 of 1 | 0 of 1 | +0.105 |
| 1.0 | 6 | 0 of 6 | 1 of 6 | 0 of 6 | 0 of 6 | +0.002 |
| 1.5 | 6 | 0 of 6 | 3 of 6 | 1 of 6 | 0 of 6 | +0.035 |

What this shows:

1. With no planted signal the rule never said Supported. The false positive rate is low, which is what the bootstrap rule was meant to give.
2. With a planted signal the rule also never said Supported. The interval lower bound was never above zero. The rule is conservative: it needs a real gain of about 5 percent or more in pinball loss, held across blocks.
3. A modest real effect would most likely give "Not supported" or "Inconclusive". Read those outcomes with the limits report next to them.

What it does not show: 6 runs per row, and one run at strength 0.5, are far too few to estimate power. The planted effect size is an invention. This is a check of the machinery and of how demanding the rule is. It is not a reason to change a threshold, and none is changed.
