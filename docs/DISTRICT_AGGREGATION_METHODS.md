# SPATIAL AGGREGATION METHODOLOGY FOR DISTRICT DECISION SUPPORT

**SIH Problem Statement 26080**: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts  
**Ministry of Earth Sciences (MoES) / NCMRWF**  
**Document Classification**: Mathematical Specification & Spatial Engine Design  

---

## 1. Overview & Architecture

To bridge the gap between 2D gridded meteorological fields (e.g. $0.25^\circ \times 0.25^\circ \approx 27\text{ km} \times 27\text{ km}$) and administrative decision jurisdictions, Phase 14 implements a **Geodesic Polygon Area-Weighted Aggregation Engine**.

```
+-------------------------------------------------------------+
|               2D Post-Processed Rainfall Grid               |
|      (Calibrated Rain, Quantiles P10/P50/P90, Exceedance P) |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|             Precomputed Spatial Weight Cache                |
|      (Fractional Polygon Intersection Area Weights w_ij)    |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|             District Statistical Aggregator                 |
|      (Area-Weighted Mean, Min, Max, Median, P90, P95)       |
+-------------------------------------------------------------+
                               |
            +------------------+------------------+
            |                                     |
            v                                     v
+-----------------------+             +-----------------------+
|  Threshold Fractions  |             | Exceedance Probabilities |
| (Area >= 64.5, 115.6) |             | (Monotonic P64.5>=P115.6) |
+-----------------------+             +-----------------------+
            |                                     |
            +------------------+------------------+
                               |
                               v
+-------------------------------------------------------------+
|              Deterministic Decision Engine                  |
|    (Prototype Categories & Structured Explanatory Reason)   |
+-------------------------------------------------------------+
```

---

## 2. Geodesic Area & Weight Formulation

### 2.1 Authalic Sphere Geodesic Area
Direct geographic multiplication $(\Delta\text{lat} \times \Delta\text{lon})$ introduces latitudinal area distortion (e.g., $1^\circ \times 1^\circ$ at $8^\circ\text{N} \approx 12,230\text{ km}^2$, while at $34^\circ\text{N} \approx 10,250\text{ km}^2$). Phase 14 calculates exact geodesic polygon areas on the authalic sphere ($R = 6,371.0088\text{ km}$) using spherical excess:

$$\text{Area}(D_k) = R^2 \sum_{i=1}^{N} \Delta\lambda_i \cdot \left(2 + \sin\phi_i + \sin\phi_{i+1}\right)$$

### 2.2 Grid-Cell Intersection Weights
For each district polygon $D_k$ and grid cell $C_{ij} = [\text{lon}_j - \frac{dx}{2}, \text{lon}_j + \frac{dx}{2}] \times [\text{lat}_i - \frac{dy}{2}, \text{lat}_i + \frac{dy}{2}]$:

$$A_{k, ij} = \text{Area}\left(D_k \cap C_{ij}\right)$$

The normalized spatial weight $w_{k, ij}$ satisfies:

$$w_{k, ij} = \frac{A_{k, ij}}{\sum_{(i', j') \in D_k} A_{k, i'j'}} \quad \text{such that} \quad \sum_{(i, j) \in D_k} w_{k, ij} = 1.0$$

---

## 3. Spatial Statistics Formulation

For a 2D scalar field $R(i, j)$ across intersected cells:

1. **Area-Weighted Mean Rainfall**:
   $$\bar{R}_k = \sum_{(i, j) \in D_k} w_{k, ij} R(i, j)$$

2. **Spatial Extrema**:
   $$R_{k, \max} = \max_{(i, j) \in D_k} R(i, j), \quad R_{k, \min} = \min_{(i, j) \in D_k} R(i, j)$$

3. **Spatial Distribution Quantiles (Median, P90, P95)**:
   Calculated by sorting values $R(i, j)$ with cumulative weights $W(r) = \sum_{R_{ij} \le r} w_{k, ij}$:
   $$P_{50} = W^{-1}(0.50), \quad P_{90} = W^{-1}(0.90), \quad P_{95} = W^{-1}(0.95)$$

4. **Threshold Area Exposure Fractions**:
   $$f_{\ge T, k} = \sum_{(i, j) \in D_k} w_{k, ij} \cdot \mathbb{I}\left(R(i, j) \ge T\right) \quad \text{for } T \in \{64.5, 115.6, 204.5\text{ mm}\}$$

---

## 4. Probability vs. Area Fraction Decoupling

Phase 14 strictly decouples **Model Confidence Probability** from **Physical Area Exposure**:

| Quantity | Mathematical Definition | Operational Meaning |
| :--- | :--- | :--- |
| **Exceedance Probability ($P_{\ge 64.5}$)** | $\sum_{(i,j)} w_{ij} P_{64.5}(i,j)$ | Model's calibrated confidence that heavy rain occurs. |
| **Heavy Area Fraction ($f_{\ge 64.5}$)** | $\sum_{(i,j)} w_{ij} \mathbb{I}(R_{ij} \ge 64.5)$ | Spatial percentage of the district territory receiving heavy rain. |

---

## 5. Missing Data & Quality Control

If a subset of grid cells are missing (e.g. domain boundary or coastal mask):

$$\text{Valid Area Fraction} = \frac{\sum_{\text{valid } (i,j)} A_{k, ij}}{\text{Area}(D_k)}$$

- If $\text{Valid Area Fraction} \ge 0.95$: `DataQualityStatus.VALID`
- If $0.60 \le \text{Valid Area Fraction} < 0.95$: `DataQualityStatus.PARTIAL`
- If $\text{Valid Area Fraction} < 0.60$: `DataQualityStatus.INSUFFICIENT_SPATIAL_COVERAGE` (Forecast withheld).

---

## 6. Population Weighting Status

- **Status**: **NOT AVAILABLE**
- **Policy**: In accordance with PS26080 scientific guidelines, Census population counts are **never fabricated**. Area-weighted aggregation remains the primary authoritative product.
