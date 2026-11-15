# S1 result: Not supported

Registered test S1 (also called test 6), run once on dataset D2 (Ethereum, 16 October to 12 November 2026) on 15 November 2026 at 16:00 UTC. Outcome under the registered decision rule: **Not supported**.

## The question

Does latency entropy H_L predict the 99th percentile latency of the next window beyond a strong queueing based model? G1 is the strong model without entropy. G2 is G1 plus entropy features. R is one minus the pinball loss of G2 divided by the pinball loss of G1, at the 0.99 quantile, on the original scale.

## Result

| Item | Value |
| --- | --- |
| Rows | 25,155,158 |
| Window length | 300 s (fixed in Amendment A3) |
| Windows: train, validation, test | 4,544, 1,317, 1,328 |
| Test period in bootstrap blocks | 4.6 (eligible under A1) |
| Pinball loss G1 | 103.2676 |
| Pinball loss G2 | 101.2339 |
| R | +0.0197 |
| 95% circular block bootstrap interval for R | -0.2519 to +0.1012 |
| One sided Diebold Mariano p (Holm adjusted, one dataset) | 0.3675 |
| Support rule needs | p below 0.05, R at least 0.05, interval lower bound above 0 |
| Rules met | none of the three |

Baselines (mean pinball loss): P0 133.73, P1 127.14, Q1 131.14, Q2 862.29. G1 is about 19 percent below P1 and 21 percent below Q1, so the model entropy had to beat is strong.

## What this means

On this dataset, adding latency entropy did not improve the forecast of the next window's 99th percentile beyond G1 by an amount the registered rule counts as support. The point estimate is small and positive (R about 2 percent). The interval is wide, from a loss of 25 percent to a gain of 10 percent, with 4.6 blocks of test data. The test therefore does not show that entropy has no value. It shows that this registered test, on this data, did not find any.

## Secondary analyses (no decision rule)

| Analysis | R | Interval | p |
| --- | --- | --- | --- |
| Drop clipped rows | +0.0471 | -0.0557 to +0.1458 | 0.1458 |
| Value weighted entropy | +0.0254 | -0.1978 to +0.0843 | 0.3274 |
| Log scale | -0.0043 | not reported | 0.5354 |
| Surge windows (239 windows) | -0.0390 | not reported | not reported |
| Unresolved as 24 hours | 0.0000 | 0 to 0 | 1.0000 |

The 24 hour variant is degenerate: every forecast is constant, so it carries no information. The Brier score (binary forecast that the next window exceeds twice the training median) is also uninformative: G1 and G2 both score 0.9277 because both forecast an exceedance almost every time. Neither was changed after the rehearsal.

## Limits

1. One dataset, one chain, 28 days. D1 (Bitcoin) was not retrievable and was treated as ineligible under A1.
2. The Q2 baseline (Pollaczek Khinchine) is constant on this data, because arrivals times mean latency is above 1 in every window. It is a registered formula that saturates here. Q1 and the lag features carry the queueing baseline.
3. 8.92 percent of rows have a completion time before arrival plus 1 ms and were clipped to 1 ms. Dropping them (secondary) moves R to +0.047, still not significant.
4. The unresolved share falls over the period (2.15 percent in the first seven days, 0.72 percent in the last seven, from A3), so training days have more unresolved transactions than test days. The share across the whole run was 1.53 percent. Unresolved transactions are excluded from targets.
5. The best settings for G1 (400 iterations, 0.05 learning rate) and G2 (150 iterations, 0.05 learning rate) sit at the edge of the registered grid, which is fixed.
6. The test windows are autocorrelated. The block bootstrap accounts for that, and that is why the interval is wide.

## Record of exactly what ran

* Code freeze tag: s1-code-freeze-v1, commit a1d8e582ab21839b105efdb86eb5aee383ac8b97, Zenodo DOI 10.5281/zenodo.24248900.
* Manifest SHA256: 12ca0cb8ee24cdd164a05bc247048682a8467151a36d9b889c42b22cdbf01148.
* A3 constants SHA256: 9d036dec92621e3060ae234b202f374e12faeb0619e44c196115df615bb7ea5b.
* Code SHA256: run_d2.py 6ae775f3..., run.py 7551b9e7..., windows.py 70979efe..., adapters.py c74b0595..., stats.py d3fbd74f... (full values in s1_result.json). These are identical to the rehearsal run.
* Seed 20261031. Primary run time 134 seconds.
* The run was made once. No setting, threshold or model was changed after the rehearsal. The rehearsal used training days only.

## Files

s1_result.json and s1_result.txt in this folder are the unedited outputs of the run. The notebook Sovereign_Negentropy_S1_Run.ipynb is the record of the Colab session.

## Next

Independent reproduction by a reviewer is invited and has no deadline. Any further test of entropy needs a new registered hypothesis on new data. This result is not re run and not reinterpreted.
