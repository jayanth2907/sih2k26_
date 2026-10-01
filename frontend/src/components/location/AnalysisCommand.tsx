'use client';

import React, { useState, useId } from 'react';
import {
  Play,
  Settings2,
  MapPin,
  ChevronDown,
  Check,
  AlertCircle,
  Loader2,
  Calendar,
  Clock,
  Layers,
  Cpu,
  Info,
  Sliders,
  X,
} from 'lucide-react';
import { PRESET_LOCATIONS } from '@/lib/constants';
import { formatCoordinates } from '@/lib/formatters';
import {
  PresetLocation,
  PostProcessingModelId,
  CesiumRainfallLayerId,
} from '@/lib/types';

interface AnalysisCommandProps {
  selectedLocation: PresetLocation | null;
  onSelectPreset: (preset: PresetLocation) => void;
  onSelectCustom: (lat: number, lon: number, name: string) => void;
  onRunAnalysis: () => void;
  isLoading: boolean;
  predictionDate: string;
  onChangeDate: (date: string) => void;
  nwpHorizonHours: number;
  onChangeNwpHorizon: (hours: number) => void;
  satelliteMaxCloud: number;
  onChangeSatelliteMaxCloud: (cloud: number) => void;
  selectedModel?: PostProcessingModelId;
  onSelectModel?: (model: PostProcessingModelId) => void;
  activeLayer?: CesiumRainfallLayerId;
  onSelectLayer?: (layer: CesiumRainfallLayerId) => void;
}

const FORECAST_WINDOWS = [
  { value: 24, label: '24 Hours', sublabel: 'Standard' },
  { value: 48, label: '48 Hours', sublabel: 'Extended' },
  { value: 72, label: '72 Hours', sublabel: '3-Day Outlook' },
];

const MODEL_OPTIONS: {
  id: PostProcessingModelId;
  name: string;
  badge: string;
  description: string;
}[] = [
  {
    id: 'regime_aware_ml',
    name: 'Regime-Aware AI',
    badge: 'MoES PS26080 Target',
    description: 'Soft-conditioned Mixture of Experts with dynamic regime residual correction',
  },
  {
    id: 'global_ml',
    name: 'Global ML',
    badge: 'HistGBM Baseline',
    description: 'Stationary pan-India machine learning correction without regime conditioning',
  },
  {
    id: 'quantile_mapping',
    name: 'EQM',
    badge: 'Statistical CDF',
    description: 'Empirical Quantile Mapping distribution calibration baseline',
  },
  {
    id: 'raw_nwp',
    name: 'Raw NWP',
    badge: 'NCUM / GFS Uncalibrated',
    description: 'Direct uncalibrated numerical weather prediction model output',
  },
];

const LAYER_OPTIONS: {
  id: CesiumRainfallLayerId;
  label: string;
  badge: string;
}[] = [
  { id: 'ai_calibrated', label: 'AI Calibrated Rainfall', badge: 'MoES Target' },
  { id: 'raw_nwp', label: 'Raw NWP', badge: 'Baseline' },
  { id: 'bias_delta', label: 'Bias Delta', badge: 'Δ mm' },
  { id: 'heavy_prob', label: 'Heavy Rain Probability', badge: 'P ≥ 64.5mm' },
  { id: 'regime', label: 'Weather Regime', badge: 'Synoptic' },
  { id: 'uncertainty', label: 'Uncertainty Bounds', badge: 'P10 - P90' },
];

export const AnalysisCommand: React.FC<AnalysisCommandProps> = ({
  selectedLocation,
  onSelectPreset,
  onSelectCustom,
  onRunAnalysis,
  isLoading,
  predictionDate,
  onChangeDate,
  nwpHorizonHours,
  onChangeNwpHorizon,
  satelliteMaxCloud,
  onChangeSatelliteMaxCloud,
  selectedModel = 'regime_aware_ml',
  onSelectModel,
  activeLayer = 'ai_calibrated',
  onSelectLayer,
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isCustomMode, setIsCustomMode] = useState(false);
  const [customLat, setCustomLat] = useState('');
  const [customLon, setCustomLon] = useState('');
  const [customName, setCustomName] = useState('');
  const [customError, setCustomError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [locationSearchQuery, setLocationSearchQuery] = useState('');

  const locationSelectId = useId();
  const dateInputId = useId();
  const horizonSelectId = useId();

  const handleSelectPreset = (preset: PresetLocation) => {
    setIsCustomMode(false);
    setIsDropdownOpen(false);
    setCustomError(null);
    onSelectPreset(preset);
  };

  const handleApplyCustom = (e: React.FormEvent) => {
    e.preventDefault();
    const lat = parseFloat(customLat);
    const lon = parseFloat(customLon);

    if (isNaN(lat) || lat < -90 || lat > 90) {
      setCustomError('Latitude must be a valid number between -90.0 and 90.0');
      return;
    }
    if (isNaN(lon) || lon < -180 || lon > 180) {
      setCustomError('Longitude must be a valid number between -180.0 and 180.0');
      return;
    }

    setCustomError(null);
    setIsDropdownOpen(false);
    onSelectCustom(
      lat,
      lon,
      customName.trim() || `Custom Point (${lat.toFixed(4)}, ${lon.toFixed(4)})`
    );
  };

  const filteredPresets = PRESET_LOCATIONS.filter(
    (p) =>
      p.name.toLowerCase().includes(locationSearchQuery.toLowerCase()) ||
      p.state.toLowerCase().includes(locationSearchQuery.toLowerCase())
  );

  return (
    <div className="relative z-30 bg-[#0c0f17]/95 border border-[#1e2638] rounded-lg p-3 shadow-2xl backdrop-blur-md max-w-6xl mx-auto space-y-3">
      {/* Primary Forecast Command Bar */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-2.5 items-center">
        {/* 1. Target Location Control (Span 4) */}
        <div className="relative md:col-span-4">
          <label
            htmlFor={locationSelectId}
            className="block text-[10px] font-mono text-[#64748b] uppercase tracking-wider mb-1 flex items-center gap-1"
          >
            <MapPin className="w-3 h-3 text-[#00e5ff]" />
            Target Location
          </label>
          <button
            type="button"
            id={locationSelectId}
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            aria-expanded={isDropdownOpen}
            aria-label="Select forecast target location"
            className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-md bg-[#141824] border border-[#2a3449] hover:border-[#00e5ff]/50 text-left transition-colors focus:outline-none focus:border-[#00e5ff]"
          >
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="truncate">
                <div className="font-semibold text-white text-xs sm:text-sm truncate">
                  {selectedLocation
                    ? `${selectedLocation.name}, ${selectedLocation.state}`
                    : 'Select Location'}
                </div>
                {selectedLocation && (
                  <div className="font-mono text-[10px] text-[#94a3b8] truncate">
                    {formatCoordinates(selectedLocation.latitude, selectedLocation.longitude)}
                  </div>
                )}
              </div>
            </div>
            <ChevronDown
              className={`w-4 h-4 text-[#94a3b8] shrink-0 transition-transform ${
                isDropdownOpen ? 'rotate-180' : ''
              }`}
            />
          </button>

          {/* Location Dropdown Modal */}
          {isDropdownOpen && (
            <div className="absolute top-full left-0 mt-1.5 w-full min-w-[300px] sm:min-w-[340px] rounded-md bg-[#10141e] border border-[#2a3449] shadow-2xl z-50 p-2 space-y-1.5 animate-in fade-in zoom-in-95 duration-100">
              <div className="flex items-center justify-between px-1 pb-1 border-b border-[#1e2638]">
                <span className="text-[10px] font-mono uppercase text-[#64748b]">
                  Monitored Monsoon Locations
                </span>
                <button
                  type="button"
                  onClick={() => setIsDropdownOpen(false)}
                  className="text-[#94a3b8] hover:text-white p-0.5 rounded"
                  aria-label="Close location picker"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Search Filter */}
              <input
                type="text"
                placeholder="Search city, district, or state..."
                value={locationSearchQuery}
                onChange={(e) => setLocationSearchQuery(e.target.value)}
                className="w-full bg-[#0a0c12] border border-[#2a3449] rounded px-2.5 py-1 text-xs text-white focus:border-[#00e5ff] focus:outline-none font-mono"
              />

              <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
                {filteredPresets.map((preset) => {
                  const isSelected = selectedLocation?.id === preset.id && !isCustomMode;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => handleSelectPreset(preset)}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-left text-xs transition-colors ${
                        isSelected
                          ? 'bg-[#0284c7]/20 text-[#00e5ff] border border-[#0284c7]/40'
                          : 'hover:bg-[#161b26] text-white'
                      }`}
                    >
                      <div className="truncate">
                        <div className="font-medium truncate">
                          {preset.name}, {preset.state}
                        </div>
                        <div className="font-mono text-[10px] text-[#64748b]">
                          {formatCoordinates(preset.latitude, preset.longitude)}
                        </div>
                      </div>
                      {isSelected && <Check className="w-3.5 h-3.5 text-[#00e5ff] shrink-0" />}
                    </button>
                  );
                })}
              </div>

              <div className="border-t border-[#1e2638] pt-1" />

              <button
                type="button"
                id="custom-coordinates-toggle"
                onClick={() => setIsCustomMode(!isCustomMode)}
                className="w-full flex items-center justify-between px-2 py-1.5 rounded text-left text-xs text-[#cbd5e1] hover:bg-[#161b26] transition-colors"
              >
                <span>Enter Custom Coordinates</span>
                <span className="font-mono text-[10px] text-[#00e5ff]">WGS84</span>
              </button>

              {isCustomMode && (
                <form
                  onSubmit={handleApplyCustom}
                  className="p-2 space-y-2 bg-[#0a0c12] rounded border border-[#1e2638]"
                >
                  {customError && (
                    <div className="flex items-center gap-1.5 text-[11px] text-[#ef4444] bg-[#ef4444]/10 p-1.5 rounded">
                      <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                      <span>{customError}</span>
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[9px] font-mono text-[#94a3b8] block">LATITUDE</label>
                      <input
                        type="number"
                        step="any"
                        placeholder="19.0760"
                        value={customLat}
                        onChange={(e) => setCustomLat(e.target.value)}
                        className="w-full bg-[#141824] border border-[#2a3449] rounded px-2 py-1 text-xs text-white font-mono focus:border-[#00e5ff] focus:outline-none"
                        required
                      />
                    </div>
                    <div>
                      <label className="text-[9px] font-mono text-[#94a3b8] block">LONGITUDE</label>
                      <input
                        type="number"
                        step="any"
                        placeholder="72.8777"
                        value={customLon}
                        onChange={(e) => setCustomLon(e.target.value)}
                        className="w-full bg-[#141824] border border-[#2a3449] rounded px-2 py-1 text-xs text-white font-mono focus:border-[#00e5ff] focus:outline-none"
                        required
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-[9px] font-mono text-[#94a3b8] block">LOCATION NAME</label>
                    <input
                      type="text"
                      placeholder="e.g. Mahabaleshwar Catchment"
                      value={customName}
                      onChange={(e) => setCustomName(e.target.value)}
                      className="w-full bg-[#141824] border border-[#2a3449] rounded px-2 py-1 text-xs text-white focus:border-[#00e5ff] focus:outline-none"
                    />
                  </div>
                  <button
                    type="submit"
                    className="w-full py-1.5 bg-[#0284c7] hover:bg-[#0284c7]/90 text-white font-semibold text-xs rounded transition-colors"
                  >
                    Set Coordinates & Update Camera
                  </button>
                </form>
              )}
            </div>
          )}
        </div>

        {/* 2. Target Forecast Date (Span 3) */}
        <div className="md:col-span-3">
          <label
            htmlFor={dateInputId}
            className="block text-[10px] font-mono text-[#64748b] uppercase tracking-wider mb-1 flex items-center gap-1"
          >
            <Calendar className="w-3 h-3 text-[#00e5ff]" />
            Target Forecast Date
          </label>
          <div className="relative">
            <input
              type="date"
              id={dateInputId}
              value={predictionDate}
              onChange={(e) => onChangeDate(e.target.value)}
              aria-label="Target Forecast Date"
              className="w-full bg-[#141824] border border-[#2a3449] rounded-md px-3 py-2 text-xs sm:text-sm text-white font-mono focus:border-[#00e5ff] focus:outline-none transition-colors"
            />
          </div>
        </div>

        {/* 3. NWP Forecast Window (Span 3) */}
        <div className="md:col-span-3">
          <label
            htmlFor={horizonSelectId}
            className="block text-[10px] font-mono text-[#64748b] uppercase tracking-wider mb-1 flex items-center gap-1"
          >
            <Clock className="w-3 h-3 text-[#00e5ff]" />
            NWP Forecast Window
          </label>
          <select
            id={horizonSelectId}
            value={nwpHorizonHours}
            onChange={(e) => onChangeNwpHorizon(parseInt(e.target.value, 10))}
            aria-label="Numerical Weather Prediction Forecast Window"
            className="w-full bg-[#141824] border border-[#2a3449] rounded-md px-3 py-2 text-xs sm:text-sm text-white font-mono focus:border-[#00e5ff] focus:outline-none transition-colors"
          >
            {FORECAST_WINDOWS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label} ({opt.sublabel})
              </option>
            ))}
          </select>
        </div>

        {/* 4. Action Controls: Settings & Run Analysis (Span 2) */}
        <div className="md:col-span-2 flex items-end gap-2 pt-1 sm:pt-0">
          {/* Settings Popover Trigger */}
          <button
            type="button"
            onClick={() => setShowSettings(!showSettings)}
            aria-expanded={showSettings}
            aria-label="Open forecast analysis settings"
            className={`p-2.5 rounded-md border text-xs flex items-center justify-center transition-colors focus:outline-none ${
              showSettings
                ? 'bg-[#0284c7]/20 border-[#00e5ff]/50 text-[#00e5ff]'
                : 'bg-[#141824] border-[#2a3449] text-[#94a3b8] hover:text-white hover:border-[#94a3b8]'
            }`}
            title="Analysis parameters & layer configuration"
          >
            <Settings2 className="w-4 h-4" />
          </button>

          {/* Primary Run Analysis Button */}
          <button
            type="button"
            id="run-analysis-button"
            onClick={onRunAnalysis}
            disabled={isLoading || !selectedLocation}
            aria-label={isLoading ? 'Analyzing meteorological data' : 'Execute forecast analysis'}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-md bg-[#0284c7] hover:bg-[#0369a1] active:scale-[0.98] disabled:opacity-50 text-white font-semibold text-xs tracking-wider transition-all shadow-lg shadow-[#0284c7]/20 focus:outline-none focus:ring-2 focus:ring-[#00e5ff]"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span className="truncate">ANALYZING...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-white shrink-0" />
                <span className="truncate">RUN ANALYSIS</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Advanced Settings & Configuration Drawer */}
      {showSettings && (
        <div className="pt-3 border-t border-[#1e2638] space-y-3.5 animate-in fade-in duration-150">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold text-white uppercase tracking-wider">
              <Sliders className="w-3.5 h-3.5 text-[#00e5ff]" />
              <span>Forecast Analysis & Visualization Settings</span>
            </div>
            <button
              type="button"
              onClick={() => setShowSettings(false)}
              className="text-[#94a3b8] hover:text-white text-xs font-mono"
            >
              Close ✕
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Section A: Model / Post-Processor Selection */}
            <div className="bg-[#10141e] border border-[#1e2638] rounded-md p-2.5 space-y-2">
              <div className="flex items-center justify-between border-b border-[#1e2638] pb-1.5">
                <span className="text-[10px] font-mono text-[#64748b] uppercase tracking-wider flex items-center gap-1">
                  <Cpu className="w-3 h-3 text-[#00e5ff]" />
                  Model / Post-Processor
                </span>
                <span className="text-[9px] font-mono text-[#00e5ff] bg-[#00e5ff]/10 px-1.5 py-0.5 rounded">
                  4-Method Suite
                </span>
              </div>
              <div className="grid grid-cols-2 gap-1.5">
                {MODEL_OPTIONS.map((m) => {
                  const isSelected = selectedModel === m.id;
                  return (
                    <button
                      key={m.id}
                      type="button"
                      onClick={() => onSelectModel?.(m.id)}
                      className={`p-2 rounded border text-left transition-all ${
                        isSelected
                          ? 'bg-[#0284c7]/20 border-[#00e5ff] text-white shadow-sm'
                          : 'bg-[#141824] border-[#1e2638] text-[#94a3b8] hover:text-white hover:border-[#2a3449]'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold">{m.name}</span>
                        {isSelected && <Check className="w-3 h-3 text-[#00e5ff]" />}
                      </div>
                      <div className="text-[9px] font-mono text-[#64748b] mt-0.5 truncate">
                        {m.badge}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Section B: Informational IMD Rainfall Thresholds */}
            <div className="bg-[#10141e] border border-[#1e2638] rounded-md p-2.5 space-y-2">
              <div className="flex items-center justify-between border-b border-[#1e2638] pb-1.5">
                <span className="text-[10px] font-mono text-[#64748b] uppercase tracking-wider flex items-center gap-1">
                  <Info className="w-3 h-3 text-[#f59e0b]" />
                  IMD Rainfall Thresholds
                </span>
                <span className="text-[9px] font-mono text-[#f59e0b] bg-[#f59e0b]/10 px-1.5 py-0.5 rounded">
                  Standard Limits
                </span>
              </div>
              <div className="space-y-1.5 text-xs">
                <div className="flex items-center justify-between bg-[#141824] p-1.5 rounded border border-[#1e2638]">
                  <span className="text-[#cbd5e1] flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#f59e0b]" />
                    Heavy Rain:
                  </span>
                  <span className="font-mono text-white font-semibold">≥ 64.5 mm/day</span>
                </div>
                <div className="flex items-center justify-between bg-[#141824] p-1.5 rounded border border-[#1e2638]">
                  <span className="text-[#cbd5e1] flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#ef4444]" />
                    Very Heavy Rain:
                  </span>
                  <span className="font-mono text-white font-semibold">≥ 115.6 mm/day</span>
                </div>
                <div className="flex items-center justify-between bg-[#141824] p-1.5 rounded border border-[#1e2638]">
                  <span className="text-[#cbd5e1] flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#9333ea]" />
                    Extremely Heavy:
                  </span>
                  <span className="font-mono text-white font-semibold">≥ 204.5 mm/day</span>
                </div>
              </div>
            </div>

            {/* Section C: Map Layer Toggles & Observation Quality */}
            <div className="bg-[#10141e] border border-[#1e2638] rounded-md p-2.5 space-y-2">
              <div className="flex items-center justify-between border-b border-[#1e2638] pb-1.5">
                <span className="text-[10px] font-mono text-[#64748b] uppercase tracking-wider flex items-center gap-1">
                  <Layers className="w-3 h-3 text-[#00e5ff]" />
                  Cesium 3D Map Layers
                </span>
                <span className="text-[9px] font-mono text-[#94a3b8]">
                  {LAYER_OPTIONS.find((l) => l.id === activeLayer)?.badge || 'Active'}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-1">
                {LAYER_OPTIONS.map((layer) => {
                  const isLayerActive = activeLayer === layer.id;
                  return (
                    <button
                      key={layer.id}
                      type="button"
                      onClick={() => onSelectLayer?.(layer.id)}
                      className={`px-2 py-1 rounded text-[11px] font-medium text-left truncate transition-colors ${
                        isLayerActive
                          ? 'bg-[#00e5ff]/20 text-[#00e5ff] border border-[#00e5ff]/40'
                          : 'bg-[#141824] text-[#94a3b8] hover:text-white border border-[#1e2638]'
                      }`}
                    >
                      {layer.label}
                    </button>
                  );
                })}
              </div>

              {/* Observation Quality Slider */}
              <div className="pt-1 border-t border-[#1e2638]">
                <div className="flex justify-between items-center text-[10px] font-mono text-[#64748b] mb-1">
                  <span>Observation Cloud Filter</span>
                  <span className="text-white font-semibold">{satelliteMaxCloud}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="60"
                  step="5"
                  value={satelliteMaxCloud}
                  onChange={(e) => onChangeSatelliteMaxCloud(parseFloat(e.target.value))}
                  aria-label="Maximum satellite cloud filter percentage"
                  className="w-full accent-[#0284c7] h-1.5 bg-[#141824] rounded-lg cursor-pointer"
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
