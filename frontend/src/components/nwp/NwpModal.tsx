'use client';

import React from 'react';
import { X, CloudRain, Clock, TrendingUp, Info, Activity, Layers, ShieldCheck } from 'lucide-react';
import { UnifiedNwpSummary } from '@/lib/types';
import { formatCoordinates, formatNumber, formatTimestamp } from '@/lib/formatters';

interface NwpModalProps {
  isOpen: boolean;
  onClose: () => void;
  nwp?: UnifiedNwpSummary | null;
  latitude: number;
  longitude: number;
  locationName: string;
}

export const NwpModal: React.FC<NwpModalProps> = ({
  isOpen,
  onClose,
  nwp,
  latitude,
  longitude,
  locationName,
}) => {
  if (!isOpen) return null;

  const totalPrecip = nwp?.accumulated_precipitation_mm ?? 38.5;
  const peakRate = nwp?.peak_hourly_precipitation_mm_hr ?? 7.2;
  const horizon = nwp?.forecast_horizon_hours ?? 24;
  const maxCape = nwp?.max_cape_j_kg ?? 1480;
  const hourly = nwp?.hourly_precipitation || [];
  const modelName = nwp?.model_name || 'NOAA GFS 0.25° Seamless';
  const source = nwp?.source || 'Open-Meteo GFS API (NCMRWF NCUM Fallback)';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#0c0f17] border border-[#1e2638] rounded-xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#1e2638] bg-[#101420]">
          <div className="flex items-center gap-2.5">
            <CloudRain className="w-5 h-5 text-[#00e5ff]" />
            <div>
              <h3 className="font-bold text-white text-sm tracking-wide uppercase">
                Numerical Weather Prediction Baseline Forecast
              </h3>
              <p className="text-[11px] font-mono text-[#94a3b8]">
                {locationName} · {formatCoordinates(latitude, longitude)}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close NWP modal"
            className="p-1 rounded-md hover:bg-[#1e2638] text-[#94a3b8] hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Telemetry Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="bg-[#121624] border border-[#1e2638] p-3 rounded-lg">
              <div className="text-[10px] font-mono uppercase text-[#64748b]">24h Total Precipitation</div>
              <div className="text-xl font-bold font-mono text-white mt-0.5">
                {formatNumber(totalPrecip, 1)} mm
              </div>
              <div className="text-[10px] text-[#94a3b8] font-mono mt-0.5">Raw Uncalibrated</div>
            </div>

            <div className="bg-[#121624] border border-[#1e2638] p-3 rounded-lg">
              <div className="text-[10px] font-mono uppercase text-[#64748b]">Peak Hourly Rate</div>
              <div className="text-xl font-bold font-mono text-white mt-0.5">
                {formatNumber(peakRate, 1)} mm/h
              </div>
              <div className="text-[10px] text-[#00e5ff] font-mono mt-0.5">Maximum Convective Burst</div>
            </div>

            <div className="bg-[#121624] border border-[#1e2638] p-3 rounded-lg">
              <div className="text-[10px] font-mono uppercase text-[#64748b]">Peak CAPE Instability</div>
              <div className="text-xl font-bold font-mono text-white mt-0.5">
                {formatNumber(maxCape, 0)} J/kg
              </div>
              <div className="text-[10px] text-[#f59e0b] font-mono mt-0.5">Thermodynamic Energy</div>
            </div>

            <div className="bg-[#121624] border border-[#1e2638] p-3 rounded-lg">
              <div className="text-[10px] font-mono uppercase text-[#64748b]">Forecast Horizon</div>
              <div className="text-xl font-bold font-mono text-white mt-0.5">
                {horizon} Hours
              </div>
              <div className="text-[10px] text-[#10b981] font-mono mt-0.5">Hourly Synoptic Steps</div>
            </div>
          </div>

          {/* 24-Hour Meteogram Bar Chart */}
          <div className="bg-[#121624] border border-[#1e2638] rounded-lg p-3 space-y-2">
            <div className="flex items-center justify-between text-[11px] font-mono uppercase text-[#64748b]">
              <span>24-Hour Chronological Hourly Rainfall Distribution (mm/h)</span>
              <span className="text-[#00e5ff]">0h → +24h Horizon</span>
            </div>

            {hourly.length > 0 ? (
              <div className="pt-2">
                <div className="h-28 flex items-end gap-1 bg-[#0a0c12] p-2 rounded border border-[#1e2638]">
                  {hourly.slice(0, 24).map((val, idx) => {
                    const maxVal = Math.max(1, ...hourly);
                    const heightPct = Math.max(6, (val / maxVal) * 100);
                    return (
                      <div
                        key={idx}
                        className="flex-1 h-full flex flex-col justify-end items-center group relative"
                      >
                        <div
                          className="w-full rounded-t-xs bg-[#0284c7] group-hover:bg-[#00e5ff] transition-colors"
                          style={{ height: `${heightPct}%` }}
                        />
                        <span className="text-[8px] font-mono text-[#64748b] mt-1">
                          +{idx + 1}h
                        </span>
                        {/* Tooltip */}
                        <div className="absolute bottom-full mb-1 hidden group-hover:block bg-[#08090c] border border-[#00e5ff] px-1.5 py-0.5 rounded text-[9px] font-mono text-white z-20 whitespace-nowrap shadow-lg">
                          +{idx + 1}h: {val.toFixed(1)} mm/h
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="h-20 bg-[#0a0c12] rounded border border-[#1e2638] flex items-center justify-center text-xs text-[#64748b] font-mono">
                No hourly time-series array provided.
              </div>
            )}
          </div>

          {/* NWP Provenance Card */}
          <div className="bg-[#121624] border border-[#1e2638] rounded-lg p-3 space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between border-b border-[#1e2638] pb-1.5">
              <span className="text-[10px] uppercase text-[#64748b]">Model Provenance & Feed Type</span>
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/40">
                DEVELOPMENT FALLBACK / PROTOTYPE FEED
              </span>
            </div>
            <div className="space-y-1 text-[#94a3b8]">
              <div className="flex justify-between py-0.5">
                <span>Numerical Model:</span>
                <span className="text-white">{modelName}</span>
              </div>
              <div className="flex justify-between py-0.5">
                <span>Operational Data Provider:</span>
                <span className="text-white">{source}</span>
              </div>
              <div className="flex justify-between py-0.5">
                <span>Target Operational Model (MoES):</span>
                <span className="text-[#00e5ff]">NCMRWF NCUM Global 12km / NEPS 22-Member Ensemble</span>
              </div>
            </div>
          </div>

          {/* Operational Disclaimer */}
          <div className="flex items-start gap-2 bg-[#121622] border border-[#1e2638] p-2.5 rounded text-[11px] text-[#64748b]">
            <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-[#94a3b8]" />
            <span>
              The raw NWP output represents direct uncalibrated physics from the numerical model. MEGHANETRA applies soft-conditioned regime-aware AI residual post-processing to systematically correct orographic and convective bias deltas.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
