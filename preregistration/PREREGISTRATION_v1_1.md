# Pre Registration of Empirical Tests, Version 1.1

Project: Sovereign Negentropy, a working paper (October 2026)

Author: Kevin Ansong, Independent Researcher

Version: 1.1. It supersedes version 1.0, which is kept unchanged in the archive folder of this repository.

Date of this version: 2 November 2026

Data access statement: no data file or series named in Sections 5, 8, 9 or 10 has been downloaded, opened or analysed for this registration or for version 1.0. The author has read the providers’ public descriptions of the datasets and is aware of the general public reporting on the 2020 growth shock, the 2022 inflation shock and the repeal of the Electronic Transfer Levy. The author makes this statement as at 2 November 2026.

## 1. Purpose and scope

This document fixes, before any analysis, the hypotheses, definitions, datasets, models, evaluation metrics and decision rules for three empirical tests of the friction entropy index in the Sovereign Negentropy paper. It states in advance what result counts as support, what counts as failure, and what counts as inconclusive.

Covered here:

* S1: whether the entropy of the latency distribution adds out of sample predictive information about tail latency in public transaction queues.
* S2: an estimate of how mobile money volume and value in Ghana responded to the Electronic Transfer Levy.
* S3: whether friction indicators built from public indices add out of sample predictive information about exposure to the 2020 and 2022 shocks.

Not covered here: Hypotheses 1 to 5 of the paper (retention, velocity fee effect, gate quality, attestation economics, friction reduction) and the revenue adequacy ratio. Those are tested only in the gated pilot of Chapter 10, under a separate registration filed before the corresponding data are collected.

A failure of S1, S2 or S3 does not reject the demurrage or fee mechanics of Chapters 3 and 5. It bears on whether the entropy index is useful as a predictor.

## 2. Changes from version 1.0

Each change below answers a specific weakness found in an audit of version 1.0 on 31 October 2026.

1. Timestamping. Version 1.0 described a git commit as immutable. Git history can be rewritten and commit dates are set by the committer. Version 1.1 requires registration on OSF Registries and a tagged archive on Zenodo (Section 11).
2. Datasets. Version 1.0 named five lifecycle states and public datasets that cannot supply them. The Sarafu data record confirmed transactions and cannot support a latency test, so Sarafu moves to an exploratory holding time analysis. Public data now use a latency bin variant of the entropy (Section 4.3). The five stage variant is reserved for telecom logs in Phase 1 (Section 4.4).
3. Idle state. Version 1.0 included Idle in the state set. Idle time dominates any such distribution and makes the entropy track velocity. Version 1.1 restricts the state set to in flight stages and leaves idle balances to the velocity term.
4. Tail alignment. Entropy of stage shares is an average property. Version 1.1 builds the entropy from the latency distribution itself, which carries tail information.
5. Formula. Version 1.0 placed velocity outside the integral. Version 1.1 follows Definition 2 of the paper, with velocity inside the integral, and fixes the scale parameters (Section 4.5).
6. Pass metric. Version 1.0 required a reduction in "tail latency distribution anomalies" under simulated surges. Version 1.1 uses pinball loss at the 0.99 quantile on real data with a time ordered test period and a stated test (Section 7).
7. Outcome partition. Version 1.0 left outcomes undefined between its pass and fail rules. Version 1.1 defines three outcomes that cover every case: supported, not supported, inconclusive.
8. Baselines. Version 1.0 compared against queueing formulas only. Version 1.1 adds persistence, a moving average, and a gradient boosted model with queueing features, and tests the entropy as an addition to that strong model.
9. Macro criterion. Version 1.0 required controls to absorb the friction indices completely, which cannot happen. Version 1.1 registers the panel, outcomes, controls and a threshold on incremental cross validated fit (Section 9).
10. Scope. Version 1.0 said the core thermodynamic hypothesis would be dropped. Version 1.1 states what each test can and cannot reject (Section 1 and Section 12). The E Levy analysis now has a specification and a decision rule (Section 8).

The pass threshold changed from a 15 percent reduction against a weak baseline to a 5 percent reduction against a strong baseline. The 15 percent figure was set against queueing models that assume Poisson arrivals and exponential service. A gain of that size over a gradient boosted model that already contains queueing features is a much stricter requirement. The author chose 5 percent as the smallest improvement judged operationally relevant. It is fixed before any data are loaded.

## 3. Hypotheses

S1 (primary). In a rolling window, the entropy of the latency distribution adds out of sample predictive information about the 99th percentile latency of the next window, beyond a gradient boosted model that already contains lagged latency features and queueing based features.

S2 (estimation with a design rule). The levy changed mobile money transaction value and volume in a way that can be estimated from published monthly statistics, with the results used to set the volume loss gate of any later pilot.

S3 (secondary). Friction indicators built from public indices, measured before each shock, add out of sample predictive information about the size of the 2020 growth shock and the 2022 inflation shock, beyond governance and structural controls.

## 4. Definitions

### 4.1 Observations

A transaction j has an arrival time a_j (the first time the system records it) and a completion time c_j (the time it is confirmed or settled). Its latency is the completion time less the arrival time. Where available, it has a value weight w_j.

Transactions without a recorded completion within a maximum horizon of 24 hours are unresolved. Latency quantiles are computed on resolved transactions. The share of unresolved transactions is reported for every window. As a sensitivity check, unresolved transactions are assigned a latency of 24 hours and the primary comparison is repeated.

### 4.2 Windows and information rule

The window length W is fixed per dataset as the smallest value from 1, 5, 10, 30 and 60 minutes for which the median training window contains at least 1,000 resolved transactions. Windows are consecutive and non overlapping.

The forecast origin is the end of window t. Every feature used for the forecast of window t plus one may use only information with a timestamp at or before that origin. This includes completions observed so far, arrivals, fees and queue sizes. No feature may use a completion timestamp after the origin.

### 4.3 Entropy of the latency distribution, public data variant (H_L)

K = 20 bins with edges spaced logarithmically between the 0.1th and 99.9th percentiles of resolved latencies in the training period. Values outside the range fall in the end bins. Edges are computed once from the training period and then frozen.

In window t, p_i is the share of transactions completed in the window whose latency falls in bin i. The entropy is H_L = the sum over i of p_i times ln(1 over p_i), with 0 ln(1 over 0) taken as 0. A value weighted version, using w_j where it exists, is computed as a sensitivity check. The features entering the models are H_L at lags 0 to 5, its mean over the last 6 windows, and its first difference.

### 4.4 Stage occupancy entropy, telecom variant (H_S)

This variant is defined here and tested only under the Phase 1 registration. The states are the in flight stages of the transaction lifecycle: authentication, routing and transit, clearing wait, and settlement confirmation. The weight p_i is the share of value weighted in flight time spent in stage i across transactions in the window. Idle balances are not a state. Their effect enters through the velocity term.

### 4.5 The full index

The index follows Definition 2 of the paper: S_E equals kappa times H plus the integral over time of sigma_E, where sigma_E equals the sum of the three friction terms divided by tau_0 times v(tau). Velocity sits inside the integral.

On public data the confirmatory predictor is H_L alone. The datasets contain no capital or institutional friction fields, and the scale parameter kappa is absorbed by the regression coefficient. For any analysis that uses the full index, kappa is fixed at 1 and tau_0 is fixed at the window length. Neither is fitted.

### 4.6 Friction terms on Phase 1 data

These definitions apply to the Phase 1 registration. Each friction term is a dimensionless ratio to a reference value, and the reference is the median over the first 14 days of the collection.

* f_c: median clearing and settlement delay in the window.
* f_t: retry rate plus error rate in the window.
* f_i: share of transactions held for manual or compliance review, weighted by hold time. If the operator cannot supply these fields, f_i is omitted and the omission is reported.
* v: value transacted in the window divided by mean outstanding balances.

## 5. Datasets for S1

The confirmatory evaluation uses two public datasets. Version 1.0 named three, but no third public dataset with arrival and completion timestamps has been identified.

D1: the DataForge Bitcoin mempool lifecycle dataset, published on Hugging Face under the ODC BY licence. Arrival is first_seen_ts and completion is block_observed_ts. Transactions flagged as pre existing when a collection window opened are excluded, because their first seen time does not show when they entered the network. The provider states that timestamps include polling and network delays and that fee coverage changed during the first collection days. Both limitations are recorded in any report.

D2: the Flashbots Mempool Dumpster archive of Ethereum mempool transactions, published under CC0. Arrival is the first seen timestamp. Completion is the timestamp of the block that included the transaction, joined by transaction hash from canonical chain data. The chain data source is named in the data freeze amendment. The period is the most recent contiguous 14 days that are complete at the freeze date, chosen with no reference to outcomes.

Time ordered split for each dataset: the first 60 percent of the time span is training, the next 20 percent is validation, and the final 20 percent is test. The test period is not loaded until the analysis code is frozen.

Data freeze amendment. Before any validation or test data are loaded, the author records in a dated amendment: exact file versions, row counts, SHA256 checksums, download dates, the chosen W and bin edges (computed from the training period only), and the chain data source for D2. The amendment is committed and registered. Fields named above are checked against each provider's documentation at that time. If a required field is absent, the dataset is dropped and the drop is recorded.

## 6. Models for S1

The forecast target is the 0.99 quantile of latency among transactions that arrive in window t plus one, evaluated after all of them have resolved or reached the 24 hour horizon.

Baselines:

* P0, persistence: the 0.99 quantile of the most recent completed window.
* P1, moving average: an exponentially weighted average of past window 0.99 quantiles with smoothing weight 0.3.
* Q1, M/M/1: arrival and service rates estimated from the last 6 windows. The forecast is ln(100) divided by the service rate less the arrival rate, and 24 hours if the arrival rate is not below the service rate.
* Q2, M/G/1: the Pollaczek Khinchine mean sojourn time from the estimated first two service time moments, multiplied by ln(100) as an exponential tail approximation.
* A Jackson network reduces to M/M/1 for a single queue. It is registered for the multi stage Phase 1 data and is not applicable to D1 and D2.

Learned models, both gradient boosted quantile regressions with the pinball loss at 0.99, using the same learner, the same tuning grid, the same budget and the same seeds:

* G1 (queueing model): lagged arrival rate, resolved counts, lagged latency quantiles (0.5, 0.9, 0.99), fee rate quantiles, pending queue size, and the Q1 and Q2 forecasts as features.
* G2 (queueing model plus entropy): all G1 features plus the H_L features of Section 4.3.

Hyperparameters are chosen on the validation period. The random seed is 20261031.

## 7. Evaluation and decision rules for S1

Loss: mean pinball loss at 0.99 over test windows. The relative improvement R is one less the ratio of the G2 loss to the G1 loss.

Test: a one sided Diebold Mariano test of equal loss with a Newey West variance (bandwidth floor of 4 times (T divided by 100) to the power 2 over 9, where T is the number of test windows). The 95 percent interval for R comes from a circular block bootstrap with block length equal to the number of windows spanned by 24 hours (minimum 10) and 10,000 resamples. The Holm correction is applied across D1 and D2.

Support on a dataset requires all three of the following:

* the Holm adjusted one sided p value is below 0.05,
* the point estimate of R is at least 0.05,
* the lower bound of the 95 percent interval for R is above 0.

Outcomes:

* Supported: support on both D1 and D2.
* Not supported: support on neither D1 nor D2.
* Inconclusive: support on exactly one dataset.

Consequences:

* Supported: the entropy features are carried into the Phase 1 registration as a candidate predictor. No claim about mechanism follows.
* Not supported: the paper is revised within 30 days to describe S_E as a descriptive index only, or to remove it, and the result is published.
* Inconclusive: the result is published with no claim, and any further test needs a new registration.

Secondary analyses, reported without a decision rule: the same comparison on surge windows (windows whose arrival rate exceeds the 95th percentile of the training period), the Brier score for the event that the realised 0.99 latency exceeds twice the training median of that quantity, the value weighted entropy, and the 24 hour latency treatment of unresolved transactions.

## 8. S2: estimation of the levy response

Data: Bank of Ghana published monthly mobile money transaction value and volume from January 2019 to the latest month available at the freeze date. Controls: the consumer price index from the Ghana Statistical Service and the cedi exchange rate from the Bank of Ghana.

Breakpoints: the effective dates of the introduction of the Electronic Transfer Levy, of each change in its rate, and of its repeal. The dates are taken from the legal instruments and recorded in the data freeze amendment.

Model: segmented regression of log monthly value, and separately log monthly volume, on a linear trend, level and slope change indicators at each breakpoint, month of year effects, log CPI and log exchange rate. Standard errors use Newey West with 6 lags. A placebo version places a fictitious breakpoint 12 months before the introduction and reports whether an effect of similar size appears.

Control series: if the Bank of Ghana publishes transaction categories that the levy exempted, the exempt category serves as a within country control. If it does not, the analysis is reported as a single series with that limitation stated.

Reported quantities: the estimated level change at each breakpoint with 95 percent intervals, and the implied elasticity, defined as the estimated change in log value divided by the change in log of one plus the effective rate. The statutory rate and, where the data permit, the effective rate are both used.

Design rule: every pilot protocol that involves a fee includes a volume loss gate. The elasticity estimate sets its initial threshold.

This analysis estimates the response to a flat fee. It does not test the velocity dependent fee schedule of Chapter 5.

## 9. S3: macro panel (secondary)

Outcomes, one cross section each:

* O1: real GDP growth in 2020 less the mean growth rate of 2015 to 2019.
* O2: CPI inflation in 2022 less the mean inflation rate of 2015 to 2019.

Predictors are measured in vintages before each shock. Candidate indicators are payment and remittance costs for the capital friction proxy, the World Bank Logistics Performance Index for the technological proxy, and World Bank business regulation and enterprise survey time indicators for the institutional proxy. Payment turnover to GDP from the BIS CPMI Red Book serves as the velocity proxy where it exists. The final list is chosen by availability and coverage and never by association with outcomes. It is recorded in the data freeze amendment before outcome data are loaded.

The friction index is the equally weighted sum of standardised proxies. The entropy term cannot be built at national level, so S3 tests the friction component only.

Controls: log GDP per capita, the mean of the six Worldwide Governance Indicators, trade openness, and private credit to GDP.

Estimation: ordinary least squares. The incremental fit is the leave one out cross validated R squared of the controls plus the friction index, less the same quantity for the controls alone. The 95 percent interval comes from a bootstrap over economies.

Support for an outcome requires an incremental cross validated R squared of at least 0.02, a lower interval bound above 0, and the predicted sign (more friction, a larger loss or higher inflation). The Holm correction is applied across O1 and O2.

* Supported: support on at least one outcome.
* Not supported: neither outcome meets the threshold.

The sample is small and has one shock per outcome. A null result here is weak evidence against the index, and the report says so.

## 10. Exploratory analyses

These carry no decision rule and are labelled exploratory in any report.

* E1: the distribution of holding times in the Sarafu Community Inclusion Currency 2020 to 2021 dataset, and its relation to velocity. The data descriptor is checked at the freeze date for the fields available and for whether the window includes a demurrage period.
* E2: the full index, with friction proxies where available, on D1 and D2.

## 11. Integrity procedures

* Code freeze. All analysis code is committed and tagged before validation and test data are loaded. The test period is loaded once.
* Deviations. Any departure from this registration is recorded in DEVIATIONS.md with its date and reason. A deviation made after data access is labelled as such wherever results are reported.
* Reporting. The results of every registered test are published in this repository, with code and all tables, within 30 days of completing the analysis, whatever the outcome.
* Timestamping. This version is registered on OSF Registries and a tagged release is archived on Zenodo. The OSF registration number and the Zenodo DOI are recorded in the repository README on the day they are issued. Git tag: preregistration_v1_1.
* Independent check. An independent reviewer is asked to record the SHA256 hash of this document before any data are loaded. The reviewer is to be designated through the University of Ghana or external peer review track named in the Technical Annex.
* Amendments. Amendments are allowed before the data freeze amendment, each versioned and dated. After the freeze, only deviations are allowed.

## 12. What these tests cannot show

* S1 tests prediction of tail latency in two public blockchain queues. It does not show that the index measures economic friction in a national payment system, whose service discipline, batching and arrival processes differ.
* The datasets are short, and mempool observations come from polling observers with delays.
* S2 is a single economy time series. Controls cannot remove every simultaneous event.
* S3 is a small cross section with one shock per outcome.
* None of these tests addresses Hypotheses 1 to 5. A passing result on S1, S2 or S3 is not evidence that the demurrage, fee or retention mechanics work.
