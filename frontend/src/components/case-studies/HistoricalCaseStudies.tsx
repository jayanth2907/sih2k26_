'use client';

import React, { useState, useEffect } from 'react';
import {
  History,
  Calendar,
  MapPin,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  Layers,
  Sparkles,
  Compass,
  X,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
  Info,
  Activity,
  CheckCircle2,
  HelpCircle,
} from 'lucide-react';
import {
  CaseStudyDetail,
  CaseStudyStatus,
  CaseStudySummary,
  TrainingOverlapStatus,
} from '@/lib/types';
import { fetchCaseStudies, fetchCaseStudyDetail } from '@/lib/api';
import { formatNumber } from '@/lib/formatters';

interface HistoricalCaseStudiesProps {
  onFocusLocation?: (lat: number, lon: number, name: string) => void;
}

export const HistoricalCaseStudies: React.FC<HistoricalCaseStudiesProps> = ({
  onFocusLocation,
}) => {
  const [caseList, setCaseList] = useState<CaseStudySummary[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<CaseStudyDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Initial load of case study catalog
  useEffect(() => {
    fetchCaseStudies()
      .then((data) => {
        if (Array.isArray(data)) setCaseList(data);
      })
      .catch((err) => {
        console.warn('[MEGHANETRA] Fallback loading for case studies:', err);
      });
  }, []);

  // Fetch detailed case study profile on selection
  const handleSelectCase = async (caseId: string) => {
    setSelectedCaseId(caseId);
    setIsLoadingDetail(true);
    setError(null);

    try {
      const detail = await fetchCaseStudyDetail(caseId);
      setSelectedDetail(detail);
    } catch (err) {
      console.error('[MEGHANETRA] Failed fetching case study detail:', err);
      setError('Could not load detailed historical case study.');
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const getStatusBadge = (status: CaseStudyStatus) => {
    switch (status) {
      case 'AVAILABLE':
        return {
          label: 'AVAILABLE',
          color: '#10b981',
          bg: 'rgba(16, 185, 129, 0.12)',
          border: 'rgba(16, 185, 129, 0.4)',
        };
      case 'PARTIALLY_AVAILABLE':
        return {
          label: 'PARTIALLY AVAILABLE',
          color: '#f59e0b',
          bg: 'rgba(245, 158, 11, 0.12)',
          border: 'rgba(245, 158, 11, 0.4)',
        };
      default:
        return {
          label: 'NOT AVAILABLE',
          color: '#ef4444',
          bg: 'rgba(239, 68, 68, 0.12)',
          border: 'rgba(239, 68, 68, 0.4)',
        };
    }
  };

  const getOverlapBadge = (overlap: TrainingOverlapStatus) => {
    switch (overlap) {
      case 'TRUE':
        return {
          label: 'TRAINING OVERLAP: TRUE (2018–2022 Split)',
          color: '#f59e0b',
          bg: 'rgba(245, 158, 11, 0.1)',
        };
      case 'FALSE':
        return {
          label: 'TRAINING OVERLAP: FALSE (External / Val)',
          color: '#10b981',
          bg: 'rgba(16, 185, 129, 0.1)',
        };
      default:
        return {
          label: 'TRAINING OVERLAP: UNKNOWN',
          color: '#94a3b8',
          bg: 'rgba(148, 163, 184, 0.1)',
        };
    }
  };

  return (
    <div className="bg-[#0b0e16] border border-[#1e2638] rounded-lg p-4 shadow-xl space-y-4">
      {/* Header & Isolation Statement */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1e2638] pb-3">
        <div className="flex items-center gap-2.5">
          <History className="w-5 h-5 text-[#00e5ff]" />
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              Historical Extreme-Event Case Studies
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1e2638] text-[#94a3b8]">
                Supplementary Analysis
              </span>
            </h3>
            <p className="text-[11px] text-[#64748b] font-mono mt-0.5">
              RETROSPECTIVE VERIFICATION · STRICT DATA LEAKAGE ISOLATION · NOT PART OF 2024–2025 PRIMARY TEST BENCHMARK
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 bg-[#121622] border border-[#1e2638] px-2.5 py-1 rounded text-[10px] font-mono text-[#94a3b8]">
          <Info className="w-3.5 h-3.5 text-[#00e5ff]" />
          <span>3 Historical Benchmark Events Registered</span>
        </div>
      </div>

      {/* 3 Event Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {caseList.map((cs) => {
          const statusBadge = getStatusBadge(cs.status);
          const overlapBadge = getOverlapBadge(cs.training_overlap);

          return (
            <div
              key={cs.case_id}
              onClick={() => handleSelectCase(cs.case_id)}
              className="bg-[#121622] border border-[#1e2638] hover:border-[#00e5ff]/50 rounded-lg p-3.5 space-y-2.5 cursor-pointer transition-all hover:bg-[#151d2d] group flex flex-col justify-between"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <span
                    className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded uppercase"
                    style={{
                      color: statusBadge.color,
                      backgroundColor: statusBadge.bg,
                      border: `1px solid ${statusBadge.border}`,
                    }}
                  >
                    {statusBadge.label}
                  </span>
                  <span className="text-[11px] font-mono text-[#00e5ff] font-bold">
                    {cs.event_year}
                  </span>
                </div>

                <h4 className="text-sm font-bold text-white group-hover:text-[#00e5ff] transition-colors leading-tight">
                  {cs.title}
                </h4>
                <p className="text-[11px] text-[#94a3b8] line-clamp-2 leading-relaxed">
                  {cs.subtitle}
                </p>
              </div>

              <div className="pt-2 border-t border-[#1e2638]/70 space-y-1.5 font-mono text-[10px]">
                <div className="flex items-center justify-between text-[#cbd5e1]">
                  <span className="flex items-center gap-1 text-[#64748b]">
                    <MapPin className="w-3 h-3 text-[#00e5ff]" />
                    Region:
                  </span>
                  <span className="truncate max-w-[140px] text-white">
                    {cs.spatial_domain.region_name}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[#cbd5e1]">
                  <span className="text-[#64748b]">Peak Obs:</span>
                  <span className="font-bold text-white">
                    {cs.peak_observation_mm != null ? `${cs.peak_observation_mm.toFixed(1)} mm/24h` : 'N/A'}
                  </span>
                </div>


                <div
                  className="px-1.5 py-0.5 rounded text-[9px] truncate"
                  style={{ color: overlapBadge.color, backgroundColor: overlapBadge.bg }}
                >
                  {overlapBadge.label}
                </div>

                <div className="flex items-center justify-between text-[#00e5ff] pt-1 font-semibold">
                  <span>Inspect Event Telemetry</span>
                  <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Case Study Detail Modal / Slide-over */}
      {selectedCaseId && selectedDetail && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0b0e16] border border-[#00e5ff]/50 rounded-lg max-w-3xl w-full p-5 shadow-2xl space-y-4 max-h-[92vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-[#1e2638] pb-3">
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-base font-bold text-white uppercase tracking-wider">
                    {selectedDetail.title}
                  </h3>
                  <span
                    className="text-[10px] font-mono font-bold px-2 py-0.5 rounded"
                    style={{
                      color: getStatusBadge(selectedDetail.status).color,
                      backgroundColor: getStatusBadge(selectedDetail.status).bg,
                      border: `1px solid ${getStatusBadge(selectedDetail.status).border}`,
                    }}
                  >
                    {getStatusBadge(selectedDetail.status).label}
                  </span>
                </div>
                <p className="text-xs text-[#94a3b8] font-mono">
                  {selectedDetail.subtitle}
                </p>
              </div>

              <button
                type="button"
                onClick={() => {
                  setSelectedCaseId(null);
                  setSelectedDetail(null);
                }}
                className="p-1 rounded text-[#94a3b8] hover:text-white hover:bg-[#1e2638] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Mandatory Disclaimers & Leakage Notice */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[10px] font-mono">
              <div className="bg-[#f59e0b]/10 border border-[#f59e0b]/40 rounded p-2 text-[#fcd34d] flex items-start gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-[#f59e0b] shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold block uppercase">SCIENTIFIC PROTOTYPE DISCLAIMER</span>
                  <span>Retrospective analysis. Not an official IMD warning or operational forecast.</span>
                </div>
              </div>

              <div className="bg-[#121622] border border-[#1e2638] rounded p-2 text-[#94a3b8] flex items-start gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-[#00e5ff] shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-white block uppercase">DATA LEAKAGE AUDIT</span>
                  <span>
                    Training Overlap: <strong className="text-white">{selectedDetail.provenance.training_overlap}</strong> · {selectedDetail.provenance.benchmark_membership}
                  </span>
                </div>
              </div>
            </div>

            {/* Event Window & Spatial Domain */}
            <div className="bg-[#121622] border border-[#1e2638] rounded-md p-3 grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-[#64748b] text-[10px] uppercase font-bold">
                  <Calendar className="w-3 h-3 text-[#00e5ff]" />
                  <span>Event Window & Timeline</span>
                </div>
                <div className="text-white font-semibold">
                  {selectedDetail.event_window.start_date} to {selectedDetail.event_window.end_date}
                </div>
                <div className="text-[11px] text-[#94a3b8]">
                  Peak Day: <strong className="text-[#00e5ff]">{selectedDetail.event_window.peak_date}</strong> ({selectedDetail.event_window.duration_hours}h duration)
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-[#64748b] text-[10px] uppercase font-bold">
                  <MapPin className="w-3 h-3 text-[#00e5ff]" />
                  <span>Geographical Coordinates</span>
                </div>
                <div className="text-white font-semibold truncate">
                  {selectedDetail.spatial_domain.region_name}, {selectedDetail.spatial_domain.state_name}
                </div>
                <div className="text-[11px] text-[#94a3b8]">
                  {selectedDetail.spatial_domain.latitude.toFixed(4)}°N, {selectedDetail.spatial_domain.longitude.toFixed(4)}°E
                  {selectedDetail.spatial_domain.elevation_m !== null && ` (${selectedDetail.spatial_domain.elevation_m}m elevation)`}
                </div>
              </div>
            </div>

            {/* Four-Model Comparison & Observational Ground Truth */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono uppercase font-bold text-[#64748b]">
                <span>Forecast vs Ground Truth Comparison</span>
                <span className="text-[10px] text-[#00e5ff]">
                  Source: {selectedDetail.observation.source_agency}
                </span>
              </div>

              {selectedDetail.forecast_comparison.is_forecast_available ? (
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 font-mono text-center">
                  <div className="bg-[#0e121a] border border-[#10b981]/50 p-2.5 rounded">
                    <span className="text-[9px] text-[#10b981] font-bold block uppercase">Ground Truth</span>
                    <span className="text-base font-bold text-white">
                      {formatNumber(selectedDetail.observation.peak_24h_mm ?? 0, 1)} <span className="text-[10px] text-[#64748b]">mm</span>
                    </span>
                    <span className="text-[9px] text-[#94a3b8] block mt-0.5">Observed</span>
                  </div>

                  <div className="bg-[#0e121a] border border-[#1e2638] p-2.5 rounded">
                    <span className="text-[9px] text-[#94a3b8] font-bold block uppercase">1. Raw NWP</span>
                    <span className="text-base font-bold text-[#94a3b8]">
                      {formatNumber(selectedDetail.forecast_comparison.raw_nwp_mm ?? 0, 1)} <span className="text-[10px] text-[#64748b]">mm</span>
                    </span>
                    <span className="text-[9px] text-[#ef4444] block mt-0.5">
                      Δ {formatNumber(selectedDetail.forecast_comparison.raw_nwp_error_mm ?? 0, 1)} mm
                    </span>
                  </div>

                  <div className="bg-[#0e121a] border border-[#1e2638] p-2.5 rounded">
                    <span className="text-[9px] text-[#cbd5e1] font-bold block uppercase">2. Quantile Map</span>
                    <span className="text-base font-bold text-white">
                      {formatNumber(selectedDetail.forecast_comparison.eqm_mm ?? 0, 1)} <span className="text-[10px] text-[#64748b]">mm</span>
                    </span>
                    <span className="text-[9px] text-[#94a3b8] block mt-0.5">EQM Baseline</span>
                  </div>

                  <div className="bg-[#0e121a] border border-[#1e2638] p-2.5 rounded">
                    <span className="text-[9px] text-[#cbd5e1] font-bold block uppercase">3. Global ML</span>
                    <span className="text-base font-bold text-white">
                      {formatNumber(selectedDetail.forecast_comparison.global_ml_mm ?? 0, 1)} <span className="text-[10px] text-[#64748b]">mm</span>
                    </span>
                    <span className="text-[9px] text-[#94a3b8] block mt-0.5">Non-Regime</span>
                  </div>

                  <div className="bg-[#0e121a] border border-[#00e5ff]/60 p-2.5 rounded shadow-lg bg-[#00e5ff]/5">
                    <span className="text-[9px] text-[#00e5ff] font-bold block uppercase">4. Regime AI</span>
                    <span className="text-base font-bold text-[#00e5ff]">
                      {formatNumber(selectedDetail.forecast_comparison.regime_aware_ml_mm ?? 0, 1)} <span className="text-[10px] text-[#64748b]">mm</span>
                    </span>
                    <span className="text-[9px] text-[#10b981] font-bold block mt-0.5">
                      Δ {formatNumber(selectedDetail.forecast_comparison.regime_aware_error_mm ?? 0, 1)} mm
                    </span>
                  </div>
                </div>
              ) : (
                <div className="bg-[#121622] border border-[#f59e0b]/40 rounded p-3 text-center font-mono space-y-1">
                  <div className="text-sm font-bold text-white">
                    Observed Ground Truth: {formatNumber(selectedDetail.observation.peak_24h_mm ?? 0, 1)} mm / 24h
                  </div>
                  <p className="text-xs text-[#f59e0b]">
                    FORECAST COMPARISON: NOT AVAILABLE — 2005 NWP Model Forecast Fields Not Archived in Repository
                  </p>
                  <p className="text-[11px] text-[#94a3b8]">
                    In accordance with strict scientific protocol, retrospective forecast values were not fabricated.
                  </p>
                </div>
              )}
            </div>

            {/* Uncertainty & Exceedance Probabilities (where available) */}
            {selectedDetail.uncertainty.is_available && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
                {/* Uncertainty Quantiles */}
                <div className="bg-[#121622] border border-[#1e2638] rounded p-3 space-y-2">
                  <span className="text-[10px] uppercase font-bold text-[#64748b] block">
                    Uncertainty Quantiles (P10 / P50 / P90)
                  </span>
                  <div className="grid grid-cols-3 gap-1.5 text-center">
                    <div className="bg-[#0b0e16] p-1.5 rounded border border-[#1e2638]">
                      <span className="text-[9px] text-[#64748b] block">P10</span>
                      <span className="font-bold text-white">{formatNumber(selectedDetail.uncertainty.p10_mm ?? 0, 1)} mm</span>
                    </div>
                    <div className="bg-[#0b0e16] p-1.5 rounded border border-[#00e5ff]/30">
                      <span className="text-[9px] text-[#00e5ff] block">P50</span>
                      <span className="font-bold text-[#00e5ff]">{formatNumber(selectedDetail.uncertainty.p50_mm ?? 0, 1)} mm</span>
                    </div>
                    <div className="bg-[#0b0e16] p-1.5 rounded border border-[#1e2638]">
                      <span className="text-[9px] text-[#64748b] block">P90</span>
                      <span className="font-bold text-white">{formatNumber(selectedDetail.uncertainty.p90_mm ?? 0, 1)} mm</span>
                    </div>
                  </div>
                </div>

                {/* Exceedance Probabilities */}
                <div className="bg-[#121622] border border-[#1e2638] rounded p-3 space-y-2">
                  <span className="text-[10px] uppercase font-bold text-[#64748b] block">
                    Exceedance Probabilities
                  </span>
                  <div className="grid grid-cols-3 gap-1.5 text-center">
                    <div className="bg-[#0b0e16] p-1.5 rounded border border-[#1e2638]">
                      <span className="text-[9px] text-[#94a3b8] block">≥64.5 mm</span>
                      <span className="font-bold text-[#00e5ff]">{Math.round((selectedDetail.exceedance_probabilities.heavy_ge_64_5mm ?? 0) * 100)}%</span>
                    </div>
                    <div className="bg-[#0b0e16] p-1.5 rounded border border-[#1e2638]">
                      <span className="text-[9px] text-[#94a3b8] block">≥115.6 mm</span>
                      <span className="font-bold text-[#f59e0b]">{Math.round((selectedDetail.exceedance_probabilities.very_heavy_ge_115_6mm ?? 0) * 100)}%</span>
                    </div>
                    <div className="bg-[#0b0e16] p-1.5 rounded border border-[#1e2638]">
                      <span className="text-[9px] text-[#94a3b8] block">≥204.5 mm</span>
                      <span className="font-bold text-[#ef4444]">{Math.round((selectedDetail.exceedance_probabilities.extreme_ge_204_5mm ?? 0) * 100)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Synoptic Regime Classification & Physical Explanation */}
            <div className="bg-[#121622] border border-[#1e2638] rounded p-3 space-y-2 font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold text-[#64748b]">Diagnosed Synoptic Weather Regime</span>
                <span className="text-[10px] text-[#00e5ff] font-bold">
                  {selectedDetail.regime.primary_regime ? selectedDetail.regime.primary_regime.replace(/_/g, ' ') : 'UNCLASSIFIED'} ({Math.round((selectedDetail.regime.confidence ?? 0) * 100)}% Conf)
                </span>
              </div>
              <p className="text-[11px] text-[#cbd5e1] leading-relaxed">
                {selectedDetail.synoptic_summary}
              </p>
              <div className="bg-[#0b0e16] p-2.5 rounded border border-[#1e2638] space-y-1">
                <span className="text-[10px] font-bold text-[#00e5ff] uppercase block">
                  Why AI Corrected This Extreme Event:
                </span>
                <p className="text-[11px] text-[#94a3b8] leading-relaxed">
                  {selectedDetail.why_corrected_summary}
                </p>
              </div>
            </div>

            {/* Spatial FSS Status */}
            <div className="bg-[#0e121a] border border-[#1e2638] rounded p-2.5 text-[10px] font-mono text-[#64748b] flex items-center justify-between">
              <span>Multi-Scale Spatial FSS (25km / 50km / 100km):</span>
              <span className="text-[#f59e0b] font-semibold">{selectedDetail.spatial_fss.status_message}</span>
            </div>

            {/* Footer Action Buttons */}
            <div className="flex flex-wrap items-center justify-end gap-2 pt-2 border-t border-[#1e2638]">
              {onFocusLocation && (
                <button
                  type="button"
                  onClick={() => {
                    onFocusLocation(
                      selectedDetail.spatial_domain.latitude,
                      selectedDetail.spatial_domain.longitude,
                      selectedDetail.spatial_domain.region_name
                    );
                    setSelectedCaseId(null);
                    setSelectedDetail(null);
                  }}
                  className="px-3 py-1.5 rounded bg-[#0284c7] hover:bg-[#0369a1] text-white text-xs font-mono transition-colors flex items-center gap-1.5"
                >
                  <Compass className="w-3.5 h-3.5" />
                  <span>Reposition Cesium 3D Camera</span>
                </button>
              )}

              <button
                type="button"
                onClick={() => {
                  setSelectedCaseId(null);
                  setSelectedDetail(null);
                }}
                className="px-3 py-1.5 rounded bg-[#121622] hover:bg-[#1a2030] text-[#94a3b8] hover:text-white text-xs font-mono transition-colors"
              >
                Close Case Profile
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
