# Sample baseline report: Ethereum public mempool data, 28 days

This report shows the format an operator would receive. It tests no hypothesis. The data are public. Arrival is the time the observer first saw a transaction. Completion is the inclusion block time. Only two timestamps exist, so this is an end to end figure. Stage durations, retries, webhooks and queues are not in this dataset and are what a pilot would add.

## Headline figures

| Item | Value |
|:---|---:|
| Transactions observed | 25,155,158 |
| Resolved (included) | 24,769,919 |
| Unresolved share | 1.53 percent |
| Median delay | 6.1 s |
| 90th percentile delay | 15.4 s |
| 99th percentile delay | 154.0 s |
| Windows reported (300 s, at least 50 resolved) | 8,052 of 8,055 |
| Rows with completion before arrival plus 1 ms, set to 1 ms | 9.08 percent |

## By hour of day (UTC)

| Hour | Resolved | Median s | 90th s | 99th s | Unresolved share |
|---:|---:|---:|---:|---:|---:|
| 00 | 1,048,239 | 6.5 | 21.8 | 971.6 | 1.80 percent |
| 01 | 934,564 | 6.1 | 18.3 | 344.7 | 2.30 percent |
| 02 | 900,221 | 6.1 | 16.3 | 102.9 | 1.85 percent |
| 03 | 921,505 | 6.1 | 12.2 | 68.8 | 1.94 percent |
| 04 | 911,684 | 6.1 | 13.7 | 61.3 | 1.57 percent |
| 05 | 825,297 | 6.1 | 13.0 | 61.3 | 1.82 percent |
| 06 | 905,939 | 6.1 | 13.7 | 61.3 | 1.65 percent |
| 07 | 927,219 | 6.1 | 13.7 | 68.8 | 1.63 percent |
| 08 | 1,041,290 | 6.1 | 14.5 | 97.2 | 1.42 percent |
| 09 | 1,161,630 | 6.1 | 18.3 | 817.5 | 1.21 percent |
| 10 | 1,067,806 | 6.1 | 15.4 | 154.0 | 1.38 percent |
| 11 | 1,068,190 | 6.1 | 13.0 | 68.8 | 1.39 percent |
| 12 | 1,089,097 | 6.1 | 13.0 | 61.3 | 1.29 percent |
| 13 | 1,119,684 | 6.1 | 14.5 | 72.9 | 1.44 percent |
| 14 | 1,151,507 | 6.1 | 15.4 | 77.2 | 1.41 percent |
| 15 | 1,146,956 | 6.1 | 14.5 | 81.8 | 1.33 percent |
| 16 | 1,128,418 | 6.1 | 13.7 | 109.0 | 1.07 percent |
| 17 | 1,113,820 | 5.8 | 12.2 | 68.8 | 1.11 percent |
| 18 | 1,147,258 | 6.1 | 14.5 | 81.8 | 1.23 percent |
| 19 | 1,055,848 | 6.1 | 12.2 | 68.8 | 1.20 percent |
| 20 | 1,092,033 | 6.1 | 15.4 | 97.2 | 1.97 percent |
| 21 | 994,193 | 6.1 | 14.5 | 91.7 | 1.85 percent |
| 22 | 1,027,886 | 6.1 | 18.3 | 971.6 | 1.56 percent |
| 23 | 989,635 | 6.5 | 19.4 | 728.6 | 1.76 percent |

## By day

| Day | Resolved | Median s | 90th s | 99th s | Unresolved share |
|---:|---:|---:|---:|---:|---:|
| 1 | 851,603 | 6.1 | 14.5 | 81.8 | 2.26 percent |
| 2 | 772,572 | 6.1 | 12.2 | 122.3 | 2.02 percent |
| 3 | 759,101 | 6.1 | 19.4 | 307.3 | 3.28 percent |
| 4 | 801,244 | 6.1 | 14.5 | 109.0 | 2.07 percent |
| 5 | 842,996 | 6.1 | 16.3 | 613.1 | 1.70 percent |
| 6 | 890,487 | 6.1 | 13.0 | 91.7 | 1.98 percent |
| 7 | 877,908 | 6.1 | 13.0 | 81.8 | 1.85 percent |
| 8 | 947,945 | 6.5 | 14.5 | 115.5 | 1.93 percent |
| 9 | 825,151 | 6.1 | 13.7 | 81.8 | 2.50 percent |
| 10 | 694,718 | 6.5 | 17.3 | 91.7 | 2.98 percent |
| 11 | 847,431 | 6.1 | 16.3 | 72.9 | 2.09 percent |
| 12 | 922,529 | 6.5 | 29.0 | 971.6 | 1.84 percent |
| 13 | 989,404 | 7.3 | 54.6 | 971.6 | 1.37 percent |
| 14 | 779,018 | 6.5 | 18.3 | 109.0 | 2.70 percent |
| 15 | 876,582 | 6.5 | 18.3 | 81.8 | 1.35 percent |
| 16 | 757,772 | 6.1 | 15.4 | 64.9 | 1.59 percent |
| 17 | 796,975 | 6.1 | 16.3 | 72.9 | 1.48 percent |
| 18 | 893,114 | 6.1 | 15.4 | 64.9 | 1.21 percent |
| 19 | 865,099 | 5.8 | 12.2 | 57.9 | 1.26 percent |
| 20 | 958,033 | 5.8 | 13.7 | 64.9 | 1.00 percent |
| 21 | 1,030,380 | 5.8 | 13.7 | 68.8 | 0.85 percent |
| 22 | 1,024,653 | 5.8 | 13.0 | 77.2 | 0.64 percent |
| 23 | 934,411 | 5.5 | 10.9 | 46.0 | 0.64 percent |
| 24 | 903,087 | 5.8 | 13.0 | 68.8 | 1.09 percent |
| 25 | 966,399 | 6.1 | 14.5 | 57.9 | 0.80 percent |
| 26 | 1,039,546 | 5.8 | 12.2 | 61.3 | 0.65 percent |
| 27 | 963,128 | 5.8 | 10.9 | 46.0 | 0.60 percent |
| 28 | 958,633 | 5.5 | 10.9 | 46.0 | 0.64 percent |

## Ten slowest windows by 99th percentile

| Window start (seconds since 1 January 1970 UTC) | Resolved | Median s | 99th s |
|---:|---:|---:|---:|
| 1792116600 | 2,472 | 6.1 | 971.6 |
| 1792140000 | 3,287 | 6.1 | 971.6 |
| 1792144200 | 2,918 | 6.5 | 971.6 |
| 1792149000 | 2,928 | 9.2 | 971.6 |
| 1792170900 | 3,136 | 6.5 | 971.6 |
| 1792171500 | 3,573 | 6.1 | 971.6 |
| 1792181400 | 3,476 | 6.5 | 971.6 |
| 1792182300 | 3,115 | 6.5 | 971.6 |
| 1792195800 | 2,464 | 6.1 | 971.6 |
| 1792198500 | 2,132 | 6.9 | 971.6 |

## Reading notes

1. Delays are measured on a log scale with 40 bins per decade, so each figure is the centre of its bin, accurate to about 3 percent.
2. Groups with fewer than 50 resolved transactions are suppressed.
3. Ethereum blocks are produced on a fixed cadence, so inclusion delays cluster around block times. An operator's stage delays will have their own shape.
4. Unresolved transactions are counted and excluded from delay figures.
