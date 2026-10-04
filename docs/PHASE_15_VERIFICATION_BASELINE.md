# PHASE 15 — ADVANCED VERIFICATION BASELINE & FORENSIC AUDIT

**SIH Problem Statement 26080**: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts  
**Ministry of Earth Sciences (MoES) / NCMRWF**  
**Document Classification**: Forensic Verification Audit & Baseline Inventory  

---

## 1. Scope & Objective

This document inventories all pre-existing verification metrics, mathematical definitions, evaluation partitions, and benchmarks established across Phases 1–14 of the PS26080 system.

The objective of Phase 15 is **NOT** to declare a universal "winner" or compute an aggregated single score. The objective is to evaluate metric-specific trade-offs, spatial resolution dependencies, weather regime sensitivity, threshold-dependent skill, probabilistic calibration, and uncertainty interval reliability across the complete post-processing chain.

---

## 2. Chronological Data Partitions & Evaluation Populations

To guarantee strict zero-leakage governance (Rule 12–14, 18), all models are evaluated on identical, chronologically partitioned datasets:

| Partition | Date Span | Sample Count | Event Count ($R \ge 64.5\text{ mm}$) | Role in System Lifecycle |
| :--- | :--- | :--- | :--- | :--- |
| **Training Partition** | JJAS 2010–2019 (10 Monsoons) | 1,708 Daily Grids (~1.7M cells) | 48,120 Events | Model weights & bias feature fitting |
| **Validation Partition** | JJAS 2020–2021 (2 Monsoons) | 340 Daily Grids (~340k cells) | 9,840 Events | Hyperparameter selection & probability tuning |
| **Held-Out Test Partition** | JJAS 2022–2023 (2 Monsoons) | 1,020 Benchmark Samples | 292 Heavy Events | **Primary Independent Scientific Benchmark** |

---

## 3. Evaluated Model Chain

| Model Identifier | Architecture Description | Primary Strengths | Limitations |
| :--- | :--- | :--- | :--- |
| **`RAW_NWP`** | Numerical Weather Prediction Baseline (NCUM 12km / GFS 0.25°) | Unbiased physical dynamics | Large convective displacement & underprediction of extremes |
| **`QUANTILE_MAPPING`** | Empirical Quantile Mapping (EQM) | Climatological cumulative distribution matching | Cannot adapt to changing synoptic flow regimes |
| **`GLOBAL_ML`** | Gradient Boosted Residual Regressor (Non-Regime) | Non-linear atmospheric predictor mapping | Smooths orographic extremes across regional boundaries |
| **`REGIME_AWARE_ML`** | Physics-Guided Regime-Gated Error Post-Processor | Regime-specific error compensation | 1D single-cell local formulation |
| **`REGIME_AWARE_TEMPORAL_V2`**| Multi-Horizon Regime Transition Engine (Phase 12) | Dynamic lead-time & regime persistence tracking | 1D point representation |
| **`SPATIAL_REGIME_AWARE`** | 2D Spatially Coherent Regime ConvNet (Phase 13) | Spatial context ($3\times3, 5\times5$), 2D error fields | Higher memory footprint for national inference |

---

## 4. Summary of Verification Baseline Metrics

1. **Continuous Metrics**:
   - $\text{RMSE} = \sqrt{\frac{1}{N}\sum (f_i - o_i)^2}$
   - $\text{MAE} = \frac{1}{N}\sum |f_i - o_i|$
   - $\text{Bias} = \frac{1}{N}\sum (f_i - o_i)$ (Sign convention: positive = overprediction, negative = underprediction)
2. **Categorical Threshold Metrics ($64.5, 115.6, 204.5\text{ mm}$)**:
   - $\text{CSI} = \frac{a}{a + b + c}$
   - $\text{ETS} = \frac{a - a_{\text{rand}}}{a + b + c - a_{\text{rand}}}$
   - $\text{POD} = \frac{a}{a + c}$
   - $\text{FAR} = \frac{b}{a + b}$
3. **Probabilistic Calibration**:
   - $\text{Brier Score} = \frac{1}{N}\sum (p_i - o_i)^2$
   - $\text{ECE} = \sum_{b=1}^{B} \frac{N_b}{N} |\bar{p}_b - \bar{o}_b|$
4. **Uncertainty Interval Coverage**:
   - Nominal 80% coverage rate for $[P_{10}, P_{90}]$.
5. **Spatial Neighborhood Skill**:
   - Fractions Skill Score ($\text{FSS}$) at 25km, 50km, and 100km neighborhood footprints.
