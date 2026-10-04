# Model Training & Artifact Documentation

## 1. Overview & Governance

This document describes model training reproducibility, hyperparameters, artifact formats, and governance rules for **SIH PS26080**.

---

## 2. Model Architecture Specifications

### Model 1: Raw NWP Forecast Baseline
- **Identifier**: `raw_nwp`
- **Type**: Numerical Weather Prediction baseline (NCUM / GFS)
- **Role**: Uncalibrated reference benchmark

### Model 2: Empirical Quantile Mapping (EQM)
- **Identifier**: `quantile_mapping`
- **Type**: Non-parametric distribution matching
- **CDF Binning**: 100 quantiles fitted strictly on training data ($2010–2019$)

### Model 3: Global ML (Stationary Regressor)
- **Identifier**: `global_ml`
- **Estimator**: `HistGradientBoostingRegressor`
- **Hyperparameters**: `learning_rate=0.05`, `max_iter=200`, `max_leaf_nodes=31`, `min_samples_leaf=20`, `l2_regularization=1.0`
- **Target**: Residual error $\epsilon = y_{\text{obs}} - y_{\text{raw}}$

### Model 4: Regime-Aware AI Post-Processing
- **Identifier**: `regime_aware_ml`
- **Estimator**: Soft-Conditioned Mixture-of-Experts (`SoftConditionedMixtureOfExperts`)
- **Expert Models**: Specialized Gradient Boosting estimators for Orographic, Coastal, and Synoptic regimes
- **Meta-Estimator**: L2 Regularized Ridge Blending ($\alpha=1.0$)
- **Target**: Regime-weighted residual calibration $\hat{\epsilon} = \sum_{k=1}^K P(r_k \mid \mathbf{x}) f_k(\mathbf{x})$

---

## 3. Artifact Directory Layout

```
artifacts/models/
├── global_ml/
│   └── v1/
│       ├── model.pkl
│       ├── metadata.json
│       └── feature_schema.json
└── regime_aware/
    └── v1/
        ├── model.pkl
        ├── metadata.json
        └── feature_schema.json
```

---

## 4. Operational Safety Rule

- **No Automated Replacement**: Retrained models are registered with `is_active_dashboard_model: false` and status `EXPERIMENTAL`. They undergo formal evaluation before prospective promotion.
