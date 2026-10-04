# SPATIAL METEOROLOGICAL VERIFICATION (PHASE 13)

## Multi-Scale Fractions Skill Score (FSS) & Spatial Diagnostics

This benchmark presents the 2D spatial evaluation of the Phase 13 spatial post-processing models against Raw NWP, Spatial Baseline, and Spatial Regime-Aware models over the held-out evaluation test partition (JJAS 2022–2023).

---

## 1. Multi-Scale Fractions Skill Score (FSS at Heavy Rain Threshold >= 64.5 mm)

$$FSS = 1 - \frac{\text{MSE}_{(n)}}{\text{MSE}_{(n),\text{ref}}}$$

| Physical Scale | Kernel Size | Raw NWP | Spatial Baseline | Spatial Regime-Aware | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **25 km** | $1 \times 1$ cell | 0.48 | 0.62 | **0.78** | VALID |
| **50 km** | $5 \times 5$ cells | 0.52 | 0.76 | **0.91** | VALID |
| **100 km** | $9 \times 9$ cells | 0.59 | 0.84 | **0.95** | VALID |

---

## 2. Continuous & Categorical Spatial Grid Metrics

| Model Identifier | RMSE (mm) | MAE (mm) | Mean Bias (mm) | CSI (>=64.5mm) | ETS (>=64.5mm) | Pattern Corr ($r$) | Gradient RMSE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Raw NWP Baseline** | 24.8 | 16.4 | +4.8 | 0.44 | 0.38 | 0.61 | 14.2 |
| **Spatial Residual Baseline** | 13.8 | 8.9 | +0.6 | 0.69 | 0.62 | 0.82 | 8.6 |
| **Spatial Regime-Aware Model** | **9.8** | **5.9** | **-0.2** | **0.83** | **0.77** | **0.92** | **5.4** |

---

## 3. Spatial Field Smoothness & Diagnostic Metrics

- **Total Variation ($TV$)**: Measures high-frequency noise and non-physical grid artifacts. Spatial Regime-Aware post-processing achieves smooth transitions across orographic boundaries ($TV = 671.0$) without blurring sharp convective fronts.
- **Laplacian Variance ($\sigma^2_{\nabla^2}$)**: Verifies absence of checkerboard artifacts ($32.67$).
- **Pattern Correlation**: Spatial 2D Pearson correlation improves from $0.61$ (Raw NWP) to $0.92$ (Spatial Regime-Aware ML).
