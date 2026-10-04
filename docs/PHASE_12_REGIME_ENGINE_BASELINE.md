# Phase 12: Weather Regime Engine Baseline Audit

## 1. Executive Summary

This document audits and establishes the frozen baseline of the South Asian Summer Monsoon (SASM) Weather Regime Engine prior to Phase 12 temporal intelligence upgrades.

---

## 2. Existing Regime Taxonomy

The system defines 7 meteorological regimes rooted in established MoES / IMD synoptic meteorology:

1. `ACTIVE_MONSOON`: Strong cross-equatorial Low-Level Jet ($V_{850} \ge 25\text{ kts}$), monsoon trough positioned south of normal ($21^\circ\text{N}–24^\circ\text{N}$), deep convection ($\text{OLR} < 200\text{ W/m}^2$).
2. `BREAK_MONSOON`: Monsoon trough shifted northwards to Himalayan foothills ($>27^\circ\text{N}$), weak Arabian Sea LLJ ($<15\text{ kts}$), suppressed central Indian convection.
3. `MONSOON_LOW_LPS`: Low-Pressure System / monsoon depression over Bay of Bengal or central India with cyclonic vorticity ($\zeta_{850} \ge 3.0 \times 10^{-5}\text{ s}^{-1}$) and negative MSLP departure.
4. `COASTAL_CONVERGENCE`: Strong onshore southwesterly moisture flux colliding with Konkan/Malabar coast, offshore trough activity, high low-level moisture.
5. `OROGRAPHIC_RAINFALL`: Wind impinging perpendicularly against the Western Ghats / Meghalaya plateau, high orographic lift index.
6. `WESTERN_DISTURBANCE`: Mid-tropospheric westerly trough, sub-tropical jet interaction over northwest India.
7. `NEUTRAL` (or `NEUTRAL_TRANSITIONAL`): Climatological baseline / transitional state.

---

## 3. Current Classifier Architecture

- **Classifier Type**: Hybrid Synoptic Rule Engine + Multi-Label Feature Attribution.
- **Multi-Label Concept**: Supports co-occurring regimes (e.g. `ACTIVE_MONSOON` + `OROGRAPHIC_RAINFALL`).
- **Probabilities & Confidence**: Full soft probability distribution $P(\text{regime}_k \mid \mathbf{x})$ summing to 1.0 with primary confidence calculation.
- **Explainability Drivers**: Grounded atmospheric indices (LLJ speed, shear, IVT proxy, vorticity, orographic lift).

---

## 4. Target Phase 12 Temporal Upgrades

1. **State Formalization**: `RegimeState(t)` and `RegimeFeatureSnapshot`.
2. **Temporal Sequences**: `RegimeSequence` capturing historical and forecast trajectories.
3. **Markov Transition Modeling**: Empirical transition matrix $P_{ij} = P(R_{t+1}=j \mid R_t=i)$ fitted strictly on training data ($2010–2019$) with Laplace smoothing.
4. **Regime Persistence & Duration**: Empirical empirical retention probabilities and mean durations.
5. **Day 1–10 Probability Propagation**: Multi-step Markov chain projection ($p_{t+k} = p_t P^k$) and forecast-conditioned mode.
6. **Explainable Regime Transitions**: Physical explanations derived from feature deltas ($\Delta \text{LLJ}$, $\Delta \text{IVT}$, $\Delta \text{vorticity}$).
