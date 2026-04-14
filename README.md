# Nonprofit Financial Resilience Analytics Platform

End-to-end implementation of the Aggie Hacks 2026 PRD using IRS Form 990 CSV extracts (2018-2024 analysis window).

## What This Project Does

This project runs all six PRD modules:

1. **Data Ingestion + Feature Engineering** (`src/data_pipeline.py`)
2. **Peer Benchmarking** (`src/peers.py`)
3. **Resilience Prediction + Scoring** (`src/resilience_model.py`)
4. **Financial Risk Simulation** (`src/risk_simulation.py`)
5. **High-Impact Discovery / Hidden Gems** (`src/hidden_gems.py`)
6. **Dashboard + Storytelling** (`app.py`)

All modules are orchestrated by `run_all.py`.

## Current Run Status

Validated successfully on the full dataset in this repo:

- Final records in `data/master_990.csv`: **396,910**
- Hidden gems in `data/hidden_gems.csv`: **27,208**
- At-risk rate: **25.4%**
- Best model in `artifacts/train_metrics.json`: **Random Forest**

## Repository Structure

- `data/data_csv/`: raw input CSV files (`*990*.csv`)
- `src/`: module implementations
- `run_all.py`: full pipeline runner
- `data/master_990.csv`: enriched master table
- `data/peer_group_stats.csv`: peer benchmark summary
- `data/simulation_results.csv`: scenario outputs
- `data/hidden_gems.csv`: hidden-gem leaderboard
- `artifacts/resilience_classifier.joblib`: trained model package
- `artifacts/train_metrics.json`: model metrics + top importances
- `outputs/`: EDA and model plots
- `app.py`: Streamlit app

## Full Run From Scratch

### 1) Environment setup

From project root:

```powershell
python --version
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Confirm raw data location

Ensure raw files are in:

- `data/data_csv/`

Required naming pattern:

- `*990*.csv` (examples: `2024_990.csv`, `2022_1_990.csv`)

### 3) Run the complete pipeline

```powershell
python run_all.py
```

Expected runtime on this machine/data size: about **6-7 minutes**.

### 4) Launch dashboard

```powershell
streamlit run app.py
```

Open the local URL shown by Streamlit in terminal.

## Running Again When New Data Is Added

When new IRS extract files arrive:

1. Copy new CSV(s) into `data/data_csv/` using the same naming convention (`*990*.csv`).
2. Re-run:

```powershell
python run_all.py
```

No code changes are required because file discovery is glob-based.

## Module Outputs

After `python run_all.py`, these files are regenerated:

- `data/master_990.csv`
  - cleaned, deduplicated, 2018-2024 filtered, engineered features, peer fields, risk fields, impact fields
- `data/peer_group_stats.csv`
  - peer-level median/mean/std/count for benchmark metrics
- `data/simulation_results.csv`
  - post-shock results for all scenarios
- `data/hidden_gems.csv`
  - ranked hidden gem candidates + donation tipping point
- `artifacts/resilience_classifier.joblib`
  - model + imputer + scaler + feature list
- `artifacts/train_metrics.json`
  - model comparison metrics, CV scores, top feature importances
- `outputs/eda_correlation_heatmap.png`
- `outputs/eda_feature_vs_target.png`
- `outputs/feature_importance.png`
- `outputs/model_comparison.csv`
- `outputs/threshold_heatmap_data.csv`

## Assumptions Made

1. **Input schema consistency:** All raw CSV files follow the 37-column structure documented in `PRD.md`.
2. **Panel years:** Analysis panel is strictly `TaxYear` 2018-2024.
3. **Deduplication rule:** latest `TaxPeriodEnd` is kept per (`EIN`, `TaxYear`).
4. **Missing government grants:** null `GovernmentGrantsAmt` means none reported and is set to 0.
5. **Employee sentinel:** values `> 50,000` are treated as invalid/sentinel and set to null.
6. **Negative total expenses:** treated as invalid and excluded after nulling.
7. **Sector fallback:** missing NTEE sector is inferred from mission text keywords.
8. **At-risk label:** constructed from PRD threshold logic (not externally observed failure labels).
9. **Shock simulation:** expenses are held constant in shock scenarios while revenue is shocked.
10. **Recovery model:** assumes fixed annual revenue recovery rate of 5%.

## Notes on Model Performance

Current model metrics are extremely high because the target (`AtRisk`) is rule-based from engineered financial features that overlap strongly with training inputs. This is expected for this setup, but for production use, consider:

- external outcome labels
- stricter temporal holdouts
- reduced feature leakage checks

## Troubleshooting

- **No input files found**
  - Confirm files exist under `data/data_csv/` and match `*990*.csv`.
- **Memory pressure**
  - Close other heavy apps, or process in chunked mode in future enhancement.
- **Streamlit page errors**
  - Re-run `python run_all.py` to regenerate missing outputs.

## Quick Commands

```powershell
# Full rebuild
python run_all.py

# Dashboard
streamlit run app.py
```
