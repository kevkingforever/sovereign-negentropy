## 1. Summary

The request is for cooperation to run a 30 day, read only measurement of settlement delay and friction in a defined cluster of payment infrastructure. The measurement runs inside the operator's own environment under a pre registered protocol. No money moves, and no existing system changes.

The outputs are a baseline friction report for the operator and, with the operator's consent, aggregate public data. Later phases are conditional and are not part of this request.

The work is led by Kevin Ansong, Independent Researcher. It is open source, and every result will be published whatever it shows.

## 2. Background and status of the evidence

The Sovereign Negentropy working paper (October 2026) proposes a voluntary layer that runs alongside existing payment and administrative systems. The paper defines a friction entropy index, a demurrage currency with a utility offset, and a velocity dependent fee.

What exists today:

* The paper has not been independently reviewed.
* Its mathematics has been checked by 47 offline programmatic checks (28 numerical and 19 symbolic). They test internal consistency only. They do not test whether the economics works.
* Every empirical claim in the paper is a hypothesis. None has been tested.
* A pre registered protocol (version 1.1) fixes the first tests and states what result would end the entropy claim.

Phase 1 does not depend on the paper being right. It produces measurements of settlement delay, retries, failures and queue behaviour that are useful to the operator whatever the index shows.

## 3. Phase 1: passive friction measurement

### 3.1 What is measured

* Lifecycle stage durations for each transaction: initiation, authentication, routing and transit, clearing wait, settlement confirmation.
* Latency quantiles (median, 90th and 99th percentile) per stage and end to end, by 10 minute window.
* Retry counts, webhook retransmissions, error and failure rates.
* Queue utilisation estimates and arrival rates.
* Fees charged per transaction band.
* The entropy of the latency distribution and of stage occupancy, and the friction terms defined in the pre registration.
* Pipeline overhead on the host (processor, memory, input and output), measured throughout.

### 3.2 Data minimisation

| Item | Treatment |
|:-------------------|:-------------------------------------------------|
| Event type and timestamp | Required |
| Transaction identifier | Required, replaced by a salted hash inside the operator environment |
| Channel or rail, status code, retry count, fee amount | Required |
| Amount | Banded (value bands agreed with the operator) or exact, at the operator's choice |
| Phone number, name, account number, KYC data, location | Excluded. Never read by the pipeline |
| Output cells | Aggregates only. Any cell with fewer than 50 transactions is suppressed |

### 3.3 Deployment pattern

![Phase 1 data flow. Raw data stay inside the operator environment. Only aggregate metrics leave.](/tmp/claude-0/-home-claude/0a14d5cf-2d61-58e5-a84c-4c654a32275e/scratchpad/figs/pipeline.png){width=100%}

* The pipeline reads from a replica, an existing event stream or a scheduled log export. It performs no writes to the core ledger and takes no database locks on production tables.
* It runs on hardware designated by the operator. The operator controls its credentials and can revoke them at any time.
* Releases are signed. The operator reviews the source code and the dependency list before deployment and may run its own build.
* A test run on synthetic data precedes any run on operator data.

### 3.4 Outputs and publication terms

* A baseline friction report for the operator, delivered first.
* An analysis under the Phase 1 pre registration, filed before collection starts.
* With the operator's consent, a public release of aggregate metrics.
* The operator may review the report for factual accuracy and confidentiality for 30 days before publication. The operator has no veto over the findings.
* Results are published whatever they show.

### 3.5 Resource limits and stop rules for Phase 1

* The operator sets a cap on the pipeline's resource use at the technical session. The pipeline stops itself if the cap is exceeded.
* The operator or the regulator may stop the pipeline at any time without notice or reason.
* Any suspected security incident halts collection and preserves evidence.

### 3.6 Validation of the measurement path

The repository contains a reference pipeline in the telemetry folder, written in the Python standard library, with three tests that anyone can rerun.

* Correctness: 12 of 12 self checks pass. The streaming histograms equal a batch computation exactly, stage quantiles recover the known lognormal truth within 8 percent, stage times sum to end to end latency for every transaction, windows under 50 transactions are suppressed, and the code imports nothing but the standard library and references no economic quantity.
* Cost per event: 0.58 to 0.67 microseconds per event from 50,000 to 3,200,000 events, so the cost does not grow with history. Memory is bounded by transactions in flight.
* Locking: on PostgreSQL 16 with four writers at 800 transactions per second for 30 seconds, five repetitions each, the read only snapshot reader caused no lock waits and no deadlocks. The few waits recorded were writers meeting each other, at the same level with and without the pipeline. The 99th percentile write latency was 2.75 ms with the pipeline and 2.92 ms without it (medians over five runs). A control reader that deliberately held a table lock raised the 99th percentile to about 155 ms, which shows the test detects locking when it occurs.

Limits: the load is synthetic and ran on one shared two core machine. These tests show the design takes no write locks and has a constant per event cost. They do not predict the behaviour of any operator's production system, so the first task of Phase 1 is to repeat the locking test on the operator's own replica.

### 3.7 Indicative timeline

| Stage | Indicative duration |
|:--------------------------|:----------------------------|
| Approvals, data protection impact assessment, security review | Set by the operator and the regulator |
| Test run on synthetic data | 2 weeks |
| Collection on the agreed cluster | 30 days |
| Analysis and operator report | 15 days |
| Factual review and publication | 30 days |

## 4. Conditional later phases (not requested now)

Nothing in this section begins without separate written approval from the operator and the regulator, a separate registration, and the Phase 1 report.

### 4.1 Phase 2: opt in sandbox cohort

* A small, closed cohort of volunteer merchants.
* Participant balances are backed by funds held in ring fenced accounts at a licensed institution. The pilot team does not hold funds.
* Demurrage, utility and fee parameters are set and approved by the regulator before launch.
* Conversion to legacy currency at published cost is available at all times.
* Entry requires a successful drill of the stop procedure (Section 4.3).

Backing invariant: at every reconciliation, the value held in ring fenced accounts is at least equal to the sum of participant balances plus accrued fees and pending redemptions. The invariant accounts for demurrage and fees. It does not require exact equality.

### 4.2 Phase 3: corridor expansion

Expansion by corridor, one at a time, under the same stop procedure, with capacity planned from measured throughput limits.

### 4.3 Stop conditions

Thresholds marked Phase 1 are set from the Phase 1 baseline and approved by the regulator. No fixed number is chosen before that baseline exists.

| Trigger | Threshold | Response |
|:---------------|:------------------------------|:--------------------------------------|
| Tail latency | 99th percentile of the parallel layer exceeds the Phase 1 baseline by a multiple set by the regulator, for a set number of consecutive windows | Pause new entries, alert, human review |
| Backing shortfall | Backing below participant balances plus accrued fees at any reconciliation | Freeze issuance, alert the regulator, reconcile. Redemptions continue at published cost |
| Queue saturation | Utilisation above a level set from Phase 1 | Throttle new connections |
| Off ramp delay | Conversion time above a level agreed with the licensed institution | Pause new entries and alert. Any liquidity action needs human approval |
| Volume loss | Cohort transaction volume falls below a threshold relative to a matched control | Review. Threshold informed by the levy elasticity estimate |
| Security incident | Any confirmed or suspected compromise | Halt and preserve evidence |

Stop authority sits with named officers of the regulator and the operator. The target time to halt is agreed with them and verified in a drill before Phase 2.

Residual risks that remain after these controls: conversion cost and delay during a rollback, operational error, losses at the licensed institution, participant confusion, and regulatory change. The pilot reports each one.

## 5. Security, privacy and compliance

* Data protection. The operator is the data controller. The pilot team processes data only under a written agreement. A data protection impact assessment precedes deployment. Compliance is with the Data Protection Act 2012 (Act 843), including any registration with the Data Protection Commission, as advised by counsel. No personal data leave the operator environment in Phase 1.
* Payment regulation. Any phase that holds or moves value follows the Payment Systems and Services Act 2019 (Act 987) and the Bank of Ghana sandbox rules, with funds held by a licensed institution.
* Anti money laundering and identity. Participants are identified through existing KYC at the operator and through the national identity card. The pilot team holds no KYC data and builds no identity layer.
* Threat model.

| Threat | Control |
|:------------------------------|:------------------------------------------------------|
| Tampering with pipeline code | Signed releases, operator code review, reproducible builds |
| Data exfiltration | No raw data egress, aggregate output only, small cell suppression |
| Insider misuse | Operator controlled credentials, access logging, least privilege |
| Supply chain compromise | Pinned dependencies, published dependency list, operator build option |
| Availability impact on production | Read only access, replica or log based source, resource cap, self stop |
| Model risk | Pre registration, independent evaluation, publication of failures |

## 6. Evaluation and integrity

* The first tests are fixed in the pre registration (version 1.1). They state what counts as support, failure and an inconclusive result.
* An evaluator independent of the author reviews the Phase 1 results. The evaluator is to be designated through a University of Ghana or external peer review track.
* Code, definitions and aggregate results are published in the open repository. Deviations from the registration are logged and labelled.
* If the entropy predictor is not supported, the paper is revised to say so within 30 days of the analysis.

## 7. Team and governance

| Role | Name | Status |
|:-------------------------|:-------------------------|:-----------------------|
| Principal investigator | Kevin Ansong | Confirmed |
| Legal entity | Sovereign Negentropy Initiative (Project Specific SPV / Pending Registration) | Pending registration |
| Technical lead | To Be Designated (TBD) upon sandbox phase authorization | To be designated |
| Quantitative lead | To Be Designated (TBD) upon sandbox phase authorization | To be designated |
| Regulatory and legal counsel | To Be Designated (TBD) upon sandbox phase authorization | To be designated |
| Independent academic evaluator | To Be Designated (University of Ghana / External Peer Review Track) | To be designated |
| Protocol team contact | Kevin Ansong, kevinansong101@gmail.com | Confirmed |

* Any change to the protocol after approval needs written agreement from the operator and the regulator.
* Declaration of interests and funding: the work has no external funding as at 2 November 2026. The author is the founder of LastStop, a web based vendor directory, and holds no interest in any payment operator named in this document.
* Licences: code is released under the MIT licence and the paper under CC BY 4.0.
* Tools and assistance. This work was developed by Kevin Ansong with AI assistance (Claude, by Anthropic) for drafting, code and test construction. Kevin Ansong directs the project and is responsible for every claim. All code, tests and results are open and can be rerun by anyone.

## Appendix A. Status of claims

| Claim | Status | Basis |
|:--------------------------|:------------------|:----------------------------------------------|
| The paper's mathematics is internally consistent | Checked | 47 offline checks (28 numerical, 19 symbolic). They do not test the economics |
| The friction entropy index predicts tail latency | Hypothesis | Pre registered test S1. No result yet |
| Demurrage with a utility offset retains balances | Hypothesis | Retention condition proved under stated assumptions (Proposition 4). Empirical retention untested |
| A velocity dependent fee raises velocity without lowering volume | Hypothesis | Untested. The levy elasticity estimate (S2) covers a flat fee only |
| A 0.05 percent fee funds 20 percent of GDP | Arithmetic | Requires taxed turnover of 400 times GDP (Proposition 9). Not a proposal to replace tax revenue |
| The Phase 1 pipeline adds no writes to the core ledger | Design requirement | Verified by operator code review and measured overhead during Phase 1 |
| Phase 1 carries no monetary risk | Design property | No value is issued, held or moved in Phase 1 |
| Zero knowledge verification takes about 1 millisecond | External figure | Order of magnitude from a third party benchmark. Not reproduced. Not used in Phase 1 |
| The parallel layer is compatible with Ghanaian law | To be confirmed | Counsel and the regulator decide |
| Later phases are safe to run | Not established | Conditional on Phase 1, separate registration and separate approval |
