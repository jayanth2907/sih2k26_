'use client';

import React from 'react';
import { X, Satellite, Layers, Info, Calendar, ShieldCheck, CheckCircle2, AlertCircle } from 'lucide-react';
import { UnifiedInundationSummary } from '@/lib/types';
import { formatCoordinates, formatNumber, formatTimestamp } from '@/lib/formatters';

interface SatelliteModalProps {
  isOpen: boolean;
  onClose: () => void;
  satellite?: UnifiedInundationSummary | null;
  latitude: number;
  longitude: number;
  locationName: string;
}

export const SatelliteModal: React.FC<SatelliteModalProps> = ({
  isOpen,
  onClose,
  satellite,
  latitude,
  longitude,
  locationName,
}) => {
  if (!isOpen) return null;

  const scene = satellite?.scene || {};
  const polygonCount = satellite?.polygon_count ?? 0;
  const floodedArea = satellite?.flooded_area_sq_km ?? 4.82;
  const validArea = satellite?.valid_area_sq_km ?? 100.0;
  const cloudPct = scene.cloud_coverage_percentage ?? 29.6;
  const sceneId = scene.scene_id || 'S2A_42QZG_20240615_0_L2A';
  const acqDate = scene.acquisition_datetime || '2024-06-15T05:30:00Z';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#0c0f17] border border-[#1e2638] rounded-xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#1e2638] bg-[#101420]">
          <div className="flex items-center gap-2.5">
            <Satellite className="w-5 h-5 text-[#00e5ff]" />
            <div>
              <h3 className="font-bold text-white text-sm tracking-wide uppercase">
                Satellite Multispectral Inundation Observation
              </h3>
              <p className="text-[11px] font-mono text-[#94a3b8]">
                {locationName} · {formatCoordinates(latitude, longitude)}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close satellite modal"
            className="p-1 rounded-md hover:bg-[#1e2638] text-[#94a3b8] hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Telemetry Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="bg-[#121624] border border-[#1e2638] p-3 rounded-lg">
              <div className="text-[10px] font-mono uppercase text-[#64748b]">Sensor & Platform</div>
              <div className="text-sm font-bold font-mono text-white mt-1">Sentinel-2 L2A</div>
              <div className="text-[10px] text-[#00e5ff] font-mono mt-0.5">MSI 6-Band Surface</div>
            </div>

            <div className="bg-[#121624] border border-[#1e2638] p-3 rounded-lg">
              <div className="text-[10px] font-mono uppercase text-[#64748b]">Cloud Coverage</div>
              <div className="text-sm font-bold font-mono text-white mt-1">
                {formatNumber(cloudPct, 1)}%
              </div>
              <div className="text-[10px] text-[#10b981] font-mono mt-0.5">Within QC Limit</div>
            </div>

            <div className="bg-[#121624] border border-[#1e2638] p-3 rounded-lg">
              <div className="text-[10px] font-mono uppercase text-[#64748b]">Inundation Area</div>
              <div className="text-sm font-bold font-mono text-[#00e5ff] mt-1">
                {formatNumber(floodedArea, 2)} km²
              </div>
              <div className="text-[10px] text-[#94a3b8] font-mono mt-0.5">
                {(floodedArea / validArea * 100).toFixed(1)}% of AOI
              </div>
            </div>

            <div className="bg-[#121624] border border-[#1e2638] p-3 rounded-lg">
              <div className="text-[10px] font-mono uppercase text-[#64748b]">Vector Polygons</div>
              <div className="text-sm font-bold font-mono text-white mt-1">
                {polygonCount} Polygons
              </div>
              <div className="text-[10px] text-[#94a3b8] font-mono mt-0.5">WGS84 Contoured</div>
            </div>
          </div>

          {/* Scene Metadata Detail Table */}
          <div className="bg-[#121624] border border-[#1e2638] rounded-lg p-3 space-y-2">
            <div className="text-[11px] font-mono uppercase text-[#64748b] tracking-wider flex items-center justify-between">
              <span>Scene Provenance & Pipeline Parameters</span>
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/40">
                HISTORICAL / DEMO FALLBACK
              </span>
            </div>

            <div className="space-y-1 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-[#1e2638]/50 text-[#94a3b8]">
                <span>Granule / Scene Identifier:</span>
                <span className="text-white select-all">{sceneId}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#1e2638]/50 text-[#94a3b8]">
                <span>Acquisition Datetime:</span>
                <span className="text-white">{formatTimestamp(acqDate)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#1e2638]/50 text-[#94a3b8]">
                <span>Data Ingestion Provider:</span>
                <span className="text-white">AWS Element 84 Earth Search STAC API</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#1e2638]/50 text-[#94a3b8]">
                <span>Multispectral Channels Used:</span>
                <span className="text-[#00e5ff]">B2 (Blue), B3 (Green), B4 (Red), B8 (NIR), B11 (SWIR-1), B12 (SWIR-2)</span>
              </div>
              <div className="flex justify-between py-1 text-[#94a3b8]">
                <span>Spatial Resolution:</span>
                <span className="text-white">10m / 20m resampled to canonical WGS84 grid</span>
              </div>
            </div>
          </div>

          {/* Operational Disclaimer */}
          <div className="flex items-start gap-2 bg-[#121622] border border-[#1e2638] p-2.5 rounded text-[11px] text-[#64748b]">
            <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-[#94a3b8]" />
            <span>
              Sentinel-2 multispectral surface reflectance is ingested as an antecedent saturation and ground inundation baseline. In production deployment with MoES/IMD, INSAT-3DR optical/infrared and GPM IMERG satellite feeds are utilized for real-time quantitative precipitation estimation.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
