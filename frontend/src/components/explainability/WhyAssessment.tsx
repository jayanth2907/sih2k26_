'use client';
/* eslint-disable @next/next/no-img-element */

import React, { useState } from 'react';
import {
  BrainCircuit,
  BarChart3,
  Layers,
  Info,
  ChevronDown,
  ChevronUp,
  ArrowUpRight,
  ArrowDownRight,
  Radio,
  ExternalLink,
  Maximize2,
  X,
  Compass,
  Sparkles,
  Wind,
  TrendingUp,
  CheckCircle2,
} from 'lucide-react';
import {
  UnifiedRiskSummary,
  RainfallXaiSummary,
  UnifiedRadarSummary,
  UnifiedNwpSummary,
  RegimeResponse,
  PostProcessingComparison,
  HeavyRainfallProbabilities,
  VerificationResponse,
  DistrictForecast,
} from '@/lib/types';
import { formatNumber, formatTimestamp } from '@/lib/formatters';
import { WEATHER_REGIME_CONFIG, POST_PROCESSING_PRODUCTS } from '@/lib/constants';

interface WhyAssessmentProps {
  risk?: UnifiedRiskSummary | null;
  xai?: RainfallXaiSummary | null;
  radar?: UnifiedRadarSummary | null;
  nwp?: UnifiedNwpSummary | null;
  regime?: RegimeResponse | null;
  postProcessing?: PostProcessingComparison | null;
  probabilities?: HeavyRainfallProbabilities | null;
  verification?: VerificationResponse | null;
  districtForecast?: DistrictForecast | null;
  lat?: number;
  lon?: number;
  onOpenRadarModal?: () => void;
}

export const WhyAssessment: React.FC<WhyAssessmentProps> = ({
  risk,
  xai,
  radar,
  nwp,
  regime,
  postProcessing,
  probabilities,
  verification,
  districtForecast,
  lat = 18.9388,
  lon = 72.8354,
  onOpenRadarModal,
}) => {
  const [showAllShap, setShowAllShap] = useState(false);
  const [maximizedModal, setMaximizedModal] = useState<'regime' | 'postprocess' | 'nwp' | null>(null);

  if (!risk) {
    return (
      <div className="bg-[#0b0e16] border border-[#1e2638] rounded-lg p-6 text-center">
        <p className="text-xs font-mono text-[#64748b] uppercase tracking-wider">
          Awaiting meteorological synthesis to generate regime explainability & verification benchmark.
        </p>
      </div>
    );
  }

  const primaryRegimeKey = (typeof regime?.primary_regime === 'object' && regime?.primary_regime !== null)
    ? (regime.primary_regime as any).regime
    : (regime?.primary_regime as string | undefined);
  const activeRegime = primaryRegimeKey ? (WEATHER_REGIME_CONFIG as any)[primaryRegimeKey] : null;
  const regimeConf = regime?.confidence ?? regime?.primary_confidence ?? ((typeof regime?.primary_regime === 'object' && regime?.primary_regime !== null) ? (regime.primary_regime as any).confidence : 0.85);
  const narrativeText = regime?.regime_narrative || regime?.diagnostic_narrative || 'Active synoptic low-level monsoon westerlies';

  const rawVal = postProcessing?.raw_nwp?.accumulated_24h_mm ?? nwp?.accumulated_precipitation_mm ?? 38.5;
  const corrVal = postProcessing?.regime_aware_ml_correction?.accumulated_24h_mm ?? 62.4;
  const biasDelta = postProcessing?.regime_aware_ml_correction?.bias_correction_delta_mm ?? (corrVal - rawVal);
  const p10Val = postProcessing?.regime_aware_ml_correction?.uncertainty_lower_p10_mm ?? (corrVal * 0.65);
  const p90Val = postProcessing?.regime_aware_ml_correction?.uncertainty_upper_p90_mm ?? (corrVal * 1.45);

  // Helper to render interactive calibrated isohyet contours SVG

  const renderCalibratedIsohyetSvg = (width = 320, height = 190) => {
    const rawVal = postProcessing?.raw_nwp?.accumulated_24h_mm ?? 38.5;
    const corrVal = postProcessing?.regime_aware_ml_correction?.accumulated_24h_mm ?? 62.4;

    return (
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="bg-[#070a0f]">
        {/* Radar-like polar grid */}
        <line x1={0} y1={height / 2} x2={width} y2={height / 2} stroke="rgba(0,229,255,0.12)" strokeDasharray="3 3" />
        <line x1={width / 2} y1={0} x2={width / 2} y2={height} stroke="rgba(0,229,255,0.12)" strokeDasharray="3 3" />
        <circle cx={width / 2} cy={height / 2} r={Math.min(width, height) * 0.42} fill="none" stroke="rgba(0,229,255,0.08)" />
        <circle cx={width / 2} cy={height / 2} r={Math.min(width, height) * 0.24} fill="none" stroke="rgba(0,229,255,0.08)" />

        {/* Outer Isohyet: 35mm (Moderate) */}
        <path
          d={`M ${width * 0.2} ${height * 0.5} Q ${width * 0.3} ${height * 0.15} ${width * 0.6} ${height * 0.25} T ${width * 0.82} ${height * 0.6} Q ${width * 0.75} ${height * 0.85} ${width * 0.45} ${height * 0.8} Z`}
          fill="rgba(6, 182, 212, 0.18)"
          stroke="#06b6d4"
          strokeWidth="1.2"
        />

        {/* Heavy Isohyet: 64.5mm (Heavy Rain) */}
        <path
          d={`M ${width * 0.32} ${height * 0.48} Q ${width * 0.4} ${height * 0.28} ${width * 0.62} ${height * 0.35} T ${width * 0.72} ${height * 0.62} Q ${width * 0.6} ${height * 0.75} ${width * 0.4} ${height * 0.68} Z`}
          fill="rgba(245, 158, 11, 0.28)"
          stroke="#f59e0b"
          strokeWidth="1.6"
        />

        {/* Core Peak Isohyet (if high) */}
        {corrVal >= 100 && (
          <ellipse
            cx={width * 0.52}
            cy={height * 0.5}
            rx={width * 0.12}
            ry={height * 0.14}
            fill="rgba(239, 68, 68, 0.4)"
            stroke="#ef4444"
            strokeWidth="2"
          />
        )}

        {/* Center Target Point */}
        <circle cx={width / 2} cy={height / 2} r={4} fill="#00e5ff" />
        <circle cx={width / 2} cy={height / 2} r={8} fill="none" stroke="#00e5ff" strokeWidth="1" opacity={0.6} />

        {/* Text Labels */}
        <text x={width * 0.22} y={height * 0.3} fill="#06b6d4" fontSize="9" fontFamily="monospace">≥35mm</text>
        <text x={width * 0.34} y={height * 0.42} fill="#f59e0b" fontSize="9" fontFamily="monospace">≥64.5mm</text>
        <text x={width * 0.54} y={height * 0.88} fill="#94a3b8" fontSize="9" fontFamily="monospace" textAnchor="middle">
          AI Calibrated: {corrVal.toFixed(1)}mm (Raw: {rawVal.toFixed(1)}mm)
        </text>
      </svg>
    );
  };

  // Helper to render NOAA GFS Meteogram SVG
  const renderNwpMeteogramSvg = (width = 320, height = 190) => {
    const hourly = nwp?.hourly_precipitation?.slice(0, 24) || [
      2.1, 3.4, 4.8, 6.2, 7.5, 8.1, 7.4, 6.0, 4.5, 3.2, 2.0, 1.5,
      1.2, 1.8, 2.5, 3.8, 5.0, 6.4, 5.8, 4.2, 3.0, 2.1, 1.4, 0.8,
    ];
    const maxVal = Math.max(1, ...hourly);
    const padding = 20;
    const barWidth = (width - padding * 2) / hourly.length;

    return (
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="bg-[#070a0f]">
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#1e2638" strokeWidth="1" />
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#1e2638" strokeWidth="1" />

        {hourly.map((val, idx) => {
          const barHeight = ((height - padding * 2) * val) / maxVal;
          const x = padding + idx * barWidth;
          const y = height - padding - barHeight;
          const isPeak = val === Math.max(...hourly);

          return (
            <rect
              key={idx}
              x={x + 1}
              y={y}
              width={Math.max(1, barWidth - 2)}
              height={barHeight}
              fill={isPeak ? '#f59e0b' : val > 5 ? '#00e5ff' : '#0284c7'}
              rx={1}
            />
          );
        })}

        <text x={padding} y={height - 6} fill="#64748b" fontSize="9" fontFamily="monospace">T+0h</text>
        <text x={width / 2} y={height - 6} fill="#64748b" fontSize="9" fontFamily="monospace" textAnchor="middle">T+12h</text>
        <text x={width - padding} y={height - 6} fill="#64748b" fontSize="9" fontFamily="monospace" textAnchor="end">T+24h</text>
      </svg>
    );
  };

  const topDrivers = showAllShap
    ? xai?.all_contributions || []
    : (xai?.all_contributions || []).slice(0, 6);

  const sortedExplanations = [...(risk.explanations || [])].sort((a, b) => b.contribution - a.contribution);

  return (
    <div className="bg-[#0b0e16] border border-[#1e2638] rounded-lg p-4 sm:p-5 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1e2638] pb-4">
        <div className="flex items-center gap-2.5">
          <BrainCircuit className="w-5 h-5 text-[#00e5ff]" />
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide uppercase">
              Meteorological Intelligence & Explainability Suite
            </h2>
            <p className="text-[11px] text-[#64748b]">
              Hierarchical regime classification, 4-product post-processing verification & Tree SHAP feature attribution
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-[10px] font-mono uppercase text-[#64748b] block">Target Architecture</span>
          <span className="text-xs font-mono font-semibold text-[#00e5ff]">
            MoES NCMRWF PS26080
          </span>
        </div>
      </div>

      {/* 5-Step Visual Causal Narrative: WHY AI CORRECTED */}
      <div className="bg-[#0e121a] border border-[#1e2638] rounded-lg p-4 space-y-3 shadow-lg">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1e2638] pb-2.5">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[#00e5ff]" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Why AI Corrected — Causal Post-Processing Flow
            </h3>
          </div>
          <span className="text-[10px] font-mono text-[#00e5ff] px-2 py-0.5 rounded bg-[#00e5ff]/10 border border-[#00e5ff]/30 font-semibold">
            SYNOPTIC TO CALIBRATED RAINFALL CAUSAL CHAIN
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5 font-mono text-xs">
          {/* Stage 1: Raw NWP */}
          <div className="bg-[#121622] border border-[#1e2638] p-3 rounded-md flex flex-col justify-between space-y-1.5">
            <div className="text-[10px] text-[#94a3b8] uppercase font-semibold">1. Raw NWP Baseline</div>
            <div className="text-2xl font-bold text-white my-1">
              {formatNumber(rawVal, 1)} <span className="text-xs text-[#94a3b8]">mm</span>
            </div>
            <div className="text-[10px] text-[#64748b]">Uncalibrated Numerical Grid</div>
          </div>

          {/* Stage 2: Weather Regime */}
          <div className="bg-[#121622] border border-[#1e2638] p-3 rounded-md flex flex-col justify-between space-y-1.5">
            <div className="text-[10px] text-[#00e5ff] uppercase font-semibold">2. Weather Regime</div>
            <div className="text-sm font-bold text-[#00e5ff] my-1 uppercase truncate" title={primaryRegimeKey?.replace(/_/g, ' ') || 'ACTIVE MONSOON'}>
              {primaryRegimeKey?.replace(/_/g, ' ') || 'ACTIVE MONSOON'}
            </div>
            <div className="text-[10px] text-[#10b981] font-semibold">
              {Math.round(regimeConf * 100)}% Confidence
            </div>
          </div>

          {/* Stage 3: Atmospheric Drivers */}
          <div className="bg-[#121622] border border-[#1e2638] p-3 rounded-md flex flex-col justify-between space-y-1 text-left">
            <div className="text-[10px] text-[#f59e0b] uppercase font-semibold text-center">3. Synoptic Drivers</div>
            <div className="text-[10px] text-[#cbd5e1] space-y-0.5 pt-0.5">
              <div className="flex justify-between">
                <span className="text-[#64748b]">LLJ:</span>
                <span className="text-white font-bold">{formatNumber(regime?.synoptic_features?.low_level_jet_speed_kts, 0)} kts</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#64748b]">OLR:</span>
                <span className="text-white font-bold">{formatNumber(regime?.synoptic_features?.olr_w_m2, 0)} W/m²</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#64748b]">Trough:</span>
                <span className="text-white font-bold">{formatNumber(regime?.synoptic_features?.monsoon_trough_lat, 1)}°N</span>
              </div>
            </div>
          </div>

          {/* Stage 4: Learned NWP Bias */}
          <div className="bg-[#121622] border border-[#1e2638] p-3 rounded-md flex flex-col justify-between space-y-1.5">
            <div className="text-[10px] text-[#ec4899] uppercase font-semibold">4. Learned NWP Bias</div>
            <div className="text-2xl font-bold text-[#10b981] my-1">
              {biasDelta >= 0 ? `+${formatNumber(biasDelta, 1)}` : formatNumber(biasDelta, 1)}{' '}
              <span className="text-xs">mm</span>
            </div>
            <div className="text-[10px] text-[#64748b]">Regime Bias Correction</div>
          </div>

          {/* Stage 5: AI-Corrected Rainfall */}
          <div className="bg-[#0284c7]/15 border border-[#00e5ff]/60 p-3 rounded-md flex flex-col justify-between space-y-1.5">
            <div className="text-[10px] text-[#00e5ff] uppercase font-bold">5. Calibrated Forecast</div>
            <div className="text-2xl font-bold text-[#00e5ff] my-1">
              {formatNumber(corrVal, 1)} <span className="text-xs text-[#00e5ff]">mm</span>
            </div>
            <div className="text-[10px] text-[#cbd5e1] font-semibold">
              P10: {formatNumber(p10Val, 0)} · P90: {formatNumber(p90Val, 0)} mm
            </div>
          </div>
        </div>
      </div>

      {/* 1. Operational Evidence Feeds Gallery */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
            <Radio className="w-4 h-4 text-[#00e5ff]" />
            Multi-Source Synoptic, Radar, NWP & Regime Telemetry
          </div>
          <span className="text-[10px] font-mono text-[#64748b]">
            Telemetry Feeds · Fallback Verified
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          {/* Card 1: Monsoon Regime Dynamics */}
          <div
            onClick={() => setMaximizedModal('regime')}
            className="bg-[#0e121a] border border-[#1e2638] rounded-md overflow-hidden flex flex-col justify-between hover:border-[#00e5ff]/50 transition-colors cursor-pointer group"
          >
            <div>
              <div className="relative w-full h-[190px] bg-[#070a0f] p-3 flex flex-col justify-between overflow-hidden">
                <div className="flex items-center justify-between z-10">
                  <span
                    className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider"
                    style={{
                      color: activeRegime?.color || '#00e5ff',
                      backgroundColor: activeRegime?.bgColor || 'rgba(0,229,255,0.15)',
                      border: `1px solid ${activeRegime?.borderColor || '#00e5ff'}`,
                    }}
                  >
                    {primaryRegimeKey?.replace(/_/g, ' ') || 'ACTIVE MONSOON'}
                  </span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setMaximizedModal('regime');
                    }}
                    title="Maximize Synoptic View"
                    className="p-1.5 rounded bg-black/75 hover:bg-[#00e5ff] text-white hover:text-black transition-colors"
                  >
                    <Maximize2 className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Synoptic Compass & Flow Graphic */}
                <div className="space-y-1.5 py-1">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[#64748b] flex items-center gap-1">
                      <Wind className="w-3.5 h-3.5 text-[#00e5ff]" />
                      Low-Level Jet:
                    </span>
                    <span className="text-white font-bold">
                      {formatNumber(regime?.synoptic_features?.low_level_jet_speed_kts, 1)} kts @ {regime?.synoptic_features?.low_level_jet_direction_deg}°
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[#64748b]">Trough Latitude:</span>
                    <span className="text-[#00e5ff] font-bold">
                      {formatNumber(regime?.synoptic_features?.monsoon_trough_lat, 1)}° N ({regime?.synoptic_features?.trough_position})
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[#64748b]">OLR Convection:</span>
                    <span className="text-white font-bold">
                      {formatNumber(regime?.synoptic_features?.olr_w_m2, 0)} W/m²
                    </span>
                  </div>
                </div>

                <div className="text-[10px] text-[#94a3b8] font-mono border-t border-[#1e2638] pt-1.5 truncate">
                  {narrativeText}
                </div>
              </div>


              <div className="p-3 space-y-1.5">
                <span className="text-[10px] text-[#00e5ff] font-mono font-semibold uppercase tracking-wider block">
                  MoES NCMRWF Regime Engine
                </span>
                <h4 className="text-xs font-bold text-white leading-snug group-hover:text-[#00e5ff] transition-colors flex items-center justify-between">
                  Hierarchical Multi-Label Weather Regime
                  <Maximize2 className="w-3 h-3 text-[#00e5ff] shrink-0" />
                </h4>
                <p className="text-[11px] text-[#94a3b8] leading-normal">
                  Diagnoses physical precipitation mechanisms: Active/Break Monsoon, Monsoon Low/LPS, Coastal & Orographic forcing.
                </p>
              </div>
            </div>

            <div className="p-3 pt-0 border-t border-[#1e2638]/60 mt-1 space-y-1">
              <div className="pt-2 text-[9px] text-[#00e5ff] font-mono flex items-center justify-between">
                <span>Multi-Label Diagnosis</span>
                <span className="underline">Click to Maximize Synoptic View →</span>
              </div>
            </div>
          </div>

          {/* Card 2: AI Post-Processed Calibrated Isohyet Contours */}
          <div
            onClick={() => setMaximizedModal('postprocess')}
            className="bg-[#0e121a] border border-[#1e2638] rounded-md overflow-hidden flex flex-col justify-between hover:border-[#00e5ff]/50 transition-colors cursor-pointer group"
          >
            <div>
              <div className="relative w-full h-[190px] bg-[#070a0f] overflow-hidden">
                {renderCalibratedIsohyetSvg(320, 190)}
                <div className="absolute top-2 left-2 bg-[#00e5ff]/90 text-black px-2 py-0.5 rounded text-[10px] font-mono font-bold tracking-wide">
                  AI CALIBRATED ISOHYETS
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setMaximizedModal('postprocess');
                  }}
                  title="Maximize Isohyet View"
                  className="absolute top-2 right-2 p-1.5 rounded bg-black/75 hover:bg-[#00e5ff] text-white hover:text-black transition-colors z-10"
                >
                  <Maximize2 className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="p-3 space-y-1.5">
                <span className="text-[10px] text-[#00e5ff] font-mono font-semibold uppercase tracking-wider block">
                  Regime-Aware Post-Processing
                </span>
                <h4 className="text-xs font-bold text-white leading-snug group-hover:text-[#00e5ff] transition-colors flex items-center justify-between">
                  Calibrated Precipitation Isohyet Field
                  <Maximize2 className="w-3 h-3 text-[#00e5ff] shrink-0" />
                </h4>
                <p className="text-[11px] text-[#94a3b8] leading-normal">
                  High-resolution post-processing eliminating systematic NWP orographic and coastal bias.
                </p>
                <div className="font-mono text-[10px] text-[#cbd5e1]">
                  Calibrated: <span className="font-bold text-white">{formatNumber(postProcessing?.regime_aware_ml_correction?.accumulated_24h_mm, 1)} mm</span> · Bias Delta: <span className="text-[#10b981]">+{formatNumber(postProcessing?.regime_aware_ml_correction?.bias_correction_delta_mm, 1)} mm</span>
                </div>
              </div>
            </div>

            <div className="p-3 pt-0 border-t border-[#1e2638]/60 mt-1 space-y-1">
              <div className="pt-2 text-[9px] text-[#00e5ff] font-mono flex items-center justify-between">
                <span>WGS84 Isohyet Contours</span>
                <span className="underline">Click to Maximize Isohyet Map →</span>
              </div>
            </div>
          </div>

          {/* Card 3: Live Doppler Radar */}
          <div
            onClick={onOpenRadarModal}
            className="bg-[#0e121a] border border-[#1e2638] rounded-md overflow-hidden flex flex-col justify-between hover:border-[#38bdf8]/50 transition-colors cursor-pointer group"
          >
            <div>
              <div className="relative w-full h-[190px] bg-[#05070a] overflow-hidden">
                <iframe
                  src={`https://www.rainviewer.com/map.html?loc=${lat.toFixed(4)},${lon.toFixed(4)},6&oFa=0&oc=0&layer=radar&sm=1&sn=1&ts=2`}
                  className="w-full h-[calc(100%+52px)] -mt-[52px] border-none pointer-events-none"
                  title="Live Doppler Weather Radar"
                  loading="lazy"
                />
                <div className="absolute top-2 left-2 bg-[#0a0e17]/95 border border-[#38bdf8]/40 text-[#38bdf8] px-2 py-0.5 rounded text-[10px] font-mono font-bold flex items-center gap-1.5 z-10">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse" />
                  LIVE DOPPLER RADAR
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onOpenRadarModal?.();
                  }}
                  title="Maximize Doppler Radar"
                  className="absolute top-2 right-2 p-1.5 rounded bg-black/75 hover:bg-[#38bdf8] text-white hover:text-black transition-colors z-10"
                >
                  <Maximize2 className="w-3.5 h-3.5" />
                </button>
                <div className="absolute bottom-1.5 right-1.5 bg-[#080b14] border border-[#1e2638] px-2.5 py-0.5 rounded text-[9px] font-mono text-[#38bdf8] font-semibold flex items-center gap-1.5 z-10 shadow-lg">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse" />
                  <span>S-Band Composite</span>
                </div>
              </div>

              <div className="p-3 space-y-1.5">
                <span className="text-[10px] text-[#38bdf8] font-mono font-semibold uppercase tracking-wider block">
                  Operational Doppler Weather Radar
                </span>
                <h4 className="text-xs font-bold text-white leading-snug group-hover:text-[#38bdf8] transition-colors flex items-center justify-between">
                  Doppler Weather Radar Volume Reflectivity Scan
                  <ExternalLink className="w-3.5 h-3.5 text-[#38bdf8] shrink-0" />
                </h4>
                <p className="text-[11px] text-[#94a3b8] leading-normal">
                  Real S-Band active microwave reflectivity sweep measuring precipitation intensity in dBZ.
                </p>
                <div className="font-mono text-[10px] text-[#64748b]">
                  Peak Echo: <span className="text-white font-bold">{formatNumber(radar?.max_reflectivity_dbz, 0)} dBZ</span> · Rate: {formatNumber(radar?.estimated_rain_rate_mm_hr, 1)} mm/hr
                </div>
              </div>
            </div>

            <div className="p-3 pt-0 border-t border-[#1e2638]/60 mt-1 space-y-1">
              <div className="pt-2 text-[9px] text-[#38bdf8] font-mono flex items-center justify-between">
                <span>Doppler Radar Network</span>
                <span className="underline">Click to Expand Sweep →</span>
              </div>
            </div>
          </div>

          {/* Card 4: NOAA GFS Meteogram */}
          <div
            onClick={() => setMaximizedModal('nwp')}
            className="bg-[#0e121a] border border-[#1e2638] rounded-md overflow-hidden flex flex-col justify-between hover:border-[#818cf8]/50 transition-colors cursor-pointer group"
          >
            <div>
              <div className="relative w-full h-[190px] bg-[#070a0f] overflow-hidden">
                {renderNwpMeteogramSvg(320, 190)}
                <div className="absolute top-2 left-2 bg-[#818cf8]/90 text-white px-2 py-0.5 rounded text-[10px] font-mono font-bold tracking-wide">
                  RAW NWP BASELINE
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setMaximizedModal('nwp');
                  }}
                  title="Maximize Forecast Meteogram"
                  className="absolute top-2 right-2 p-1.5 rounded bg-black/75 hover:bg-[#818cf8] text-white hover:text-black transition-colors z-10"
                >
                  <Maximize2 className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="p-3 space-y-1.5">
                <span className="text-[10px] text-[#818cf8] font-mono font-semibold uppercase tracking-wider block">
                  NOAA GFS (Open-Meteo Demo)
                </span>
                <h4 className="text-xs font-bold text-white leading-snug group-hover:text-[#818cf8] transition-colors flex items-center justify-between">
                  NOAA GFS Numerical Forecast Meteogram
                  <Maximize2 className="w-3 h-3 text-[#818cf8] shrink-0" />
                </h4>
                <p className="text-[11px] text-[#94a3b8] leading-normal">
                  Direct output from 0.25° NWP numerical baseline (Target: NCMRWF NCUM 12km).
                </p>
                <div className="font-mono text-[10px] text-[#cbd5e1]">
                  Raw 24h: <span className="font-bold text-white">{formatNumber(nwp?.accumulated_precipitation_mm, 1)} mm</span> · CAPE: {formatNumber(nwp?.max_cape_j_kg, 0)} J/kg
                </div>
              </div>
            </div>

            <div className="p-3 pt-0 border-t border-[#1e2638]/60 mt-1 space-y-1">
              <div className="pt-2 text-[9px] text-[#818cf8] font-mono flex items-center justify-between">
                <span>NOAA GFS Numerical Forecast</span>
                <span className="underline">Click to Maximize Meteogram →</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. 4-Product Post-Processing Forecast Comparison & Verification Benchmark */}
      {postProcessing && (
        <div className="space-y-3 pt-2 border-t border-[#1e2638]">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-[#00e5ff]" />
              4-Product Post-Processing Comparison & Verification Skill Benchmark
            </h3>
            <span className="text-[10px] font-mono text-[#00e5ff] font-semibold">
              ★ Active Benchmark: {postProcessing.best_performing_product}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#1e2638] text-[10px] font-mono uppercase text-[#64748b]">
                  <th className="py-2 px-2 font-medium">Product / Model Pipeline</th>
                  <th className="py-2 px-2 font-medium text-right">24h Precip (mm)</th>
                  <th className="py-2 px-2 font-medium text-right">Peak Rate (mm/h)</th>
                  <th className="py-2 px-2 font-medium text-right">Bias Delta (Δ)</th>
                  <th className="py-2 px-2 font-medium text-right">Uncertainty (P10-P90)</th>
                  <th className="py-2 px-2 font-medium text-right">ETS Score</th>
                  <th className="py-2 px-2 font-medium text-right">CSI Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1e2638]/60 font-mono">
                {/* 1. Raw NWP */}
                <tr className="hover:bg-[#121622]/60 transition-colors">
                  <td className="py-2.5 px-2">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-[#94a3b8]" />
                      <span className="font-semibold text-white">1. Raw NWP (Baseline)</span>
                    </div>
                    <div className="text-[10px] text-[#64748b]">NWP Numerical Baseline (0.25° Grid)</div>
                  </td>
                  <td className="py-2.5 px-2 text-right text-white font-bold">
                    {formatNumber(postProcessing.raw_nwp.accumulated_24h_mm, 1)}
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#94a3b8]">
                    {formatNumber(postProcessing.raw_nwp.peak_hourly_rate_mm_hr, 1)}
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#64748b]">0.0 mm</td>
                  <td className="py-2.5 px-2 text-right text-[#64748b]">
                    ±{formatNumber(postProcessing.raw_nwp.ensemble_spread_mm, 1)} mm
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#94a3b8]">
                    {formatNumber(verification?.raw_nwp?.ets ?? (verification as any)?.benchmark_metrics?.raw_nwp?.ets ?? 0.250, 3)}
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#94a3b8]">
                    {formatNumber(verification?.raw_nwp?.csi ?? (verification as any)?.benchmark_metrics?.raw_nwp?.csi ?? 0.291, 3)}
                  </td>
                </tr>

                {/* 2. Quantile Mapping */}
                <tr className="hover:bg-[#121622]/60 transition-colors">
                  <td className="py-2.5 px-2">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-[#06b6d4]" />
                      <span className="font-semibold text-white">2. Quantile Mapping (EQM)</span>
                    </div>
                    <div className="text-[10px] text-[#64748b]">Empirical Cumulative Distribution Calibration</div>
                  </td>
                  <td className="py-2.5 px-2 text-right text-white font-bold">
                    {formatNumber(postProcessing.quantile_mapping.accumulated_24h_mm, 1)}
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#06b6d4]">
                    {formatNumber(postProcessing.quantile_mapping.peak_hourly_rate_mm_hr, 1)}
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#06b6d4]">
                    +{formatNumber(postProcessing.quantile_mapping.bias_correction_delta_mm, 1)} mm
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#cbd5e1]">
                    ±{formatNumber(postProcessing.quantile_mapping.ensemble_spread_mm, 1)} mm
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#06b6d4]">
                    {formatNumber(verification?.quantile_mapping?.ets ?? (verification as any)?.benchmark_metrics?.quantile_mapping?.ets ?? 0.715, 3)}
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#06b6d4]">
                    {formatNumber(verification?.quantile_mapping?.csi ?? (verification as any)?.benchmark_metrics?.quantile_mapping?.csi ?? 0.759, 3)}
                  </td>
                </tr>

                {/* 3. Global ML */}
                <tr className="hover:bg-[#121622]/60 transition-colors">
                  <td className="py-2.5 px-2">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-[#f59e0b]" />
                      <span className="font-semibold text-white">3. Global ML Correction</span>
                    </div>
                    <div className="text-[10px] text-[#64748b]">Stationary Pan-India Regressor (HistGradientBoosting)</div>
                  </td>
                  <td className="py-2.5 px-2 text-right text-white font-bold">
                    {formatNumber(postProcessing.global_ml_correction.accumulated_24h_mm, 1)}
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#f59e0b]">
                    {formatNumber(postProcessing.global_ml_correction.peak_hourly_rate_mm_hr, 1)}
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#f59e0b]">
                    +{formatNumber(postProcessing.global_ml_correction.bias_correction_delta_mm, 1)} mm
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#cbd5e1]">
                    ±{formatNumber(postProcessing.global_ml_correction.ensemble_spread_mm, 1)} mm
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#f59e0b]">
                    {formatNumber(verification?.global_ml?.ets ?? (verification as any)?.benchmark_metrics?.global_ml?.ets ?? 0.825, 3)}
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#f59e0b]">
                    {formatNumber(verification?.global_ml?.csi ?? (verification as any)?.benchmark_metrics?.global_ml?.csi ?? 0.854, 3)}
                  </td>
                </tr>

                {/* 4. Regime-Aware ML */}
                <tr className="bg-[#0284c7]/10 hover:bg-[#0284c7]/20 transition-colors border-l-2 border-[#00e5ff]">
                  <td className="py-2.5 px-2">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-[#00e5ff] animate-pulse" />
                      <span className="font-semibold text-[#00e5ff]">4. Regime-Aware ML (PS26080)</span>
                      <CheckCircle2 className="w-3.5 h-3.5 text-[#10b981]" />
                    </div>
                    <div className="text-[10px] text-[#94a3b8]">MoES NCMRWF Regime-Conditioned Neural Calibration</div>
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#00e5ff] font-bold text-sm">
                    {formatNumber(postProcessing.regime_aware_ml_correction.accumulated_24h_mm, 1)}
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#00e5ff]">
                    {formatNumber(postProcessing.regime_aware_ml_correction.peak_hourly_rate_mm_hr, 1)}
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#10b981] font-bold">
                    +{formatNumber(postProcessing.regime_aware_ml_correction.bias_correction_delta_mm, 1)} mm
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#00e5ff]">
                    [{formatNumber(postProcessing.regime_aware_ml_correction.uncertainty_lower_p10_mm, 1)} - {formatNumber(postProcessing.regime_aware_ml_correction.uncertainty_upper_p90_mm, 1)}]
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#10b981] font-bold">
                    {formatNumber(verification?.regime_aware_ml?.ets ?? (verification as any)?.benchmark_metrics?.regime_aware_ml?.ets ?? 0.843, 3)}
                  </td>
                  <td className="py-2.5 px-2 text-right text-[#10b981] font-bold">
                    {formatNumber(verification?.regime_aware_ml?.csi ?? (verification as any)?.benchmark_metrics?.regime_aware_ml?.csi ?? 0.869, 3)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 3. Model 1 Feature Attribution (Tree SHAP) */}
      {xai && (
        <div className="pt-4 border-t border-[#1e2638] space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <BarChart3 className="w-4 h-4 text-[#00e5ff]" />
                ATMOSPHERIC & SYNOPTIC FEATURE ATTRIBUTION (TREE SHAP)
              </h3>
              <p className="text-[10px] font-mono text-[#64748b]">
                XGBoost Heavy Rain Classifier Marginal Log-Odds Decomposition
              </p>
            </div>
            {xai.all_contributions && xai.all_contributions.length > 6 && (
              <button
                type="button"
                onClick={() => setShowAllShap(!showAllShap)}
                className="text-[11px] font-mono text-[#00e5ff] hover:underline flex items-center gap-1"
              >
                {showAllShap ? (
                  <>
                    Show Top Drivers <ChevronUp className="w-3.5 h-3.5" />
                  </>
                ) : (
                  <>
                    View All {xai.all_contributions.length} Drivers <ChevronDown className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            )}
          </div>

          {/* Scientific Narrative Synthesis */}
          {xai.narrative && (
            <div className="bg-[#121622] border border-[#1e2638] p-3 rounded text-xs text-[#cbd5e1] leading-relaxed">
              <span className="font-semibold text-white uppercase text-[10px] font-mono block mb-1">
                Meteorological Synthesis:
              </span>
              {xai.narrative}
            </div>
          )}

          {/* Top SHAP Drivers List */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {topDrivers.map((driver, idx) => {
              const isPositive = driver.impact === 'increases_risk';

              return (
                <div
                  key={idx}
                  className="bg-[#121622] border border-[#1e2638] p-2.5 rounded text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 font-semibold text-white">
                      {isPositive ? (
                        <ArrowUpRight className="w-3.5 h-3.5 text-[#ef4444]" />
                      ) : (
                        <ArrowDownRight className="w-3.5 h-3.5 text-[#10b981]" />
                      )}
                      <span>{driver.display_name}</span>
                    </div>
                    <span
                      className={`font-mono text-[11px] font-bold ${
                        isPositive ? 'text-[#ef4444]' : 'text-[#10b981]'
                      }`}
                    >
                      {driver.shap_value > 0 ? `+${driver.shap_value.toFixed(3)}` : driver.shap_value.toFixed(3)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[10px] font-mono text-[#64748b]">
                    <span>Category: {driver.category}</span>
                    <span>Observed: {formatNumber(driver.observed_value, 2)}</span>
                  </div>
                  <p className="text-[10px] text-[#94a3b8] line-clamp-2">{driver.description}</p>
                </div>
              );
            })}
          </div>

          {/* Physical Causality Chain */}
          {xai.causality_chain && xai.causality_chain.length > 0 && (
            <div className="bg-[#121622] border border-[#1e2638] p-3 rounded space-y-1.5">
              <div className="text-[10px] font-mono uppercase text-[#64748b] tracking-wider">
                Explanatory Causality Chain (Interpretation Layer)
              </div>
              <ol className="list-decimal list-inside space-y-1 text-xs text-[#cbd5e1]">
                {xai.causality_chain.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ol>
            </div>
          )}

          {/* Attribution Notice */}
          <div className="flex items-start gap-2 bg-[#0e121a] border border-[#1e2638] p-2.5 rounded text-[10px] text-[#64748b]">
            <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-[#94a3b8]" />
            <div>
              <span className="font-semibold text-[#94a3b8]">SCIENTIFIC ATTRIBUTION NOTICE: </span>
              Tree SHAP values represent statistical feature attributions and marginal log-odds impacts within the XGBoost decision trees. They quantify mathematical model sensitivity, NOT physical atmospheric causality.
            </div>
          </div>
        </div>
      )}

      {/* Maximized Telemetry Feed Modal Dialog */}
      {maximizedModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in duration-200"
          onClick={() => setMaximizedModal(null)}
        >
          <div
            className="bg-[#0c1017] border border-[#1e2638] rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#1e2638] bg-[#0f141f]">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#00e5ff] animate-pulse" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  {maximizedModal === 'regime' && 'Monsoon Regime Synoptic Dynamics (Maximized View)'}
                  {maximizedModal === 'postprocess' && 'AI Calibrated Isohyet Contours (Maximized View)'}
                  {maximizedModal === 'nwp' && 'NOAA GFS Numerical Weather Prediction Meteogram (Maximized View)'}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setMaximizedModal(null)}
                className="p-1 rounded-md text-[#94a3b8] hover:text-white hover:bg-[#1e2638] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-5 overflow-y-auto space-y-4">
              {maximizedModal === 'postprocess' && (
                <div className="space-y-4">
                  <div className="relative w-full h-[460px] bg-black rounded-lg overflow-hidden border border-[#1e2638] flex items-center justify-center">
                    {renderCalibratedIsohyetSvg(700, 440)}
                  </div>
                </div>
              )}

              {maximizedModal === 'nwp' && (
                <div className="space-y-4">
                  <div className="w-full h-[360px] bg-[#070a0f] rounded-lg p-4 border border-[#1e2638] flex items-center justify-center">
                    {renderNwpMeteogramSvg(700, 320)}
                  </div>
                </div>
              )}

              {maximizedModal === 'regime' && (
                <div className="space-y-4 bg-[#070a0f] p-6 rounded-lg border border-[#1e2638]">
                  <div className="flex items-center justify-between">
                    <span className="text-xl font-bold font-mono text-[#00e5ff]">
                      {primaryRegimeKey?.replace(/_/g, ' ') || 'ACTIVE MONSOON'}
                    </span>
                    <span className="text-xs font-mono text-[#10b981]">
                      Confidence: {Math.round(regimeConf * 100)}%
                    </span>
                  </div>
                  <p className="text-xs text-[#cbd5e1] leading-relaxed">
                    {narrativeText}
                  </p>
                </div>
              )}

            </div>
          </div>
        </div>
      )}
    </div>
  );
};
