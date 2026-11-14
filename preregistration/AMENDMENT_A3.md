---
title: "Amendment A3 to the Pre Registration of Empirical Tests, Version 1.1"
subtitle: "Constants from the training period: window length, bin edges, and the unresolved share report"
author: "Kevin Ansong. Status: to be registered"
date: "14 November 2026"
---

# 1. Status and purpose

A3 fixes the two constants that S1 takes from the training period of D2, and reports the unresolved share required by Amendment A1.1. It changes no rule, threshold, model or outcome. It follows A1 (SHA256 ceac2e992772b3b18611d6ceab9004db886fcb7d13f50d3dd816a1112a1752b2), A1.1 (SHA256 120aa87963569650ce79551abb1afc1a4cd550b36c67e6d6da88f1c1b05c4a42) and A2 (SHA256 605009011f49cabdb85a4c07c954377c6c8a2aef412d194b5f88476248e40380). It is made before the validation and test periods are opened, as the registration requires.

# 2. What was read

The script `s1/freeze_a3.py` first checked all 28 D2 files against the A2 manifest (SHA256 12ca0cb8ee24cdd164a05bc247048682a8467151a36d9b889c42b22cdbf01148). All 28 matched. It then read the arrival time and the inclusion time of every row.

* The window length and the bin edges use only rows that arrive before the end of the training period, with completions at or before that end. The tests show that changing every validation and test outcome leaves both constants unchanged (`s1/tests/test_a3.py`).
* For all 28 days, only the share of rows with no inclusion time was computed, by arrival day and by arrival hour of day in UTC (A1.1).
* No latency from the validation or test period was computed. No forecast was run.

The script was run in Google Colab on 14 November 2026 at 08:56 UTC. SHA256 of the code files used: adapters.py a3e265ed3ffef8296acf9e88867982d96c0782ebcefe459f29087ff310167575, freeze_a3.py cb5ac4868be5468010f5de096a9838e6b7fe1e2e6437253a415bb069a3476375, windows.py bad5176a8495a221a8f71265d04d3689b512a858326e26f21be20a6dd7bea5fa, config.py 8c2a85d968d027fafe8b3ee229d96a4589ce7251314915872ff1d2f9aab72d08.

# 3. The split

The first arrival is 2026-10-16 00:00:00 UTC (1792108800.268) and the last is 2026-11-12 23:59:59 UTC (1794527999.969). With the registered 60, 20, 20 split of that span:

* training ends 2026-11-01 19:12:00 UTC (1793560320.0886)
* validation ends 2026-11-07 09:36:00 UTC (1794044160.0288)
* the test period starts there. After the 24 hour purge it leaves about 4.6 days of scored windows.

D2 has 25,155,158 rows. 14,375,926 arrive before the end of training.

# 4. Window length W

The registered rule takes the smallest candidate whose median training window holds at least 1,000 resolved transactions. Median resolved transactions per window in the training period:

| Candidate W (seconds) | 60 | 300 | 600 | 1800 | 3600 |
|:---|:---|:---|:---|:---|:---|
| Median resolved | 555.0 | 2833.0 | 555.00 | 17220.0 | 34463.0 |

**W is 300 seconds.** It is fixed for the validation and test periods.

# 5. Bin edges

20 log spaced bins between the 0.1th and 99.9th percentiles of training latencies (21 edges, in seconds, full precision):

\begingroup\small
\begin{verbatim}
 0  0.0009999275207519533
 1  0.0021462064688621708
 2  0.004606536085257384
 3  0.009887294168872995
 4  0.021221712838567247
 5  0.04554947876643832
 6  0.09776567196421869
 7  0.20984052668584705
 8  0.4503937400022103
 9  0.966708024598474
10  2.0749054034776275
11  4.45349818542041
12  9.558819430659764
13  20.51668713082307
14  44.036238353236335
15  94.51771019063406
16  202.86922484204695
17  435.4308023861883
18  934.5921433588649
19  2005.9730952461007
20  4305.544496008163
\end{verbatim}
\endgroup

These edges are fixed. The lowest edge equals the 1 millisecond latency floor of A1 section 3.3, because more than 0.1 percent of rows are clipped to it (next section).

# 6. Two facts about the data that the registration did not know

1. **Unincluded transactions are coded as zero.** The inclusion field was never empty in any of the 28 files. In 385,239 rows (1.53 percent) it is zero. These are the unresolved rows, as A1 section 3.4 intends: a transaction without an inclusion time is unresolved. The adapter treats an empty, zero or negative inclusion time as unresolved.
2. **Many rows are clipped.** Of the 14,375,926 training rows, 1,251,012 (8.7 percent) complete before arrival plus 1 millisecond and are clipped to the 1 millisecond floor under A1 section 3.3. The provider's documentation says block times are set at the start of the slot. The share of rows in the lowest bin is therefore large, and the entropy partly reflects the clipped share. The sensitivity run that drops these rows, registered in A1 section 3.3, stays in the plan and is reported with the result.

# 7. Eligibility under A1

The bootstrap block is 288 windows (24 hours at 300 seconds). The scored test period holds about 1,324 windows, which is 4.6 blocks. The requirement is at least 3. D2 is expected to be eligible. This is a calendar calculation, with no outcome used, and the run confirms it.

# 8. Unresolved share (A1.1)

Overall, 1.53 percent of rows are unresolved. A1.1 asks for the share by day and by hour of day, to look for a rise just before midnight UTC. The full tables are in the appendix. The result:

* **By hour.** There is no spike that ends at midnight. The share is lowest at 16:00 (1.07 percent), rises from 20:00 (1.97 percent), and peaks at 01:00 (2.30 percent). It is 1.76 percent at 23:00 and 1.80 percent at 00:00. Over 20:00 to 05:59 it is 1.84 percent, and over 06:00 to 19:59 it is 1.33 percent. This is a broad overnight rise, not the sharp signature of late inclusion after a daily merge.
* **By day.** The share falls over the period: 2.15 percent in the first 7 days (16 to 22 October) and 0.72 percent in the last 7 days (6 to 12 November). By period: 2.03 percent from 16 October to 1 November, 0.98 percent from 2 to 6 November, and 0.73 percent from 7 to 12 November.
* **Reading.** A decline over days is not what late inclusion without later updates would produce, because that effect does not depend on the age of the file. The cause is not determined. It may be a change at the provider or a change in network conditions. This is reported as a limit: the training days have a higher unresolved share than the test days, so the 0.99 quantile of resolved latency may be trimmed differently in the two. Both models face the same shift. A3 changes nothing because of it. The S1 report states this limit next to the result.

# 9. What follows

1. The code freeze tag for the S1 code.
2. One run of S1 on D2. The run reads W and the bin edges from the output file named below, recomputes them, and stops if they differ.
3. Reproduction by a reviewer, and publication of the result within 30 days.

Output files, in the repository at `preregistration/a3/`: a3_constants.json SHA256 9d036dec92621e3060ae234b202f374e12faeb0619e44c196115df615bb7ea5b, a3_constants_unresolved_by_day.csv SHA256 b48d683f4de40e421ede09fdbe761aa1e3329154def6066c2567a2fc4f2db1c4, a3_constants_unresolved_by_hour.csv SHA256 0e7e71d2007357d596391db4adea03c557935c2fd2fbaa2088faa7e283bd6a90.

# Appendix: unresolved share

By arrival day (UTC): day, rows, unresolved, share.

\begingroup\scriptsize
\begin{verbatim}
2026-10-16    871297   19694  0.0226
2026-10-17    788533   15961  0.0202
2026-10-18    784836   25735  0.0328
2026-10-19    818202   16958  0.0207
2026-10-20    857618   14622  0.0170
2026-10-21    908505   18018  0.0198
2026-10-22    894427   16519  0.0185
2026-10-23    966592   18647  0.0193
2026-10-24    846304   21153  0.0250
2026-10-25    716050   21332  0.0298
2026-10-26    865480   18049  0.0209
2026-10-27    939852   17323  0.0184
2026-10-28   1003111   13707  0.0137
2026-10-29    800648   21630  0.0270
2026-10-30    888598   12016  0.0135
2026-10-31    770029   12257  0.0159
2026-11-01    808955   11980  0.0148
2026-11-02    904008   10894  0.0121
2026-11-03    876135   11036  0.0126
2026-11-04    967704    9671  0.0100
2026-11-05   1039172    8792  0.0085
2026-11-06   1031286    6633  0.0064
2026-11-07    940416    6005  0.0064
2026-11-08    913050    9963  0.0109
2026-11-09    974240    7841  0.0080
2026-11-10   1046382    6836  0.0065
2026-11-11    968939    5811  0.0060
2026-11-12    964789    6156  0.0064
\end{verbatim}
\endgroup

By arrival hour of day (UTC): hour, rows, unresolved, share.

\begingroup\scriptsize
\begin{verbatim}
00:00   1067459   19220  0.0180
01:00    956582   22018  0.0230
02:00    917228   17007  0.0185
03:00    939715   18210  0.0194
04:00    926199   14515  0.0157
05:00    840588   15291  0.0182
06:00    921159   15220  0.0165
07:00    942627   15408  0.0163
08:00   1056237   14947  0.0142
09:00   1175799   14169  0.0121
10:00   1082794   14988  0.0138
11:00   1083271   15081  0.0139
12:00   1103334   14237  0.0129
13:00   1136008   16324  0.0144
14:00   1168018   16511  0.0141
15:00   1162440   15484  0.0133
16:00   1140638   12220  0.0107
17:00   1126297   12477  0.0111
18:00   1161601   14343  0.0123
19:00   1068692   12844  0.0120
20:00   1113996   21963  0.0197
21:00   1012943   18750  0.0185
22:00   1044153   16267  0.0156
23:00   1007380   17745  0.0176
\end{verbatim}
\endgroup
