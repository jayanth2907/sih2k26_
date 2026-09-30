# Chronological Dataset Structure for PS26080

This directory contains meteorological training, validation, and test datasets partitioned using **strict chronological splitting** to avoid temporal data leakage and respect physical causality.

## Split Partitioning Strategy

* **Training Set (`data/training/`)**: Historical monsoon seasons **2018 – 2022** (June 1 – Sept 30). Used for fitting regime classification models (XGBoost/LightGBM) and post-processing error-correction models.
* **Validation Set (`data/validation/`)**: Monsoon season **2023** (June 1 – Sept 30). Used for hyperparameter tuning, threshold calibration, and early stopping.
* **Test Set (`data/test/`)**: Monsoon seasons **2024 – 2025** (June 1 – Sept 30). Used exclusively for out-of-sample meteorological evaluation and lead-time verification.

## Scientific Rules
1. **No Random Shuffling**: Random `train_test_split` is strictly prohibited because spatial and temporal auto-correlation in atmospheric flow fields causes severe optimistic bias.
2. **Causality Integrity**: Forecast initialization timestamps must always precede or equal observation timestamps ($t_{obs} \ge t_{init}$).
3. **Missing Grid Attribution**: All records must contain `data_source` and `is_demo` tags.
