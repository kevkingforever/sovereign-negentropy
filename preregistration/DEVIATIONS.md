# Deviations from the registered plan

Every departure from PREREGISTRATION_v1_1 is recorded here with its date and reason. A deviation made after any data access is labelled "after data access".

No departure after data access is recorded. Two amendments, made before any data access, are recorded below.

## A1, 12 November 2026

* Date: 12 November 2026 (approved 10 November, registered 12 November).
* Section of the registration: sections 5 and 11 (data, bootstrap and amendments), and the open items they left.
* What was planned: a 24 hour block bootstrap, a 14 day Ethereum period, and several design choices left open.
* What was done: a dataset needs at least 3 bootstrap blocks to be eligible and an ineligible dataset cannot support. The Ethereum period is 28 days. The learner, the queueing baselines, the handling of completion before arrival, the D2 completion source and the reporting rules are fixed.
* Reason: with the planned periods the bootstrap interval has almost no width, so a pass is too easy.
* Made before or after data access: before. No dataset had been downloaded or analysed.
* Effect on interpretation: Bitcoin's 7 day sample is expected to be ineligible, so the decision rests mainly on Ethereum.

## A1.1, 12 November 2026

* Date: 12 November 2026.
* Section of A1: 3.1 and 3.4.
* What was planned: eligibility "spans at least 3 bootstrap blocks", and a sentence saying the 3 day gap limits the effect of late inclusion.
* What was done: eligibility is counted in scored test windows. The late inclusion sentence is withdrawn, the limit is stated, and A2 reports the unresolved share by day and by hour of day in UTC.
* Reason: reviewer comments on both sections. The provider's documentation does not say whether inclusion fields are updated after the daily merge.
* Made before or after data access: before. Only the column names of one Ethereum file had been read.
* Effect on interpretation: the S1 result applies to transactions that were resolved when the provider produced each daily file.

Entry format:

* Date:
* Section of the registration:
* What was planned:
* What was done:
* Reason:
* Made before or after data access:
* Effect on interpretation:
