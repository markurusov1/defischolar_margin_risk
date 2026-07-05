# defischolar_margin_risk

Simulation code for comparing **fixed Loan-to-Value (LTV) liquidation rules** used by
DeFi lending protocols (Aave-style) against a **TradFi-inspired dynamic portfolio-margin**
approach, applied to Uniswap v3 concentrated-liquidity positions used as collateral.

The project runs two simulations over the same historical ETH price range and compares
how often positions are liquidated under each model.

---

## Quick start

Requirements: Python 3.8+ with `pandas`, `numpy`, `scikit-learn`, and `matplotlib`.

```bash
pip install pandas numpy scikit-learn matplotlib
```

All scripts are run **from inside the `src/` directory** (imports assume `src/` is the
working directory):

```bash
cd src
python simulator.py          # 1. DeFi baseline
python hybrid_simulator.py   # 2. TradFi-inspired hybrid
python charts.py             # 3. Comparison figures + summary
```

**Run them in this order — it is a hard dependency chain, not a preference:**

1. `simulator.py` produces the DeFi baseline and copies its results into
   `output/paper_data/`.
2. `hybrid_simulator.py` **trains its regression on the DeFi baseline**, reading
   `output/paper_data/liquidation_timeseries.csv`. If run first (or on a fresh clone
   with no DeFi run yet) it falls back to a degraded "direct mode" and results will not
   match. Whenever `simulator.py` is re-run, re-run the hybrid too.
3. `charts.py` reads **both** the DeFi and hybrid results from `output/paper_data/` and
   generates the paper figures and `summary.txt`, so it must run last.

> Note: `simulator.py` takes roughly 10–15 minutes over the full price history
> (it rebuilds the position cohort each day).
> 
> After running everything, check output/paper_data/summary.txt to see the headline numbers (39,649 vs 929 liquidations)

---

## How the two models work

Both simulations use the same daily ETH/USD price series and the same random position
cohorts (see "Reproducibility" below).

- **Each simulated day** opens a fresh set of 500 Uniswap v3 positions created at that
  day's opening price (which equals the previous day's close in the data), and checks
  whether each position survives to the day's close.
- **DeFi baseline (`simulator.py`)** applies a fixed 65% LTV with a 70% liquidation
  threshold. A position is liquidated when its health factor falls below 1.
- **Hybrid (`hybrid_simulator.py`)** stress-tests each position across 11 price shocks
  (−15% … +15%), then applies a graduated "sliding scale": the worse the projected
  worst-case health factor, the more the borrowing limit is tightened (down to 35% LTV
  under severe stress), reducing loans *before* a liquidation would occur.

---

## Reproducibility

Both simulators call `random.seed(42)` once before their main loop. Because the seed and
the per-day position-creation order are identical across the two runs, **the DeFi and
hybrid simulations see the exact same position cohorts each day** — so the comparison
isolates the difference between the two liquidation rules, not luck of the draw. Re-running
either script on any machine reproduces the same numbers.

To check that a result is not an artifact of one seed, change `RANDOM_SEED` (defined near
the top of each simulator) to a few different values and confirm the reduction percentage
holds.

All results in the paper come from the latest runs saved in output/paper_data/