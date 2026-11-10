"""All registered constants in one place. Change nothing here after the code freeze tag."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    horizon_s: float = 86400.0          # unresolved after 24 hours (Section 4.1)
    w_candidates_s: tuple = (60.0, 300.0, 600.0, 1800.0, 3600.0)  # Section 4.2
    min_resolved_per_window: int = 1000  # median training window rule
    k_bins: int = 20                     # Section 4.3
    bin_lo_pct: float = 0.1
    bin_hi_pct: float = 99.9
    lags: int = 6                        # H_L lags 0 to 5, mean of last 6
    tau: float = 0.99                    # pinball quantile
    seed: int = 20261031                 # Section 6
    train_frac: float = 0.6
    val_frac: float = 0.2
    block_s: float = 86400.0             # bootstrap block spans 24 hours
    min_block: int = 10
    n_boot: int = 10000
    alpha: float = 0.05
    r_min: float = 0.05
    min_blocks: int = 3                  # AMENDMENT A1: dataset eligible only if test spans at least this many bootstrap blocks
    latency_floor_s: float = 0.001       # AMENDMENT A1: completion before arrival is clipped to this latency
    purge: bool = True                   # DECISION: drop windows whose target is unresolved at the split edge
    ewma_weight: float = 0.3             # P1
    q_estimator: str = "sojourn"         # DECISION: queueing estimator, see queueing.py
