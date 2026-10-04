# Phase 12: Advanced Weather Regime Intelligence

## 1. Scientific Objective

Phase 12 elevates the South Asian Summer Monsoon (SASM) Weather Regime Engine from instantaneous snapshot diagnostics to a **scientifically grounded temporal regime intelligence system**.

The framework models:
1. **Regime State Vectors**: Multi-label probability distributions $P(\text{regime}_k \mid \mathbf{x}_t)$.
2. **Markov Regime Transitions**: Empirical 7×7 transition operator $\mathbf{P}$ fitted strictly on training data ($2010–2019$).
3. **Regime Persistence & Expected Duration**: Geometric memory models $E[\text{duration}] = 1 / (1 - P_{ii})$.
4. **Day 1–10 Probability Propagation**: Multi-step horizon projections $\mathbf{p}_{t+k} = \mathbf{p}_t \mathbf{P}^k$.
5. **Physical Transition Explainability**: Feature delta attribution ($\Delta \text{LLJ}$, $\Delta \text{IVT}$, $\Delta \text{vorticity}$).

---

## 2. Formal Regime State Representation

At any forecast or observation valid time $t$, the meteorological regime state is defined as:

$$\text{RegimeState}(t) = \left\{ t, \mathbf{x}_t, R_{\text{primary}}, \{R_{\text{active}}\}, \mathbf{p}_t, c_{\text{class}}, c_{\text{trans}}, P_{\text{persist}}, \mathbf{s}_t \right\}$$

Where:
- $\mathbf{p}_t = \left[ P(\text{Active}), P(\text{Break}), P(\text{LPS}), P(\text{Coastal}), P(\text{Orographic}), P(\text{WD}), P(\text{Neutral}) \right]^\top$
- $\sum_{k=1}^7 p_{t,k} = 1.0, \quad 0 \le p_{t,k} \le 1.0$
- $P_{\text{persist}} = P(R_{t+1} = R_t \mid R_t)$

---

## 3. Markov Transition Probability Matrix

For regimes $i, j \in \{1, \dots, 7\}$:

$$P_{ij} = P(R_{t+1} = j \mid R_t = i) = \frac{N(i \to j) + \alpha}{\sum_{k=1}^7 N(i \to k) + 7\alpha}$$

Where $\alpha = 1.0$ (Laplace smoothing). The transition operator $\mathbf{P}$ satisfies the stochastic row invariant:

$$\sum_{j=1}^7 P_{ij} = 1.0 \quad \forall i$$

---

## 4. Multi-Day Temporal Forecasting

For a forecast horizon of $k \in [1, 10]$ days ahead:

$$\mathbf{p}_{t+k} = \mathbf{p}_t \cdot \mathbf{P}^k$$

- **Forecast-Conditioned Mode**: When multi-level NWP forecast fields ($\mathbf{x}_{t+k}$) are available from NCUM/GFS, regime probabilities are diagnosed directly from future atmospheric predictors.
- **Transition-Based Projection Mode**: When future NWP fields are unprovisioned, probability propagation operates via the Markov transition operator $\mathbf{P}^k$.

> [!NOTE]
> **Scientific Disclosure**: Transition-based output is transparently labeled `TRANSITION_BASED_PROJECTION` and is never claimed to be an operational numerical weather forecast.
