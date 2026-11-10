---
title: "Amendment A1 to the Pre Registration of Empirical Tests, Version 1.1"
subtitle: "Design decisions for S1, made before any validation or test data are loaded"
author: "Kevin Ansong. Status: DRAFT for reviewer read, not yet registered"
date: "Draft of 10 November 2026"
---

# 1. Status and purpose

This is a draft of Amendment A1. It is not registered. It changes nothing until it is committed, registered on OSF and dated.

The registration (PREREGISTRATION_v1_1, section 11) allows amendments before the data freeze amendment, each versioned and dated. A1 is that kind of amendment. It fixes design choices that the registration left open and corrects two rules that cannot work with the datasets as planned. After A1 comes the data freeze amendment (A2), which records file versions, checksums, the chosen window length and the bin edges.

Registered file: preregistration/PREREGISTRATION_v1_1.pdf, SHA256 8a065dee4f3b365f0d592336074a9203e1bafab9f1dddcac1d3a25f0278fa1e0. A1 changes only what is listed in section 3. Everything else in the registration stands, including the primary loss, the 0.99 quantile, the 0.05 threshold, the minimum improvement R of 0.05, the seed 20261031, the 60, 20, 20 split and the Holm rule.

# 2. Data exposure before this amendment

No dataset has been downloaded or analysed. The author and one reviewer have seen a handful of public preview rows of the D1 dataset on its web page, and the public documentation of both datasets. No statistic has been computed from any real data. Everything in section 3 was decided from the registration text, the providers' documentation and synthetic data only.

# 3. Changes and decisions

Each item gives what the registration says, what A1 decides, why, and the effect on interpretation.

## 3.1 Bootstrap blocks and dataset eligibility (corrects a rule)

Registered: the 95 percent interval for R uses a circular block bootstrap with block length equal to the windows spanned by 24 hours.

Problem: the test period is the final 20 percent of the span, and the last 24 hours of it cannot be scored, because outcomes need 24 hours to resolve. For D1, a 7 day sample leaves about 0.4 days of test windows. For D2 over 14 days it leaves about 1.8 days. In both cases the test period holds fewer than two blocks. A bootstrap with one block only rotates the same series, so every resample returns almost the same R. The interval then has almost no width, and the third support condition (lower bound above 0) passes whenever R is positive.

Decision: a dataset is eligible only if its scored test period spans at least 3 bootstrap blocks. An ineligible dataset is reported in full but cannot support, and it is left out of the Holm correction and of the outcome. If neither dataset is eligible, the outcome is "Not testable".

Consequence for D1: a 7 day sample cannot meet the rule. At 60, 20, 20 with a 24 hour gap, a dataset needs a total span of about 20 days. D1 is therefore expected to be ineligible. It is still processed and reported as a descriptive check with its limits. The author will ask the provider for longer history. If a longer file arrives before the freeze, D1 is tested under the same rules. No dataset is added or swapped after the freeze.

Effect: the confirmatory decision will most likely rest on D2 alone. A "Supported" outcome then means support on one public dataset, and the report says so in the first paragraph.

## 3.2 Length of the D2 period (corrects a rule)

Registered: the most recent contiguous 14 days that are complete at the freeze date.

Decision: 28 contiguous days, ending 3 days before the freeze date. The end date uses no reference to outcomes. Reason: section 3.1. With 28 days the scored test period is about 4.6 days, which is at least 3 blocks. Size: the published daily CSV files are about 100 MB zipped, so about 3 GB in total. The pipeline reads them in chunks.

## 3.3 Latency below zero (new rule)

Registered: silent. Provider documentation says D2 inclusion delay can be negative, because block timestamps are set at the start of the slot.

Decision: a completion time earlier than arrival plus 1 millisecond is set to arrival plus 1 millisecond. The row stays. The number of rows changed is reported for every dataset and every day. Sensitivity analysis: the same comparison with those rows removed.

Reason: a negative value is timestamp noise, not a faster transaction. Removing rows because of their latency value would remove the fastest transactions and distort the distribution that the entropy measures. Clipping keeps the counts. Effect: D2 latencies are measured with 12 second slot granularity. Nothing finer is claimed.

## 3.4 D2 completion source (names the source the registration leaves open)

Registered: completion is the timestamp of the including block, joined by hash from canonical chain data, with the source named in the data freeze amendment.

Decision: use the inclusion fields published in the Mempool Dumpster files themselves: included block timestamp as completion, and the file's first seen timestamp as arrival. The provider states that these fields are filled by checking each transaction's inclusion status against an Ethereum execution node. The published page does not name the node provider. A transaction without inclusion fields is unresolved. No outside join is made.

Reason: one source removes a place where timestamps can fail to line up. Limitation, recorded: the provider fills inclusion fields when it merges each day, so a transaction included later than that may show as unresolved. The 3 day gap before the freeze date in section 3.2 limits the effect. A2 reports the unresolved share by day.

## 3.5 Queueing baselines

Registered: Q1 and Q2 from rates estimated over the last 6 windows. Service time is not observed in D1 or D2.

Decision: Q1 treats the mean observed latency m as the mean sojourn time, so Q1 equals ln(100) times m. The registered rule of 24 hours when arrivals are not below service does not arise under this estimator. Q2 uses the Pollaczek Khinchine mean with the first two moments of observed latency as service moments and the 24 hour value when utilisation reaches 1. On public chain data Q2 will often equal 24 hours. A feature that is constant in training is kept and reported in the limits.

## 3.6 Learner and tuning

Registered: gradient boosted quantile regression, pinball loss at 0.99, same learner, grid, budget and seeds for G1 and G2.

Decision: the scikit learn library class HistGradientBoostingRegressor with the quantile loss at 0.99, early stopping off, seed 20261031. The grid is every combination of learning rate 0.05 and 0.15, maximum depth 3 and 5, iterations 150 and 400, and minimum leaf size 10 and 30, so 16 settings. The same grid is used for G1 and G2. The setting with the lowest validation pinball loss is chosen, then the model is refit on the training period only. The learner is fitted to the natural log of the target and its forecasts are exponentiated. The 0.99 quantile of the log is the log of the 0.99 quantile, so the target is unchanged. Selection and testing always compute the pinball loss on the original scale.

## 3.7 Gaps between periods

Decision: a 24 hour gap. A training or validation window is dropped if its outcome would not be fully resolved before the period ends. A test window is scored only if its outcome is resolved before the data end. Features use only information at or before the forecast origin; the code has a test that deletes all later information and checks that no feature changes.

## 3.8 Inference details

* The Diebold Mariano p value uses the normal distribution and the registered bandwidth rule. If the long run variance estimate is zero or negative, p is set to 1.
* The bootstrap uses seed 20261031, 10,000 resamples and a percentile interval.
* The Holm correction is over eligible datasets only.
* Windows with no resolved arrival transaction are skipped. The first 5 windows have incomplete lags and are skipped.

## 3.9 Reporting rules, with no effect on decisions

* Every result carries a limits report: window counts, block count, share unresolved, constant features, settings at the edge of the grid, windows dropped by the gap.
* If G1 and G2 forecasts differ by less than 1 percent on average, the result is labelled "collapsed". The registered rules already give "not supported" in that case.
* Secondary results, with no decision rule: the loss scored on the natural log scale, the surge windows, the Brier score, value weighted entropy and the 24 hour latency treatment, all as registered, plus the log scale and the exclusion of negative rows from section 3.3.

# 4. What these changes cannot fix

* D2 latency is measured from one observer's first sighting to a block timestamp at 12 second granularity.
* A power study on synthetic data (s1/POWER_STUDY.md) shows that at around 24 hours of data the registered rule detects a planted signal only in some runs. A "not supported" result on limited data is not evidence against the idea.
* D1 is a 7 day sample and cannot carry the decision.
* If the outcome is "Supported", it supports one claim: the entropy features are carried into the Phase 1 registration as a candidate predictor. No claim about mechanism follows, as registered.

# 5. Order of events after approval

1. A reviewer records the SHA256 of the registered PDF, and the reply is kept.
2. A1 is committed and registered on OSF with the date.
3. The files are downloaded. Only the training period is used to set the window length and bin edges.
4. A2 records versions, row counts, checksums, download dates, W, bin edges and the unresolved share by day, and is committed and registered.
5. The analysis code is tagged. The test period is loaded once.
6. A reviewer reruns the frozen code on the same checksummed files and compares the numbers.
7. Results are published in the repository within 30 days of completion, whatever they show.
