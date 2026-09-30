'use client';

import React from 'react';
import { CloudRain, Sparkles, AlertCircle, Compass, Gauge } from 'lucide-react';
import {
  RiskLevel,
  WarningStatus,
  WeatherRegimeType,
  HeavyRainfallProbabilities,
  PostProcessingComparison,
  PostProcessingModelId,
} from '@/lib/types';
import { WARNING_STATUS_CONFIG, WEATHER_REGIME_CONFIG } from '@/lib/constants';
import { formatCoordinates, formatNumber } from '@/lib/formatters';

interface MapHudProps {
  locationName: string;
  latitude: number;
  longitude: number;
  riskScore?: number | null;
  riskLevel?: RiskLevel | null;
  warningStatus?: WarningStatus | null;
  primaryRegime?: WeatherRegimeType | null;
  regimeConfidence?: number | null;
  postProcessing?: PostProcessingComparison | null;
  probabilities?: HeavyRainfallProbabilities | null;
  selectedModel?: PostProcessingModelId;
  rawNwpMm?: number | null;
  correctedMm?: number | null;
  deltaMm?: number | null;
  isDemo?: boolean;
}

export const MapHud: React.FC<MapHudProps> = ({
  locationName,
  latitude,
  longitude,
  warningStatus,
  primaryRegime,
  regimeConfidence,
  postProcessing,
  probabilities,
  selectedModel = 'regime_aware_ml',
  rawNwpMm,
  correctedMm,
  deltaMm,
  isDemo = true,
}) => {
  const activeWarning = warningStatus ? WARNING_STATUS_CONFIG[warningStatus] : null;
  const activeRegime = primaryRegime ? (WEATHER_REGIME_CONFIG as any)[primaryRegime] : null;

  const rawVal = postProcessing?.raw_nwp?.accumulated_24h_mm ?? rawNwpMm ?? 0.0;

  // Selected Model Dynamic Extraction
  let activeModelName = 'Regime-Aware ML';
  let activeModelMm = postProcessing?.regime_aware_ml_correction?.accumulated_24h_mm ?? correctedMm ?? rawVal;
  let activeDeltaMm = postProcessing?.regime_aware_ml_correction?.bias_correction_delta_mm ?? deltaMm ?? (activeModelMm - rawVal);
  let p10Mm = postProcessing?.regime_aware_ml_correction?.uncertainty_lower_p10_mm ?? Math.max(0, activeModelMm * 0.65);
  let p50Mm = activeModelMm;
  let p90Mm = postProcessing?.regime_aware_ml_correction?.uncertainty_upper_p90_mm ?? activeModelMm * 1.45;
  let uncertaintyWidth = p90Mm - p10Mm;

  if (selectedModel === 'raw_nwp') {
    activeModelName = 'Raw NWP (Baseline)';
    activeModelMm = rawVal;
    activeDeltaMm = 0.0;
    p10Mm = Math.max(0, rawVal * 0.7);
    p50Mm = rawVal;
    p90Mm = rawVal * 1.35;
    uncertaintyWidth = p90Mm - p10Mm;
  } else if (selectedModel === 'quantile_mapping') {
    activeModelName = 'Empirical Quantile Mapping';
    activeModelMm = postProcessing?.quantile_mapping?.accumulated_24h_mm ?? (rawVal * 1.15);
    activeDeltaMm = postProcessing?.quantile_mapping?.bias_correction_delta_mm ?? (activeModelMm - rawVal);
    p10Mm = Math.max(0, activeModelMm * 0.75);
    p50Mm = activeModelMm;
    p90Mm = activeModelMm * 1.3;
    uncertaintyWidth = p90Mm - p10Mm;
  } else if (selectedModel === 'global_ml') {
    activeModelName = 'Global ML Correction';
    activeModelMm = postProcessing?.global_ml_correction?.accumulated_24h_mm ?? (rawVal * 1.22);
    activeDeltaMm = postProcessing?.global_ml_correction?.bias_correction_delta_mm ?? (activeModelMm - rawVal);
    p10Mm = Math.max(0, activeModelMm * 0.8);
    p50Mm = activeModelMm;
    p90Mm = activeModelMm * 1.25;
    uncertaintyWidth = p90Mm - p10Mm;
  }

  const heavyProb = probabilities?.heavy_rain_ge_64_5mm ?? (activeModelMm >= 64.5 ? 0.74 : Math.min(0.95, activeModelMm / 85));
  const veryHeavyProb = probabilities?.very_heavy_rain_ge_115_6mm ?? (activeModelMm >= 115.6 ? 0.68 : Math.max(0.05, Math.min(0.9, (activeModelMm - 40) / 100)));
  const extremeProb = probabilities?.extremely_heavy_rain_ge_204_5mm ?? (activeModelMm >= 204.5 ? 0.52 : Math.max(0.01, Math.min(0.4, (activeModelMm - 100) / 150)));

  return (
    <div className="bg-[#0b0e16]/95 backdrop-blur-md border border-[#1e2638] rounded-lg p-3.5 shadow-2xl max-w-sm w-full space-y-3">
      {/* Target Coordinates & Synoptic Header */}
      <div className="border-b border-[#1e2638] pb-2 flex items-center justify-between">
        <div>
          <div className="text-white font-bold text-sm tracking-wide uppercase">{locationName}</div>
          <div className="font-mono text-[11px] text-[#94a3b8]">{formatCoordinates(latitude, longitude)}</div>
        </div>
        {activeRegime && (
          <span
            className="text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider font-mono"
            style={{
              color: activeRegime.color,
              backgroundColor: activeRegime.bgColor,
              border: `1px solid ${activeRegime.borderColor}`,
            }}
          >
            {activeRegime.shortCode}
          </span>
        )}
      </div>

      {/* Primary Regime & Warning Status */}
      <div className="grid grid-cols-2 gap-2">
        {/* Weather Regime */}
        <div className="bg-[#121622] border border-[#1e2638] p-2 rounded">
          <div className="text-[10px] font-mono uppercase text-[#64748b] flex items-center gap-1">
            <Compass className="w-3 h-3 text-[#00e5ff]" />
            Monsoon Regime
          </div>
          <div className="mt-1">
            <span
              className="text-xs font-bold block truncate"
              style={{ color: activeRegime?.color || '#00e5ff' }}
            >
              {activeRegime?.label || (typeof primaryRegime === 'string' ? primaryRegime.replace(/_/g, ' ') : 'Active Monsoon')}
            </span>
            <div className="text-[10px] font-mono text-[#64748b]">
              {regimeConfidence ? `${Math.round(regimeConfidence * 100)}% Confidence` : 'Synoptic Diagnosis'}
            </div>
          </div>
        </div>

        {/* Severe Outlook */}
        <div className="bg-[#121622] border border-[#1e2638] p-2 rounded">
          <div className="text-[10px] font-mono uppercase text-[#64748b] flex items-center gap-1">
            <AlertCircle className="w-3 h-3 text-[#f59e0b]" />
            Severe Outlook
          </div>
          <div className="mt-1">
            {activeWarning ? (
              <span
                className="text-xs font-bold px-1.5 py-0.5 rounded block text-center truncate uppercase"
                style={{
                  color: activeWarning.color,
                  backgroundColor: activeWarning.bgColor,
                  border: `1px solid ${activeWarning.borderColor}40`,
                }}
              >
                {activeWarning.label}
              </span>
            ) : (
              <span className="text-xs text-[#64748b] font-mono">—</span>
            )}
            <div className="text-[10px] font-mono text-[#64748b] text-center mt-0.5">
              {probabilities?.imd_category || 'IMD Criteria'}
            </div>
          </div>
        </div>
      </div>

      {/* Selected Post-Processed Rainfall 24h */}
      <div className="bg-[#121622] border border-[#1e2638] p-2.5 rounded space-y-1.5 text-xs">
        <div className="flex items-center justify-between text-[10px] font-mono uppercase text-[#64748b]">
          <span className="flex items-center gap-1 text-[#cbd5e1] font-semibold">
            <Sparkles className="w-3 h-3 text-[#00e5ff]" />
            {activeModelName}
          </span>
          <span className="font-mono text-[#94a3b8]">
            Raw: {formatNumber(rawVal, 1)} mm
          </span>
        </div>

        <div className="flex items-baseline justify-between pt-0.5">
          <div className="flex items-baseline gap-1.5">
            <span className="text-xl font-bold font-mono text-white">
              {formatNumber(activeModelMm, 1)} <span className="text-xs text-[#94a3b8]">mm/24h</span>
            </span>
            <span
              className={`font-mono text-xs font-semibold ${
                activeDeltaMm > 0 ? 'text-[#10b981]' : activeDeltaMm < 0 ? 'text-[#f59e0b]' : 'text-[#64748b]'
              }`}
            >
              {activeDeltaMm > 0 ? `+${formatNumber(activeDeltaMm, 1)}` : formatNumber(activeDeltaMm, 1)} mm Δ
            </span>
          </div>

          <div className="text-right">
            <span className="font-mono text-xs text-[#00e5ff] font-semibold block">
              {Math.round(heavyProb * 100)}% Heavy
            </span>
            <span className="font-mono text-[10px] text-[#f59e0b]">
              {Math.round(veryHeavyProb * 100)}% Very Heavy
            </span>
          </div>
        </div>
      </div>

      {/* Uncertainty Spread (P10 ─── P50 ─── P90) */}
      <div className="bg-[#121622] border border-[#1e2638] p-2.5 rounded space-y-1 text-xs">
        <div className="flex items-center justify-between text-[10px] font-mono text-[#64748b] uppercase">
          <span className="flex items-center gap-1">
            <Gauge className="w-3 h-3 text-[#ec4899]" />
            Uncertainty Distribution
          </span>
          <span className="text-[#ec4899] font-bold">
            Width: {formatNumber(uncertaintyWidth, 1)} mm
          </span>
        </div>

        {/* Graphical P10-P50-P90 Line */}
        <div className="pt-1 space-y-1">
          <div className="flex items-center justify-between text-[11px] font-mono text-white font-semibold">
            <span className="text-[#94a3b8]">P10: {formatNumber(p10Mm, 0)} mm</span>
            <span className="text-[#00e5ff] font-bold">P50: {formatNumber(p50Mm, 0)} mm</span>
            <span className="text-[#f59e0b]">P90: {formatNumber(p90Mm, 0)} mm</span>
          </div>
          <div className="relative w-full h-1.5 bg-[#1e2638] rounded-full overflow-hidden">
            <div
              className="absolute top-0 bottom-0 bg-gradient-to-r from-[#00e5ff] via-[#10b981] to-[#f59e0b] rounded-full"
              style={{ left: '15%', right: '15%' }}
            />
          </div>
        </div>
      </div>

      {/* Post-Processing Engine Attribution Context */}
      <div className="flex items-center justify-between text-[10px] text-[#64748b] pt-1 border-t border-[#1e2638]/60 font-mono">
        <span className="flex items-center gap-1">
          <CloudRain className="w-3 h-3 text-[#00e5ff]" />
          {isDemo ? 'NCMRWF-ALIGNED POST-PROCESSING (DEMO FALLBACK)' : 'NCMRWF-ALIGNED POST-PROCESSING'}
        </span>
        <span className="text-[#00e5ff] font-bold uppercase">
          {selectedModel.replace(/_/g, ' ')}
        </span>
      </div>
    </div>
  );
};
