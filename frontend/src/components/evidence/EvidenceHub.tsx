'use client';

import React from 'react';
import {
  Satellite,
  Radio,
  Wind,
  CloudRain,
  Maximize2,
  Clock,
  Layers,
} from 'lucide-react';
import {
  UnifiedInundationSummary,
  UnifiedRadarSummary,
  UnifiedNwpSummary,
  RegimeResponse,
  SourceStatusDetail,
} from '@/lib/types';
import { formatNumber, formatTimestamp } from '@/lib/formatters';
import { WEATHER_REGIME_CONFIG } from '@/lib/constants';

interface EvidenceHubProps {
  satellite?: UnifiedInundationSummary | null;
  radar?: UnifiedRadarSummary | null;
  nwp?: UnifiedNwpSummary | null;
  regime?: RegimeResponse | null;
  sourceStatus?: Record<string, SourceStatusDetail>;
  isDemo?: boolean;
  onOpenRadarModal: () => void;
  onOpenSatelliteModal?: () => void;
  onOpenNwpModal?: () => void;
  onOpenAtmosphericModal?: () => void;
}

export const EvidenceHub: React.FC<EvidenceHubProps> = ({
  satellite,
  radar,
  nwp,
  regime,
  sourceStatus,
  isDemo = true,
  onOpenRadarModal,
  onOpenSatelliteModal,
  onOpenNwpModal,
  onOpenAtmosphericModal,
}) => {
  const synoptics = regime?.synoptic_features;
  const primaryRegimeKey =
    typeof regime?.primary_regime === 'object' && regime?.primary_regime !== null
      ? (regime.primary_regime as any).regime
      : (regime?.primary_regime as string | undefined) || 'ACTIVE_MONSOON';

  const regimeConfig = WEATHER_REGIME_CONFIG[primaryRegimeKey as keyof typeof WEATHER_REGIME_CONFIG] || {
    label: primaryRegimeKey.replace(/_/g, ' '),
    color: '#00e5ff',
    bgColor: '#00e5ff15',
    borderColor: '#00e5ff50',
  };

  return (
    <div className="bg-[#0b0e16] border border-[#1e2638] rounded-lg p-4 shadow-xl space-y-4">
      {/* Evidence Hub Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1e2638] pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-md bg-[#0284c7]/10 border border-[#0284c7]/30">
            <Layers className="w-4 h-4 text-[#00e5ff]" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wider uppercase flex items-center gap-2">
              Multi-Source Meteorological Evidence Hub
              <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-[#0284c7]/20 text-[#00e5ff] border border-[#0284c7]/40">
                4 Interactive Viewers
              </span>
            </h2>
            <p className="text-[11px] font-mono text-[#94a3b8] tracking-wider mt-0.5">
              OBSERVATIONAL SATELLITE, RADAR, SYNOPTIC REGIME FORCING & NUMERICAL BASELINES
            </p>
          </div>
        </div>

        {/* Global Provenance Indicator */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#141824] border border-[#1e2638] text-[10px] font-mono">
            <span className="w-2 h-2 rounded-full bg-[#f59e0b] animate-pulse" />
            <span className="text-[#f59e0b] font-semibold">DEMO DATA · SYNTHETIC / FALLBACK MODE</span>
          </div>
        </div>
      </div>

      {/* 4-Card Multi-Source Telemetry Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* ========================================================================= */}
        {/* 1. SATELLITE OBSERVATION CARD */}
        {/* ========================================================================= */}
        <div className="bg-[#101420] border border-[#1e2638] hover:border-[#00e5ff]/40 rounded-lg p-3 flex flex-col justify-between space-y-2.5 transition-all shadow-md">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase font-bold text-white flex items-center gap-1.5">
                <Satellite className="w-3.5 h-3.5 text-[#00e5ff]" />
                1. Satellite Observation
              </span>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#00e5ff]/10 text-[#00e5ff] border border-[#00e5ff]/30">
                {sourceStatus?.satellite_model2?.status === 'success' ? 'AVAILABLE' : 'FALLBACK'}
              </span>
            </div>

            {/* Satellite Scene Info */}
            <div className="bg-[#0a0c12] p-2.5 rounded border border-[#1e2638] space-y-1.5 text-xs font-mono">
              <div className="flex justify-between text-[#94a3b8]">
                <span>Sensor:</span>
                <span className="text-white truncate max-w-[130px]">Sentinel-2 L2A / INSAT</span>
              </div>
              <div className="flex justify-between text-[#94a3b8]">
                <span>Cloud Cover:</span>
                <span className="text-white">
                  {satellite?.scene?.cloud_coverage_percentage !== undefined
                    ? `${formatNumber(satellite.scene.cloud_coverage_percentage, 1)}%`
                    : '29.6%'}
                </span>
              </div>
              <div className="flex justify-between text-[#94a3b8]">
                <span>Inundation Area:</span>
                <span className="text-[#00e5ff] font-semibold">
                  {satellite?.flooded_area_sq_km !== undefined
                    ? `${formatNumber(satellite.flooded_area_sq_km, 2)} km²`
                    : '4.82 km²'}
                </span>
              </div>
              <div className="flex justify-between text-[#94a3b8]">
                <span>Analyzed Extent:</span>
                <span className="text-white">
                  {satellite?.valid_area_sq_km !== undefined
                    ? `${formatNumber(satellite.valid_area_sq_km, 1)} km²`
                    : '100.0 km²'}
                </span>
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onOpenSatelliteModal}
            className="w-full py-1.5 px-2 rounded bg-[#141824] hover:bg-[#1a2030] text-[#00e5ff] text-[10px] font-mono font-semibold flex items-center justify-center gap-1 transition-colors border border-[#1e2638]"
          >
            <Maximize2 className="w-3 h-3" />
            <span>CLICK TO VIEW SATELLITE DETAILS</span>
          </button>
        </div>

        {/* ========================================================================= */}
        {/* 2. DOPPLER RADAR EVIDENCE CARD */}
        {/* ========================================================================= */}
        <div className="bg-[#101420] border border-[#1e2638] hover:border-[#00e5ff]/40 rounded-lg p-3 flex flex-col justify-between space-y-2.5 transition-all shadow-md">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase font-bold text-white flex items-center gap-1.5">
                <Radio className="w-3.5 h-3.5 text-[#00e5ff]" />
                2. Doppler Radar
              </span>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/30">
                {radar?.max_reflectivity_dbz ? 'ACTIVE FEED' : 'RADAR UNAVAILABLE'}
              </span>
            </div>

            {/* Radar Telemetry Grid */}
            <div className="bg-[#0a0c12] p-2.5 rounded border border-[#1e2638] space-y-1.5 text-xs font-mono">
              <div className="flex justify-between items-baseline">
                <span className="text-[#94a3b8]">Max Reflectivity:</span>
                <span className="text-base font-bold text-white">
                  {radar?.max_reflectivity_dbz !== undefined
                    ? `${formatNumber(radar.max_reflectivity_dbz, 1)} dBZ`
                    : '34.2 dBZ'}
                </span>
              </div>
              <div className="flex justify-between text-[#94a3b8]">
                <span>Est. Rain Rate:</span>
                <span className="text-[#00e5ff] font-semibold">
                  {radar?.estimated_rain_rate_mm_hr !== undefined
                    ? `${formatNumber(radar.estimated_rain_rate_mm_hr, 1)} mm/h`
                    : '12.4 mm/h'}
                </span>
              </div>
              <div className="flex justify-between text-[#94a3b8]">
                <span>Echo Coverage:</span>
                <span className="text-white">
                  {radar?.coverage_percentage !== undefined
                    ? `${formatNumber(radar.coverage_percentage, 1)}%`
                    : '42.0%'}
                </span>
              </div>
              <div className="flex justify-between text-[#94a3b8]">
                <span>Scan Time:</span>
                <span className="text-white truncate max-w-[120px]">
                  {formatTimestamp(radar?.timestamp)}
                </span>
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onOpenRadarModal}
            className="w-full py-1.5 px-2 rounded bg-[#141824] hover:bg-[#1a2030] text-[#00e5ff] text-[10px] font-mono font-semibold flex items-center justify-center gap-1 transition-colors border border-[#1e2638]"
          >
            <Maximize2 className="w-3 h-3" />
            <span>CLICK TO EXPAND RADAR VIEW</span>
          </button>
        </div>

        {/* ========================================================================= */}
        {/* 3. ATMOSPHERIC DRIVERS CARD (PS26080 SYNOPTIC ENGINE) */}
        {/* ========================================================================= */}
        <div className="bg-[#101420] border border-[#1e2638] hover:border-[#00e5ff]/40 rounded-lg p-3 flex flex-col justify-between space-y-2.5 transition-all shadow-md">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase font-bold text-white flex items-center gap-1.5">
                <Wind className="w-3.5 h-3.5 text-[#00e5ff]" />
                3. Atmospheric Drivers
              </span>
              <span
                className="text-[9px] font-mono px-1.5 py-0.5 rounded font-semibold"
                style={{
                  color: regimeConfig.color,
                  backgroundColor: regimeConfig.bgColor,
                  border: `1px solid ${regimeConfig.borderColor}`,
                }}
              >
                {regimeConfig.label}
              </span>
            </div>

            {/* Synoptic Features Breakdown */}
            <div className="bg-[#0a0c12] p-2.5 rounded border border-[#1e2638] space-y-1 text-[11px] font-mono">
              <div className="flex justify-between text-[#94a3b8]">
                <span>850 hPa LLJ Speed:</span>
                <span className="text-white font-semibold">
                  {synoptics?.low_level_jet_speed_kts !== undefined
                    ? `${formatNumber(synoptics.low_level_jet_speed_kts, 1)} kts`
                    : '28.4 kts'}
                </span>
              </div>
              <div className="flex justify-between text-[#94a3b8]">
                <span>Monsoon Trough:</span>
                <span className="text-white">
                  {synoptics?.monsoon_trough_lat !== undefined
                    ? `${formatNumber(synoptics.monsoon_trough_lat, 1)}° N`
                    : '21.4° N'}
                </span>
              </div>
              <div className="flex justify-between text-[#94a3b8]">
                <span>Convective OLR:</span>
                <span className="text-[#00e5ff]">
                  {synoptics?.olr_w_m2 !== undefined
                    ? `${formatNumber(synoptics.olr_w_m2, 0)} W/m²`
                    : '184 W/m²'}
                </span>
              </div>
              <div className="flex justify-between text-[#94a3b8]">
                <span>Orographic Lift:</span>
                <span className="text-white">
                  {synoptics?.orographic_lift_index !== undefined
                    ? formatNumber(synoptics.orographic_lift_index, 2)
                    : '0.74'}
                </span>
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onOpenAtmosphericModal}
            className="w-full py-1.5 px-2 rounded bg-[#141824] hover:bg-[#1a2030] text-[#00e5ff] text-[10px] font-mono font-semibold flex items-center justify-center gap-1 transition-colors border border-[#1e2638]"
          >
            <Maximize2 className="w-3 h-3" />
            <span>CLICK TO VIEW SYNOPTIC DRIVERS</span>
          </button>
        </div>

        {/* ========================================================================= */}
        {/* 4. RAW NWP FORECAST CARD */}
        {/* ========================================================================= */}
        <div className="bg-[#101420] border border-[#1e2638] hover:border-[#00e5ff]/40 rounded-lg p-3 flex flex-col justify-between space-y-2.5 transition-all shadow-md">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono uppercase font-bold text-white flex items-center gap-1.5">
                <CloudRain className="w-3.5 h-3.5 text-[#00e5ff]" />
                4. Raw NWP Forecast
              </span>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#64748b]/20 text-[#94a3b8] border border-[#64748b]/40">
                UNCALIBRATED
              </span>
            </div>

            {/* NWP Metrics & Mini Meteogram */}
            <div className="bg-[#0a0c12] p-2.5 rounded border border-[#1e2638] space-y-1.5 text-xs font-mono">
              <div className="flex justify-between items-baseline">
                <span className="text-[#94a3b8]">24h Total Precip:</span>
                <span className="text-base font-bold text-white">
                  {nwp?.accumulated_precipitation_mm !== undefined
                    ? `${formatNumber(nwp.accumulated_precipitation_mm, 1)} mm`
                    : '38.5 mm'}
                </span>
              </div>
              <div className="flex justify-between text-[#94a3b8]">
                <span>Peak Hourly Rate:</span>
                <span className="text-white">
                  {nwp?.peak_hourly_precipitation_mm_hr !== undefined
                    ? `${formatNumber(nwp.peak_hourly_precipitation_mm_hr, 1)} mm/h`
                    : '7.2 mm/h'}
                </span>
              </div>

              {/* Mini 24h Time Series Bar Visualization */}
              {nwp?.hourly_precipitation && nwp.hourly_precipitation.length > 0 ? (
                <div className="pt-1">
                  <div className="text-[9px] text-[#64748b] mb-0.5">24h Hourly Rate Distribution:</div>
                  <div className="h-8 flex items-end gap-0.5 bg-[#141824] p-1 rounded border border-[#1e2638]">
                    {nwp.hourly_precipitation.slice(0, 24).map((val, idx) => {
                      const maxVal = Math.max(1, ...nwp.hourly_precipitation);
                      const heightPct = Math.max(8, (val / maxVal) * 100);
                      return (
                        <div
                          key={idx}
                          className="flex-1 h-full flex items-end"
                          title={`Hour +${idx + 1}: ${val} mm/h`}
                        >
                          <div
                            className="w-full rounded-t-xs bg-[#0284c7] hover:bg-[#00e5ff] transition-colors"
                            style={{ height: `${heightPct}%` }}
                          />
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="h-8 bg-[#141824] rounded border border-[#1e2638] flex items-center justify-center text-[10px] text-[#64748b]">
                  24h Horizon Loaded
                </div>
              )}
            </div>
          </div>

          <button
            type="button"
            onClick={onOpenNwpModal}
            className="w-full py-1.5 px-2 rounded bg-[#141824] hover:bg-[#1a2030] text-[#00e5ff] text-[10px] font-mono font-semibold flex items-center justify-center gap-1 transition-colors border border-[#1e2638]"
          >
            <Maximize2 className="w-3 h-3" />
            <span>CLICK TO VIEW FORECAST DETAILS</span>
          </button>
        </div>
      </div>
    </div>
  );
};
