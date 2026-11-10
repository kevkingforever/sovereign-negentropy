# Reviewers

This file lists people who have agreed to be named as reviewers, with the date and scope of their review. A listing records that a review took place. It does not record agreement with the paper.

## Review 1: telemetry code, 4 November 2026

* Reviewer: Kofi Taylor.
* Commit reviewed: bd2f5e926d17c8fb5e9769216fcfc46e1e3355f2
* Scope: ran `telemetry/check_pipeline.py` (12 of 12 passed at that commit), read the pipeline, generator, benchmark code, pre registration v1.1, README, annex and verification map, and ran eight small reproductions against the unchanged pipeline. Not in scope: the 47 mathematical checks, a rerun of the PostgreSQL benchmark, the economics, and any public data. No study data were downloaded or analysed.
* Result: eight weaknesses reproduced. Resolution on 5 November 2026 (pipeline version 0.2, 20 checks):

| Finding | Resolution |
|:---|:---|
| Stage cell suppression incomplete | Fixed. Each stage figure is suppressed below 50 contributing transactions. Suppressed windows no longer expose their completion count. Check C13. |
| Duplicate starts overwrite history, replays double count | Fixed. Duplicate starts and replays within a bounded recent window are rejected and counted. Durable deduplication is left to the ingestion adapter. Checks C14, C15. |
| No expiry of unfinished transactions or old windows | Fixed. Open transactions expire after 24 hours of event time and are counted as unresolved. Windows are evicted beyond a retention limit. Checks C16, C20. |
| H_S differs from the registered occupancy statistic | Relabelled. The reference code reports H_exit, the entropy of durations booked at stage exit. The registered in flight occupancy statistic is not implemented. |
| Histogram saturation hides tails | Fixed. Overflow and underflow are counted and edge quantiles are flagged as bounds. Check C17. |
| Input validation incomplete | Fixed. Configuration and event fields are validated before any state change, with reason specific counts. Check C18. |
| Failure and retry semantics unclear | Documented in the pipeline docstring. Retries are per event, failures are failed events, and rates are not reported. A terminal failure state is not modelled. |
| pooled() writes a fake window | Fixed. Check C19. |
| Check descriptions broader than what they test | Relabelled. C6, C7, C8, C10, C11 and C12 now state what they establish. C7 now compares against injected totals. |
| "No locks" too broad | Narrowed to "no write locks". Read queries take ordinary read locks. |
| Benchmark watermark can skip a late committing row | Recorded as a known limit of the benchmark adapter. Not reproduced as a database experiment. |
| Default window 10 s, annex says 10 minutes | Recorded. The deployment window is set at configuration. |
| Annex diagram link to a local path | Fixed in annex version 1.3. |

* S1 readiness: the review found that the registered test is not yet runnable from this repository and listed eight items to settle in a dated amendment before any held out data are loaded. They are being resolved in that amendment. The reviewer also records that a web search surfaced example rows from one public dataset's preview page. No analysis was done on them. This is recorded here for the confirmatory analysis.

## Review 2: telemetry code follow up, 9 November 2026

* Reviewer: Kofi Taylor.
* Commit reviewed: 68769ef4975bd3efa58e1b7ab93f65b7adaaf0b6 (pipeline version 0.2), compared with the previously reviewed commit bd2f5e926d17c8fb5e9769216fcfc46e1e3355f2.
* Scope: ran `telemetry/check_pipeline.py` (20 of 20 passed), compiled the source, compared it with the previous commit and ran ten focused checks. Not in scope: the PostgreSQL benchmark, the 47 mathematical checks, and any public data. No dataset was downloaded or analysed.
* Files hashed by the reviewer (SHA256): `telemetry/pipeline.py` dbcc176540765a1cdc5a14879aeb0a3b9bfbd4794a22bce5cc95460e187dd447, `telemetry/check_pipeline.py` 95a6cbb355589901cd9df00bcdaafea5964a70f6ec12b371f6953085e156994f, `preregistration/PREREGISTRATION_v1_1.md` 013a7bb0e82897af24640296f3a131fa83f2f0e5a73437faddc6795d842b036f. The registered PDF `preregistration/PREREGISTRATION_v1_1.pdf` has SHA256 8a065dee4f3b365f0d592336074a9203e1bafab9f1dddcac1d3a25f0278fa1e0.
* Result: of the eight earlier weaknesses, five fixed, one mostly fixed (expiration) and two documented as outside the implementation. Two new issues were reproduced. Resolution on 9 November 2026 (pipeline version 0.3, 22 checks):

| Finding | Resolution |
|:---|:---|
| Expiration does not run at the end of a stream | Fixed. New methods `advance_watermark(ts)` and `flush()` expire stale transactions at the end of a batch or stream. Check C22. |
| A rejected event can move the expiration clock | Fixed. Only accepted events advance event time. Check C21. |
| Registered in flight stage occupancy entropy (H_S) not implemented | Stays outside this version. The code reports H_exit and says so. |
| Terminal failures not modelled | Stays outside this version. Operators need a separate terminal failure rule. |
| Durable replay protection | Stays outside this version. A production adapter needs durable checkpoints and deduplication across restarts. |
| Benchmark ingestion can skip a late committing row | Recorded as a known limit. The database benchmark was not rerun by the reviewer. |
| S1 not runnable from the repository | Correct. The data freeze amendment, analysis code and code freeze tag are still to be written and registered before any held out data are loaded. |
| Duplicate sentence in this file | Removed. |

To be listed, a reviewer sends a short note, or opens an issue, stating the scope of the review (for example: the mathematics of Chapters 2 to 5, the pre registration, or the verification programs) and the date.
