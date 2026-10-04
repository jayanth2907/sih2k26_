# SPATIAL MODEL ARCHITECTURE (PHASE 13)

## Compact Convolutional & Spatial Regime-Aware Post-Processing Architecture

```
                       INPUT TENSOR [C, H, W]
  [Raw NWP, Multi-level Winds, RH, MSLP, CAPE, IVT, Terrain, Regime Probs]
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
     Multi-Scale Conv Block           Physical Orographic &
     (3x3 / 5x5 / Sobel / Laplacian)  Coastal Convergence Module
                 │                               │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                     Soft Regime-Gating Layer
         [P_ACTIVE, P_OROGRAPHIC, P_LPS, P_BREAK, P_WD]
                                 │
                                 ▼
                   Residual Error Field Delta_R(x,y)
                                 │
                                 ▼
         Corrected Field: R_corr(x,y) = max(0, R_nwp + Delta_R)
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
     Calibrated Exceedance            Spatial Quantiles
    Probability Fields [H, W]         Uncertainty Fields [H, W]
  (P64.5 >= P115.6 >= P204.5)        (0 <= P10 <= P50 <= P90)
```

### Key Structural Properties
1. **Residual Learning**: Output predicts the error field $\Delta\hat{R}(x,y)$, avoiding direct raw generation and preserving large-scale physical mass conservation.
2. **Physics & Regime Conditioning**: Topographic lift interacts directly with moisture transport proxy ($\text{IVT}$); convective Cape interacts with low-pressure system (LPS) probability.
3. **Monotonicity Guarantees**: Numerical post-processing enforces strict mathematical order on probability tiers and forecast quantiles.
4. **Governance**: Gated with `EXPERIMENTAL` status in the model registry.
