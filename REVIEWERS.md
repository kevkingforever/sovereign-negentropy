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

To be listed, a reviewer sends a short note, or opens an issue, stating the scope of the review (for example: the mathematics of Chapters 2 to 5, the pre registration, or the verification programs) and the date.

To be listed, a reviewer sends a short note, or opens an issue, stating the scope of the review (for example: the mathematics of Chapters 2 to 5, the pre registration, or the verification programs) and the date.
