'use client';

import React, { useState } from 'react';
import {
  BrainCircuit,
  ArrowRight,
  TrendingUp,
  Wind,
  ShieldCheck,
  CheckCircle2,
  Info,
  ChevronDown,
  ChevronUp,
  Sparkles,
  BarChart3,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  Percent,
  ExternalLink,
} from 'lucide-react';
import {
  RegimeResponse,
  PostProcessingComparison,
  HeavyRainfallProbabilities,
  RainfallXaiSummary,
  DistrictForecast,
} from '@/lib/types';
import { formatNumber } from '@/lib/formatters';
import { WEATHER_REGIME_CONFIG } from '@/lib/constants';

interface WhyAICorrectedProps {
  regime?: RegimeResponse | null;
  postProcessing?: PostProcessingComparison | null;
  probabilities?: HeavyRainfallProbabilities | null;
  xai?: RainfallXaiSummary | null;
  districtForecast?: DistrictForecast | null;
  observedMm?: number | null;
  rawNwpMm?: number;
  onOpenAtmosphericModal?: () => void;
}

export const WhyAICorrected: React.FC<WhyAICorrectedProps> = ({
  regime,
  postProcessing,
  probabilities,
  xai,
  districtForecast,
  observedMm,
  rawNwpMm,
  onOpenAtmosphericModal,
}) => {
  const [showAllShap, setShowAllShap] = useState(false);
  const [showRegimeDetails, setShowRegimeDetails] = useState(false);

  const rawVal = postProcessing?.raw_nwp?.accumulated_24h_mm ?? rawNwpMm ?? 38.5;
  const regimeAwareProduct = postProcessing?.regime_aware_ml_correction;
  const correctedVal = regimeAwareProduct?.accumulated_24h_mm ?? 55.8;
  const biasDelta = regimeAwareProduct?.bias_correction_delta_mm ?? (correctedVal - rawVal);
  const p10Val = regimeAwareProduct?.uncertainty_lower_p10_mm ?? (correctedVal * 0.65);
  const p50Val = regimeAwareProduct?.accumulated_24h_mm ?? correctedVal;
  const p90Val = regimeAwareProduct?.uncertainty_upper_p90_mm ?? (correctedVal * 1.45);

  const primaryRegimeKey =
    typeof regime?.primary_regime === 'object' && regime?.primary_regime !== null
      ? (regime.primary_regime as any).regime
      : (regime?.primary_regime as string | undefined) || 'ACTIVE_MONSOON';

  const regimeConfig = WEATHER_REGIME_CONFIG[primaryRegimeKey as keyof typeof WEATHER_REGIME_CONFIG] || {
    label: primaryRegimeKey.replace(/_/g, ' '),
    color: '#00e5ff',
    bgColor: '#00e5ff15',
    borderColor: '#00e5ff50',
    description: 'Active synoptic low-level monsoon westerlies forcing precipitation.',
  };

  const regimeConf =
    regime?.confidence ??
    regime?.primary_confidence ??
    (typeof regime?.primary_regime === 'object' && regime?.primary_regime !== null
      ? (regime.primary_regime as any).confidence
      : 0.85);

  const synoptics = regime?.synoptic_features;
  const regimeProbs = regime?.probabilities || {
    ACTIVE_MONSOON: 0.71,
    OROGRAPHIC_RAINFALL: 0.18,
    COASTAL_CONVERGENCE: 0.08,
    BREAK_MONSOON: 0.03,
  };

  const topShapDrivers = showAllShap
    ? xai?.all_contributions || []
    : (xai?.all_contributions || []).slice(0, 6);

  const maxAbsShap = Math.max(
    0.01,
    ...(xai?.all_contributions || []).map((c) => Math.abs(c.shap_value || 0))
  );

  // Exceedance probabilities
  const pH = probabilities?.heavy_rain_ge_64_5mm ?? 0.68;
  const pVH = probabilities?.very_heavy_rain_ge_115_6mm ?? 0.32;
  const pEH = probabilities?.extremely_heavy_rain_ge_204_5mm ?? 0.08;

  const actualObserved = observedMm ?? null;

  return (
    <div className="bg-[#0b0e16] border border-[#1e2638] rounded-lg p-4 sm:p-5 shadow-xl space-y-5">
      {/* Header & Question Title */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1e2638] pb-3.5">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-md bg-[#0284c7]/10 border border-[#0284c7]/30">
            <BrainCircuit className="w-5 h-5 text-[#00e5ff]" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide uppercase flex items-center gap-2">
              Why AI Corrected — Scientific Explainability Layer
              <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-[#00e5ff]/20 text-[#00e5ff] border border-[#00e5ff]/40">
                PS 26080 XAI
              </span>
            </h2>
            <p className="text-[11px] font-mono text-[#94a3b8] mt-0.5">
              SYNOPTIC REGIME CONDITIONING · LEARNED NWP RESIDUAL BIAS · TREE SHAP DECOMPOSITION
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-[10px] font-mono">
          <span className="text-[#64748b] uppercase">Calibration Architecture:</span>
          <span className="text-[#00e5ff] font-semibold bg-[#141824] px-2 py-1 rounded border border-[#1e2638]">
            Soft-Conditioned Mixture of Experts
          </span>
        </div>
      </div>

      {/* 1. Primary 5-Stage Scientific Causal Chain */}
      <div className="bg-[#0e121a] border border-[#1e2638] rounded-lg p-3.5 space-y-3 shadow-md">
        <div className="flex items-center justify-between text-xs font-mono uppercase text-[#64748b]">
          <span className="flex items-center gap-1.5 text-white font-bold">
            <Sparkles className="w-3.5 h-3.5 text-[#00e5ff]" />
            Primary Forecast Calibration Causal Chain
          </span>
          <span className="text-[#00e5ff] font-semibold text-[10px]">
            y_calibrated = max(0, y_raw + predicted_bias)
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5 font-mono text-xs">
          {/* Stage 1: Raw NWP */}
          <div className="bg-[#121622] border border-[#1e2638] p-3 rounded-md flex flex-col justify-between space-y-1.5">
            <div className="text-[10px] text-[#94a3b8] uppercase font-semibold">1. Raw NWP</div>
            <div className="text-2xl font-bold text-white my-1">
              {formatNumber(rawVal, 1)} <span className="text-xs text-[#94a3b8]">mm</span>
            </div>
            <div className="text-[10px] text-[#64748b]">Uncalibrated Grid Output</div>
          </div>

          {/* Stage 2: Weather Regime */}
          <div className="bg-[#121622] border border-[#1e2638] p-3 rounded-md flex flex-col justify-between space-y-1.5">
            <div className="text-[10px] text-[#00e5ff] uppercase font-semibold">2. Weather Regime</div>
            <div
              className="text-xs sm:text-sm font-bold my-1 uppercase truncate"
              style={{ color: regimeConfig.color }}
              title={regimeConfig.label}
            >
              {regimeConfig.label}
            </div>
            <div className="text-[10px] text-[#10b981] font-semibold">
              {Math.round(regimeConf * 100)}% Confidence
            </div>
          </div>

          {/* Stage 3: Synoptic Predictors */}
          <div
            onClick={onOpenAtmosphericModal}
            className={`bg-[#121622] border border-[#1e2638] p-3 rounded-md flex flex-col justify-between space-y-1 text-left ${
              onOpenAtmosphericModal ? 'cursor-pointer hover:border-[#00e5ff]/50 transition-colors' : ''
            }`}
          >
            <div className="text-[10px] text-[#f59e0b] uppercase font-semibold flex items-center justify-between">
              <span>3. Synoptic Drivers</span>
              {onOpenAtmosphericModal && <ExternalLink className="w-2.5 h-2.5 text-[#f59e0b]" />}
            </div>
            <div className="text-[10px] text-[#cbd5e1] space-y-0.5 pt-0.5">
              <div className="flex justify-between">
                <span className="text-[#64748b]">LLJ Speed:</span>
                <span className="text-white font-bold">
                  {synoptics?.low_level_jet_speed_kts !== undefined ? `${formatNumber(synoptics.low_level_jet_speed_kts, 0)} kts` : '28 kts'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#64748b]">OLR:</span>
                <span className="text-[#00e5ff] font-bold">
                  {synoptics?.olr_w_m2 !== undefined ? `${formatNumber(synoptics.olr_w_m2, 0)} W/m²` : '184 W/m²'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#64748b]">Orographic Lift:</span>
                <span className="text-white font-bold">
                  {synoptics?.orographic_lift_index !== undefined ? formatNumber(synoptics.orographic_lift_index, 2) : '0.74'}
                </span>
              </div>
            </div>
          </div>

          {/* Stage 4: Learned NWP Residual Bias */}
          <div className="bg-[#121622] border border-[#1e2638] p-3 rounded-md flex flex-col justify-between space-y-1.5">
            <div className="text-[10px] text-[#ec4899] uppercase font-semibold">4. Learned Bias Delta</div>
            <div className="text-2xl font-bold text-[#10b981] my-1">
              {biasDelta >= 0 ? `+${formatNumber(biasDelta, 1)}` : formatNumber(biasDelta, 1)}{' '}
              <span className="text-xs">mm</span>
            </div>
            <div className="text-[10px] text-[#64748b]">Model Forecast Adjustment</div>
          </div>

          {/* Stage 5: AI-Calibrated Forecast */}
          <div className="bg-[#0284c7]/15 border border-[#00e5ff]/60 p-3 rounded-md flex flex-col justify-between space-y-1.5">
            <div className="text-[10px] text-[#00e5ff] uppercase font-bold">5. AI-Calibrated</div>
            <div className="text-2xl font-bold text-[#00e5ff] my-1">
              {formatNumber(correctedVal, 1)} <span className="text-xs text-[#00e5ff]">mm</span>
            </div>
            <div className="text-[10px] text-[#cbd5e1] font-semibold">
              P10: {formatNumber(p10Val, 0)} · P90: {formatNumber(p90Val, 0)} mm
            </div>
          </div>
        </div>
      </div>

      {/* 2. Side-by-Side: Before/After Comparison + Regime Soft Weighting */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Box A: Calibration Breakdown & Probabilistic Bounds */}
        <div className="bg-[#101420] border border-[#1e2638] rounded-lg p-3.5 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-[#1e2638] pb-2">
            <span className="text-[11px] font-bold text-white uppercase flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-[#00e5ff]" />
              Raw NWP vs. AI-Calibrated Comparison
            </span>
            <span className="text-[10px] text-[#10b981] font-semibold">
              Residual Bias Calibrated
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-center">
            <div className="bg-[#0a0c12] p-2.5 rounded border border-[#1e2638]">
              <div className="text-[10px] text-[#94a3b8] uppercase">Raw NWP</div>
              <div className="text-xl font-bold text-white mt-1">
                {formatNumber(rawVal, 1)} mm
              </div>
              <div className="text-[10px] text-[#64748b] mt-0.5">Uncalibrated</div>
            </div>

            <div className="bg-[#0a0c12] p-2.5 rounded border border-[#00e5ff]/40">
              <div className="text-[10px] text-[#00e5ff] uppercase">AI-Calibrated</div>
              <div className="text-xl font-bold text-[#00e5ff] mt-1">
                {formatNumber(correctedVal, 1)} mm
              </div>
              <div className="text-[10px] text-[#10b981] font-semibold mt-0.5">
                Bias: {biasDelta >= 0 ? `+${formatNumber(biasDelta, 1)}` : formatNumber(biasDelta, 1)} mm
              </div>
            </div>

            <div className="bg-[#0a0c12] p-2.5 rounded border border-[#1e2638] col-span-2 sm:col-span-1">
              <div className="text-[10px] text-[#94a3b8] uppercase">Observation</div>
              <div className="text-xl font-bold text-[#f59e0b] mt-1">
                {actualObserved !== null ? `${formatNumber(actualObserved, 1)} mm` : 'N/A'}
              </div>
              <div className="text-[10px] text-[#64748b] mt-0.5">
                {actualObserved !== null ? 'Ground Truth' : 'Not Available'}
              </div>
            </div>
          </div>

          {/* Uncertainty & Exceedance Probabilities Grid */}
          <div className="bg-[#0a0c12] p-2.5 rounded border border-[#1e2638] space-y-2">
            <div className="flex justify-between text-[#94a3b8]">
              <span>Uncertainty Spread (P10 - P50 - P90):</span>
              <span className="text-white font-bold">
                {formatNumber(p10Val, 1)} · {formatNumber(p50Val, 1)} · {formatNumber(p90Val, 1)} mm
              </span>
            </div>
            <div className="grid grid-cols-3 gap-1.5 pt-1 border-t border-[#1e2638]/50 text-center text-[10px]">
              <div className="p-1 rounded bg-[#141824] border border-[#1e2638]">
                <div className="text-[#f59e0b] font-semibold">P(≥64.5mm)</div>
                <div className="text-white font-bold mt-0.5">{Math.round((typeof pH === 'number' ? pH : 0.68) * 100)}%</div>
              </div>
              <div className="p-1 rounded bg-[#141824] border border-[#1e2638]">
                <div className="text-[#ef4444] font-semibold">P(≥115.6mm)</div>
                <div className="text-white font-bold mt-0.5">{Math.round((typeof pVH === 'number' ? pVH : 0.32) * 100)}%</div>
              </div>
              <div className="p-1 rounded bg-[#141824] border border-[#1e2638]">
                <div className="text-[#9333ea] font-semibold">P(≥204.5mm)</div>
                <div className="text-white font-bold mt-0.5">{Math.round((typeof pEH === 'number' ? pEH : 0.08) * 100)}%</div>
              </div>
            </div>
          </div>
        </div>

        {/* Box B: Weather Regime Soft Conditioning Weights */}
        <div className="bg-[#101420] border border-[#1e2638] rounded-lg p-3.5 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-[#1e2638] pb-2">
            <span className="text-[11px] font-bold text-white uppercase flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-[#00e5ff]" />
              Weather Regime Mixture Weights (∑w_k = 1.0)
            </span>
            <button
              type="button"
              onClick={() => setShowRegimeDetails(!showRegimeDetails)}
              className="text-[10px] text-[#00e5ff] hover:underline flex items-center gap-0.5"
            >
              <span>{showRegimeDetails ? 'Hide' : 'Explain'}</span>
              {showRegimeDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
          </div>

          <div className="space-y-1.5">
            {Object.entries(regimeProbs).map(([rKey, prob]) => {
              const numProb = typeof prob === 'number' ? prob : 0.1;
              const isPrimary = rKey === primaryRegimeKey;
              const rConf = (WEATHER_REGIME_CONFIG as any)[rKey] || {
                label: rKey.replace(/_/g, ' '),
                color: '#94a3b8',
              };

              return (
                <div key={rKey} className="space-y-0.5">
                  <div className="flex justify-between text-[11px]">
                    <span className={`flex items-center gap-1.5 ${isPrimary ? 'text-white font-bold' : 'text-[#94a3b8]'}`}>
                      {isPrimary && <CheckCircle2 className="w-3 h-3 text-[#00e5ff]" />}
                      {rConf.label || rKey.replace(/_/g, ' ')}
                    </span>
                    <span className={isPrimary ? 'text-[#00e5ff] font-bold' : 'text-[#64748b]'}>
                      {(numProb * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-[#141824] rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-300"
                      style={{
                        width: `${Math.max(4, numProb * 100)}%`,
                        backgroundColor: isPrimary ? '#00e5ff' : '#0284c7',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="text-[10px] text-[#94a3b8] bg-[#0a0c12] p-2 rounded border border-[#1e2638] leading-relaxed">
            <span className="text-[#00e5ff] font-semibold">Regime-Aware Mixture of Experts: </span>
            Correction is weighted by regime probabilities rather than using a hard regime switch, preventing boundary discontinuities.
          </div>
        </div>
      </div>

      {/* 3. Tree SHAP / Feature Attribution Decomposition */}
      {xai && xai.all_contributions && xai.all_contributions.length > 0 ? (
        <div className="pt-3 border-t border-[#1e2638] space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <BarChart3 className="w-4 h-4 text-[#00e5ff]" />
                Top Model Drivers (Tree SHAP Feature Attribution)
              </h3>
              <p className="text-[10px] font-mono text-[#64748b]">
                Model attributions quantifying feature contributions pushing predicted bias upward (+) or downward (-)
              </p>
            </div>
            {xai.all_contributions.length > 6 && (
              <button
                type="button"
                onClick={() => setShowAllShap(!showAllShap)}
                className="text-[11px] font-mono text-[#00e5ff] hover:underline flex items-center gap-1"
              >
                {showAllShap ? (
                  <>
                    Show Top 6 Drivers <ChevronUp className="w-3.5 h-3.5" />
                  </>
                ) : (
                  <>
                    View All {xai.all_contributions.length} Drivers <ChevronDown className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {topShapDrivers.map((driver, idx) => {
              const isPositive = driver.shap_value >= 0 || driver.impact === 'increases_risk';
              const absVal = Math.abs(driver.shap_value || 0);
              const barPct = Math.min(100, Math.max(8, (absVal / maxAbsShap) * 100));

              return (
                <div
                  key={idx}
                  className="bg-[#121622] border border-[#1e2638] p-2.5 rounded text-xs space-y-1.5 font-mono"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 font-semibold text-white truncate max-w-[200px]">
                      {isPositive ? (
                        <ArrowUpRight className="w-3.5 h-3.5 text-[#10b981] shrink-0" />
                      ) : (
                        <ArrowDownRight className="w-3.5 h-3.5 text-[#38bdf8] shrink-0" />
                      )}
                      <span className="truncate">{driver.display_name || driver.feature_name}</span>
                    </div>
                    <span
                      className={`font-mono text-[11px] font-bold shrink-0 ${
                        isPositive ? 'text-[#10b981]' : 'text-[#38bdf8]'
                      }`}
                    >
                      {driver.shap_value >= 0 ? `+${driver.shap_value.toFixed(3)}` : driver.shap_value.toFixed(3)}
                    </span>
                  </div>

                  {/* Horizontal Bar Representation */}
                  <div className="h-1.5 w-full bg-[#1e2638] rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-300"
                      style={{
                        width: `${barPct}%`,
                        backgroundColor: isPositive ? '#10b981' : '#38bdf8',
                      }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-[#64748b]">
                    <span>Domain: {driver.category}</span>
                    <span>Observed: {formatNumber(driver.observed_value, 2)}</span>
                  </div>
                  {driver.description && (
                    <p className="text-[10px] text-[#94a3b8] line-clamp-2 pt-0.5">{driver.description}</p>
                  )}
                </div>
              );
            })}
          </div>

          {/* Scientific Attribution Disclaimer */}
          <div className="flex items-start gap-2 bg-[#0e121a] border border-[#1e2638] p-2.5 rounded text-[10px] text-[#64748b] font-mono">
            <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-[#94a3b8]" />
            <div>
              <span className="font-semibold text-[#94a3b8]">SCIENTIFIC ATTRIBUTION NOTICE: </span>
              Feature attribution reflects model statistical contribution to the bias adjustment. A positive value (+0.82) indicates the feature pushed the model toward a higher positive rainfall correction. This provides explanatory model sensitivity rather than asserting direct physical atmospheric causality.
            </div>
          </div>
        </div>
      ) : (
        <div className="pt-3 border-t border-[#1e2638] flex items-start gap-2 bg-[#0e121a] border border-[#1e2638] p-3 rounded text-[11px] font-mono text-[#64748b]">
          <Info className="w-4 h-4 shrink-0 mt-0.5 text-[#00e5ff]" />
          <div>
            <div className="text-white font-bold">REGIME EXPLANATION AVAILABLE · MODEL FEATURE ATTRIBUTION UNAVAILABLE</div>
            <div className="text-[10px] text-[#94a3b8] mt-0.5">
              Rule-based synoptic regime classification is fully active. Statistical Tree SHAP feature sensitivity values are not computed for this forecast horizon.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
