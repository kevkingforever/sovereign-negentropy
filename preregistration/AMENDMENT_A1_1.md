---
title: "Amendment A1.1 to the Pre Registration of Empirical Tests, Version 1.1"
subtitle: "Two clarifications to A1, made before any validation or test data are loaded"
author: "Kevin Ansong. Status: to be registered"
date: "12 November 2026"
---

# 1. Status and purpose

A1 was registered on 12 November 2026 as the GitHub release `preregistration_a1`, PDF SHA256 ceac2e992772b3b18611d6ceab9004db886fcb7d13f50d3dd816a1112a1752b2. Later the same day a reviewer sent comments on sections 3.1 and 3.4. Both comments are accepted. A1.1 changes only the two items below. Everything else in the registration and in A1 stands.

As of this amendment no dataset has been downloaded or analysed. The only D2 file content read is the one line of column names, read on 12 November 2026.

# 2. Changes

## 2.1 Section 3.1: eligibility is counted in windows

A1 says a dataset is eligible if its scored test period spans at least 3 bootstrap blocks. Elapsed time and window count can differ when windows are skipped under section 3.8.

Decision: a dataset is eligible only if the number of scored test windows is at least 3 times the block length in windows. The block length in windows is ceil(86400 divided by the window length in seconds), with the registered minimum. The published code already applies this rule (`s1/run.py`, `eligible`), so no code change is needed.

## 2.2 Section 3.4: late inclusion

A1 says the 3 day gap before the freeze date limits the effect of transactions included after the provider's daily merge. The provider's public documentation does not say whether inclusion fields are updated after that merge. It says that the merger checks inclusion status when it produces the daily files, and that a transaction already included when first received is dropped from the files. The sentence in A1 therefore rested on an assumption that the documentation does not support, and it is withdrawn.

Decision:

* If a transaction is included after the merge for its day and the fields are never updated, it stays unresolved. Such transactions are the slow ones, so the resolved only target can understate the true 0.99 quantile of delay.
* The comparison of G1 and G2 is not affected in kind, because both models are scored against the same target. The meaning of the result is limited to the delay of transactions that were resolved at merge time. Every report of the S1 result states this.
* A2 reports the unresolved share by day and by hour of day in UTC, for the whole D2 period. A rise in the unresolved share just before midnight UTC is reported as evidence of this effect, with no change to the test.
* The 3 day gap in section 3.2 stays, for a different reason: it keeps the final days of the period away from the provider's most recent files.

# 3. Effect on interpretation

Neither change moves a threshold, a loss, a model or the outcome rule. Section 2.1 removes a reading of "spans" that was open to two interpretations. Section 2.2 replaces an unsupported claim with a reported check and a stated limit.
