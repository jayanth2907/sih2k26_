# DISTRICT WARNING INTELLIGENCE & DECISION SUPPORT

**SIH Problem Statement 26080**: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts  
**Ministry of Earth Sciences (MoES) / NCMRWF**  
**Document Classification**: Decision-Support Specification & Warning Intelligence Guidelines  

---

## 1. Statutory Disclaimer & Institutional Boundaries

> [!IMPORTANT]
> **MANDATORY LEGAL & INSTITUTIONAL DISCLAIMER**:
> This platform produces **PROTOTYPE MODEL-DERIVED DECISION SUPPORT** for meteorological and disaster management research. It does **NOT** issue statutory weather warnings, alerts, or color-coded advisories. Statutory forecasts and public warnings for India are solely issued by the **India Meteorological Department (IMD)**.

---

## 2. Deterministic Decision Support Categories

The system classifies district rainfall risk into four deterministic tiers based on physical rainfall accumulation envelopes and configurable probability escalation triggers:

```
+-------------------------------------------------------------------------------+
|                            DETERMINISTIC RULE MATRIX                          |
+-------------------------------------------------------------------------------+
|  TIER 1: EXTREMELY HEAVY RAINFALL                                             |
|  Trigger: P50 >= 204.5 mm  OR  P(>=204.5) >= 25%  OR  Area(>=204.5) >= 20%    |
+-------------------------------------------------------------------------------+
|  TIER 2: VERY HEAVY RAINFALL                                                  |
|  Trigger: P50 >= 115.6 mm  OR  P(>=115.6) >= 40%  OR  Area(>=115.6) >= 30%    |
+-------------------------------------------------------------------------------+
|  TIER 3: HEAVY RAINFALL                                                       |
|  Trigger: P50 >= 64.5 mm   OR  P(>=64.5)  >= 55%  OR  Area(>=64.5)  >= 40%    |
+-------------------------------------------------------------------------------+
|  TIER 4: NORMAL / MODERATE                                                    |
|  Trigger: P50 < 64.5 mm    AND Probabilities & Area below escalation triggers |
+-------------------------------------------------------------------------------+
```

---

## 3. Threshold Configuration Matrix

| Parameter | Configuration Key | Default Value | Nature of Threshold |
| :--- | :--- | :--- | :--- |
| **Heavy Accumulation Limit** | `accumulation_heavy_mm` | $64.5\text{ mm/24h}$ | IMD-Aligned Physical Definition |
| **Very Heavy Accumulation Limit** | `accumulation_very_heavy_mm` | $115.6\text{ mm/24h}$ | IMD-Aligned Physical Definition |
| **Extreme Accumulation Limit** | `accumulation_extreme_mm` | $204.5\text{ mm/24h}$ | IMD-Aligned Physical Definition |
| **Heavy Escalation Probability** | `heavy_probability_threshold` | $0.55$ ($55\%$) | Configurable Prototype Model Trigger |
| **Very Heavy Escalation Probability** | `very_heavy_probability_threshold` | $0.40$ ($40\%$) | Configurable Prototype Model Trigger |
| **Extreme Escalation Probability** | `extreme_probability_threshold` | $0.25$ ($25\%$) | Configurable Prototype Model Trigger |
| **Heavy Area Trigger** | `heavy_area_fraction_threshold` | $0.40$ ($40\%$) | Configurable Spatial Coverage Trigger |
| **Very Heavy Area Trigger** | `very_heavy_area_fraction_threshold` | $0.30$ ($30\%$) | Configurable Spatial Coverage Trigger |
| **Extreme Area Trigger** | `extreme_area_fraction_threshold` | $0.20$ ($20\%$) | Configurable Spatial Coverage Trigger |

---

## 4. Atmospheric Driver Attribution

For every district, the system extracts the physical atmospheric features governing post-processing corrections:
- **Low-Level Jet (LLJ)**: $850\text{ hPa}$ wind speed ($m/s$).
- **Integrated Vapor Transport (IVT)**: Total column water vapor flux ($kg/m/s$).
- **Tropospheric Humidity**: $850\text{ hPa}$ and $700\text{ hPa}$ Relative Humidity ($\%$).
- **Surface Pressure Anomaly**: Mean Sea Level Pressure deviation from regional mean ($\text{hPa}$).
- **Thermodynamic Instability**: Convective Available Potential Energy ($\text{CAPE}$, $J/kg$).
- **Cyclonic Vorticity**: $850\text{ hPa}$ relative vorticity ($10^{-5}\text{ s}^{-1}$).
- **Orographic Lift Index**: Vector product of low-level winds and terrain gradient.
- **Coastal Convergence Index**: Land-sea thermal and roughness discontinuity metric.

---

## 5. Machine-Generated Meteorological Bulletins

The system produces structured, human-readable meteorological outlook bulletins deterministically without LLM hallucination. Each bulletin features:
1. District & State Identification
2. 24-Hour Quantitative Precipitation Summary (Mean, P50, P10, P90, Max, Min)
3. Exceedance Probabilities ($\ge 64.5, 115.6, 204.5\text{ mm}$)
4. Spatial Area Exposure Percentages
5. Synoptic Regime & Atmospheric Driver Attribution
6. Model-Derived Decision Category & Explicit Scientific Basis
7. Complete Provenance & Statutory Disclaimers
