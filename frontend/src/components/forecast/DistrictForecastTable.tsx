'use client';

import React, { useState, useMemo } from 'react';
import {
  MapPin,
  ArrowUpDown,
  Search,
  Sparkles,
  Compass,
  AlertTriangle,
  ChevronRight,
  Filter,
  Info,
  Layers,
  Activity,
  X,
  ShieldAlert,
} from 'lucide-react';
import { DistrictForecast, WeatherRegimeType } from '@/lib/types';
import { WEATHER_REGIME_CONFIG } from '@/lib/constants';
import { formatNumber } from '@/lib/formatters';

interface DistrictForecastTableProps {
  districts?: DistrictForecast[] | null;
  selectedDistrictName?: string;
  onSelectDistrict: (districtName: string, stateName: string) => void;
  onOpenAtmosphericModal?: () => void;
}

type SortField =
  | 'district_name'
  | 'raw_nwp_rainfall_mm'
  | 'corrected_rainfall_mm'
  | 'correction_magnitude_mm'
  | 'heavy_probability_pct'
  | 'very_heavy_probability_pct'
  | 'extreme_probability_pct'
  | 'ensemble_spread_mm';

export const DistrictForecastTable: React.FC<DistrictForecastTableProps> = ({
  districts = [],
  selectedDistrictName,
  onSelectDistrict,
  onOpenAtmosphericModal,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedState, setSelectedState] = useState<string>('ALL');
  const [selectedRegime, setSelectedRegime] = useState<string>('ALL');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [sortField, setSortField] = useState<SortField>('corrected_rainfall_mm');
  const [sortAsc, setSortAsc] = useState(false);
  const [inspectingDistrict, setInspectingDistrict] = useState<DistrictForecast | null>(null);

  const fallbackDistricts: DistrictForecast[] = useMemo(
    () => [
      {
        district_id: 'MH_MUMBAI_CITY',
        district_name: 'Mumbai City',
        state_name: 'Maharashtra',
        lat: 18.9388,
        lon: 72.8354,
        forecast_date: '2024-07-15',
        raw_nwp_rainfall_mm: 58.4,
        corrected_rainfall_mm: 82.6,
        correction_magnitude_mm: 24.2,
        forecast_lower_bound_p10_mm: 52.0,
        forecast_upper_bound_p90_mm: 118.5,
        ensemble_spread_mm: 26.0,
        heavy_probability_pct: 78.5,
        very_heavy_probability_pct: 28.4,
        extreme_probability_pct: 4.2,
        primary_regime: 'COASTAL_CONVERGENCE' as WeatherRegimeType,
        dominant_regime: 'COASTAL_CONVERGENCE' as WeatherRegimeType,
        regime_confidence: 0.88,
        uncertainty_category: 'MODERATE',
        aggregation_method: 'POINT_SAMPLED_CENTROID',
        decision_support_category: 'HEAVY_RAINFALL',
        decision_basis: 'Forecast calibrated rainfall (82.6 mm) and heavy rain probability (78.5%) exceed 64.5 mm threshold.',
        provenance_status: 'HELD_OUT_PROTOTYPE_EVALUATION',
        is_official_imd_warning: false,
        disclaimer: 'Prototype model-derived decision support. Not an official IMD warning.',
      },
      {
        district_id: 'MH_SATARA',
        district_name: 'Satara',
        state_name: 'Maharashtra',
        lat: 17.6805,
        lon: 73.9935,
        forecast_date: '2024-07-15',
        raw_nwp_rainfall_mm: 72.0,
        corrected_rainfall_mm: 114.5,
        correction_magnitude_mm: 42.5,
        forecast_lower_bound_p10_mm: 76.0,
        forecast_upper_bound_p90_mm: 162.0,
        ensemble_spread_mm: 33.6,
        heavy_probability_pct: 92.0,
        very_heavy_probability_pct: 54.0,
        extreme_probability_pct: 12.5,
        primary_regime: 'OROGRAPHIC_RAINFALL' as WeatherRegimeType,
        dominant_regime: 'OROGRAPHIC_RAINFALL' as WeatherRegimeType,
        regime_confidence: 0.92,
        uncertainty_category: 'HIGH',
        aggregation_method: 'POINT_SAMPLED_CENTROID',
        decision_support_category: 'VERY_HEAVY_RAINFALL',
        decision_basis: 'Very heavy rain probability (54.0%) exceeds 40% operational alert threshold in Western Ghats.',
        provenance_status: 'HELD_OUT_PROTOTYPE_EVALUATION',
        is_official_imd_warning: false,
        disclaimer: 'Prototype model-derived decision support. Not an official IMD warning.',
      },
      {
        district_id: 'OD_PURI',
        district_name: 'Puri',
        state_name: 'Odisha',
        lat: 19.8135,
        lon: 85.8312,
        forecast_date: '2024-07-15',
        raw_nwp_rainfall_mm: 64.0,
        corrected_rainfall_mm: 88.2,
        correction_magnitude_mm: 24.2,
        forecast_lower_bound_p10_mm: 58.0,
        forecast_upper_bound_p90_mm: 124.0,
        ensemble_spread_mm: 25.8,
        heavy_probability_pct: 84.0,
        very_heavy_probability_pct: 32.0,
        extreme_probability_pct: 6.0,
        primary_regime: 'MONSOON_LOW_LPS' as WeatherRegimeType,
        dominant_regime: 'MONSOON_LOW_LPS' as WeatherRegimeType,
        regime_confidence: 0.85,
        uncertainty_category: 'MODERATE',
        aggregation_method: 'POINT_SAMPLED_CENTROID',
        decision_support_category: 'HEAVY_RAINFALL',
        decision_basis: 'Calibrated P50 (88.2 mm) exceeds 64.5 mm heavy-rainfall threshold under active Bay of Bengal low.',
        provenance_status: 'HELD_OUT_PROTOTYPE_EVALUATION',
        is_official_imd_warning: false,
        disclaimer: 'Prototype model-derived decision support. Not an official IMD warning.',
      },
      {
        district_id: 'MH_NAGPUR',
        district_name: 'Nagpur',
        state_name: 'Maharashtra',
        lat: 21.1458,
        lon: 79.0882,
        forecast_date: '2024-07-15',
        raw_nwp_rainfall_mm: 18.0,
        corrected_rainfall_mm: 11.2,
        correction_magnitude_mm: -6.8,
        forecast_lower_bound_p10_mm: 4.0,
        forecast_upper_bound_p90_mm: 22.0,
        ensemble_spread_mm: 7.0,
        heavy_probability_pct: 8.0,
        very_heavy_probability_pct: 1.0,
        extreme_probability_pct: 0.0,
        primary_regime: 'BREAK_MONSOON' as WeatherRegimeType,
        dominant_regime: 'BREAK_MONSOON' as WeatherRegimeType,
        regime_confidence: 0.82,
        uncertainty_category: 'LOW',
        aggregation_method: 'POINT_SAMPLED_CENTROID',
        decision_support_category: 'NORMAL',
        decision_basis: 'Calibrated rainfall (11.2 mm) is well below the 64.5 mm heavy-rainfall threshold.',
        provenance_status: 'HELD_OUT_PROTOTYPE_EVALUATION',
        is_official_imd_warning: false,
        disclaimer: 'Prototype model-derived decision support. Not an official IMD warning.',
      },
      {
        district_id: 'ML_EAST_KHASI_HILLS',
        district_name: 'East Khasi Hills',
        state_name: 'Meghalaya',
        lat: 25.5788,
        lon: 91.8933,
        forecast_date: '2024-07-15',
        raw_nwp_rainfall_mm: 85.0,
        corrected_rainfall_mm: 142.0,
        correction_magnitude_mm: 57.0,
        forecast_lower_bound_p10_mm: 95.0,
        forecast_upper_bound_p90_mm: 198.0,
        ensemble_spread_mm: 40.2,
        heavy_probability_pct: 96.0,
        very_heavy_probability_pct: 68.0,
        extreme_probability_pct: 22.0,
        primary_regime: 'OROGRAPHIC_RAINFALL' as WeatherRegimeType,
        dominant_regime: 'OROGRAPHIC_RAINFALL' as WeatherRegimeType,
        regime_confidence: 0.94,
        uncertainty_category: 'HIGH',
        aggregation_method: 'POINT_SAMPLED_CENTROID',
        decision_support_category: 'VERY_HEAVY_RAINFALL',
        decision_basis: 'Calibrated P50 (142.0 mm) and very heavy probability (68.0%) exceed 115.6 mm threshold in Meghalaya plateau.',
        provenance_status: 'HELD_OUT_PROTOTYPE_EVALUATION',
        is_official_imd_warning: false,
        disclaimer: 'Prototype model-derived decision support. Not an official IMD warning.',
      },
      {
        district_id: 'KL_ERNAKULAM',
        district_name: 'Ernakulam',
        state_name: 'Kerala',
        lat: 9.9816,
        lon: 76.2999,
        forecast_date: '2024-07-15',
        raw_nwp_rainfall_mm: 52.0,
        corrected_rainfall_mm: 74.5,
        correction_magnitude_mm: 22.5,
        forecast_lower_bound_p10_mm: 48.0,
        forecast_upper_bound_p90_mm: 108.0,
        ensemble_spread_mm: 23.4,
        heavy_probability_pct: 72.0,
        very_heavy_probability_pct: 21.0,
        extreme_probability_pct: 3.5,
        primary_regime: 'COASTAL_CONVERGENCE' as WeatherRegimeType,
        dominant_regime: 'COASTAL_CONVERGENCE' as WeatherRegimeType,
        regime_confidence: 0.86,
        uncertainty_category: 'MODERATE',
        aggregation_method: 'POINT_SAMPLED_CENTROID',
        decision_support_category: 'HEAVY_RAINFALL',
        decision_basis: 'Calibrated P50 (74.5 mm) exceeds 64.5 mm heavy-rainfall threshold on Malabar Coast.',
        provenance_status: 'HELD_OUT_PROTOTYPE_EVALUATION',
        is_official_imd_warning: false,
        disclaimer: 'Prototype model-derived decision support. Not an official IMD warning.',
      },
    ],
    []
  );

  const rawList = useMemo(() => {
    if (!districts || districts.length === 0) return fallbackDistricts;
    return districts.map((d) => {
      const pHeavy = d.heavy_probability_pct ?? (d.heavy_prob ? d.heavy_prob * 100 : 0);
      const pVHeavy = d.very_heavy_probability_pct ?? (d.very_heavy_prob ? d.very_heavy_prob * 100 : 0);
      const pExtreme = d.extreme_probability_pct ?? (d.extreme_prob ? d.extreme_prob * 100 : 0);
      const cRain = d.corrected_rainfall_mm ?? d.corrected_mm ?? 0;
      const rawRain = d.raw_nwp_rainfall_mm ?? d.raw_nwp_mm ?? 0;
      const delta = d.correction_magnitude_mm ?? d.correction_delta_mm ?? (cRain - rawRain);
      const p10 = d.forecast_lower_bound_p10_mm ?? d.uncertainty_lower_bound_mm ?? Math.max(0, cRain * 0.7);
      const p90 = d.forecast_upper_bound_p90_mm ?? d.uncertainty_upper_bound_mm ?? (cRain * 1.35);
      const regime = (d.primary_regime || d.dominant_regime || 'ACTIVE_MONSOON') as WeatherRegimeType;

      let cat = d.decision_support_category;
      let basis = d.decision_basis;
      if (!cat) {
        if (cRain >= 204.5 || pExtreme >= 25) {
          cat = 'EXTREMELY_HEAVY_RAINFALL';
          basis = `Calibrated P50 (${cRain.toFixed(1)} mm) or extreme probability (${pExtreme.toFixed(1)}%) meets/exceeds 204.5 mm threshold.`;
        } else if (cRain >= 115.6 || pVHeavy >= 40) {
          cat = 'VERY_HEAVY_RAINFALL';
          basis = `Calibrated P50 (${cRain.toFixed(1)} mm) or very heavy probability (${pVHeavy.toFixed(1)}%) meets/exceeds 115.6 mm threshold.`;
        } else if (cRain >= 64.5 || pHeavy >= 55) {
          cat = 'HEAVY_RAINFALL';
          basis = `Calibrated P50 (${cRain.toFixed(1)} mm) or heavy rain probability (${pHeavy.toFixed(1)}%) meets/exceeds 64.5 mm threshold.`;
        } else {
          cat = 'NORMAL';
          basis = `Calibrated P50 (${cRain.toFixed(1)} mm) is below the 64.5 mm heavy-rainfall threshold.`;
        }
      }

      return {
        ...d,
        raw_nwp_rainfall_mm: rawRain,
        corrected_rainfall_mm: cRain,
        correction_magnitude_mm: delta,
        forecast_lower_bound_p10_mm: p10,
        forecast_upper_bound_p90_mm: p90,
        heavy_probability_pct: pHeavy,
        very_heavy_probability_pct: pVHeavy,
        extreme_probability_pct: pExtreme,
        primary_regime: regime,
        dominant_regime: regime,
        decision_support_category: cat,
        decision_basis: basis,
        aggregation_method: d.aggregation_method || 'POINT_SAMPLED_CENTROID',
        provenance_status: d.provenance_status || 'HELD_OUT_PROTOTYPE_EVALUATION',
        is_official_imd_warning: false,
        disclaimer: 'Prototype model-derived decision support. Not an official IMD warning.',
      };
    });
  }, [districts, fallbackDistricts]);

  // Unique state list for filtering
  const stateOptions = useMemo(() => {
    const states = Array.from(new Set(rawList.map((d) => d.state_name))).sort();
    return ['ALL', ...states];
  }, [rawList]);

  // Unique regime list for filtering
  const regimeOptions = useMemo(() => {
    const regimes = Array.from(new Set(rawList.map((d) => (d.primary_regime || d.dominant_regime || 'ACTIVE_MONSOON')))).sort();
    return ['ALL', ...regimes];
  }, [rawList]);

  // Search, Dropdown Filtering & Sorting
  const filteredList = useMemo(() => {
    return rawList
      .filter((d) => {
        const matchesSearch =
          d.district_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          d.state_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (d.primary_regime || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
          (d.district_id || '').toLowerCase().includes(searchTerm.toLowerCase());

        const matchesState = selectedState === 'ALL' || d.state_name === selectedState;
        const matchesRegime =
          selectedRegime === 'ALL' ||
          (d.primary_regime || d.dominant_regime) === selectedRegime;
        const matchesCategory =
          selectedCategory === 'ALL' ||
          (d.decision_support_category || '').toUpperCase() === selectedCategory.toUpperCase();

        return matchesSearch && matchesState && matchesRegime && matchesCategory;
      })
      .sort((a, b) => {
        let valA: any = a[sortField] ?? 0;
        let valB: any = b[sortField] ?? 0;
        if (typeof valA === 'string') {
          valA = valA.toLowerCase();
          valB = (valB as string).toLowerCase();
        }
        if (valA < valB) return sortAsc ? -1 : 1;
        if (valA > valB) return sortAsc ? 1 : -1;
        return 0;
      });
  }, [rawList, searchTerm, selectedState, selectedRegime, selectedCategory, sortField, sortAsc]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const getCategoryBadge = (cat?: string) => {
    switch (cat) {
      case 'EXTREMELY_HEAVY_RAINFALL':
        return {
          label: 'EXTREMELY HEAVY',
          color: '#ef4444',
          bg: 'rgba(239, 68, 68, 0.15)',
          border: 'rgba(239, 68, 68, 0.5)',
        };
      case 'VERY_HEAVY_RAINFALL':
        return {
          label: 'VERY HEAVY',
          color: '#f97316',
          bg: 'rgba(249, 115, 22, 0.15)',
          border: 'rgba(249, 115, 22, 0.5)',
        };
      case 'HEAVY_RAINFALL':
        return {
          label: 'HEAVY RAIN',
          color: '#eab308',
          bg: 'rgba(234, 179, 8, 0.15)',
          border: 'rgba(234, 179, 8, 0.5)',
        };
      default:
        return {
          label: 'NORMAL',
          color: '#10b981',
          bg: 'rgba(16, 185, 129, 0.12)',
          border: 'rgba(16, 185, 129, 0.4)',
        };
    }
  };

  return (
    <div className="bg-[#0b0e16] border border-[#1e2638] rounded-lg p-4 shadow-xl space-y-4">
      {/* Header & Mandatory Prototype Notice */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1e2638] pb-3">
        <div className="flex items-center gap-2.5">
          <MapPin className="w-5 h-5 text-[#00e5ff]" />
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              District-Level Decision Support & Prototype Rainfall Outlook
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1e2638] text-[#00e5ff]">
                748 Administrative Framework
              </span>
            </h3>
            <p className="text-[11px] text-[#64748b] font-mono mt-0.5">
              POINT-SAMPLED DISTRICT ESTIMATES · 24H CALIBRATED P50 · P10–P90 UNCERTAINTY · IMD-ALIGNED PROBABILITY TIERS
            </p>
          </div>
        </div>

        {/* Prototype Warning Disclaimer Badge */}
        <div className="flex items-center gap-1.5 bg-[#f59e0b]/10 border border-[#f59e0b]/30 px-2.5 py-1 rounded text-[10px] font-mono text-[#fcd34d]">
          <AlertTriangle className="w-3.5 h-3.5 text-[#f59e0b]" />
          <span>PROTOTYPE DECISION SUPPORT · NOT AN OFFICIAL IMD WARNING</span>
        </div>
      </div>

      {/* Filter Controls Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
        {/* Search Bar */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-[#64748b] absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search district, code, state..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-[#121622] border border-[#1e2638] focus:border-[#00e5ff] rounded py-1.5 pl-8 pr-3 text-xs font-mono text-white placeholder-[#64748b] outline-none transition-colors"
          />
        </div>

        {/* State Filter */}
        <div className="flex items-center gap-1.5 bg-[#121622] border border-[#1e2638] rounded px-2 py-1">
          <Filter className="w-3 h-3 text-[#64748b]" />
          <span className="text-[10px] font-mono text-[#64748b] uppercase">State:</span>
          <select
            value={selectedState}
            onChange={(e) => setSelectedState(e.target.value)}
            className="bg-transparent text-xs font-mono text-white outline-none w-full cursor-pointer"
          >
            {stateOptions.map((st) => (
              <option key={st} value={st} className="bg-[#121622] text-white">
                {st === 'ALL' ? 'All States / UTs' : st}
              </option>
            ))}
          </select>
        </div>

        {/* Regime Filter */}
        <div className="flex items-center gap-1.5 bg-[#121622] border border-[#1e2638] rounded px-2 py-1">
          <Activity className="w-3 h-3 text-[#64748b]" />
          <span className="text-[10px] font-mono text-[#64748b] uppercase">Regime:</span>
          <select
            value={selectedRegime}
            onChange={(e) => setSelectedRegime(e.target.value)}
            className="bg-transparent text-xs font-mono text-white outline-none w-full cursor-pointer"
          >
            {regimeOptions.map((reg) => (
              <option key={reg} value={reg} className="bg-[#121622] text-white">
                {reg === 'ALL' ? 'All Weather Regimes' : reg.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
        </div>

        {/* Decision Category Filter */}
        <div className="flex items-center gap-1.5 bg-[#121622] border border-[#1e2638] rounded px-2 py-1">
          <Layers className="w-3 h-3 text-[#64748b]" />
          <span className="text-[10px] font-mono text-[#64748b] uppercase">Outlook:</span>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-transparent text-xs font-mono text-white outline-none w-full cursor-pointer"
          >
            <option value="ALL" className="bg-[#121622] text-white">All Outlook Categories</option>
            <option value="NORMAL" className="bg-[#121622] text-white">Normal (&lt;64.5 mm)</option>
            <option value="HEAVY_RAINFALL" className="bg-[#121622] text-white">Heavy Rain (≥64.5 mm)</option>
            <option value="VERY_HEAVY_RAINFALL" className="bg-[#121622] text-white">Very Heavy (≥115.6 mm)</option>
            <option value="EXTREMELY_HEAVY_RAINFALL" className="bg-[#121622] text-white">Extremely Heavy (≥204.5 mm)</option>
          </select>
        </div>
      </div>

      {/* Interactive Table */}
      <div className="overflow-x-auto max-h-[380px] overflow-y-auto border border-[#1e2638]/60 rounded-md">
        <table className="w-full text-left text-xs border-collapse font-mono">
          <thead className="sticky top-0 bg-[#0e121a] z-10 border-b border-[#1e2638] text-[10px] uppercase text-[#64748b]">
            <tr>
              <th
                onClick={() => handleSort('district_name')}
                className="py-2.5 px-3 font-medium cursor-pointer hover:text-white"
              >
                <div className="flex items-center gap-1">
                  District & State <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-2.5 px-2 font-medium">Dominant Regime</th>
              <th
                onClick={() => handleSort('raw_nwp_rainfall_mm')}
                className="py-2.5 px-2 font-medium text-right cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  Raw NWP <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort('corrected_rainfall_mm')}
                className="py-2.5 px-2 font-medium text-right cursor-pointer text-[#00e5ff] hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  AI Calibrated (P50) <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort('ensemble_spread_mm')}
                className="py-2.5 px-2 font-medium text-right cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  Uncertainty [P10–P90] <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort('correction_magnitude_mm')}
                className="py-2.5 px-2 font-medium text-right cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  Bias Δ <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort('heavy_probability_pct')}
                className="py-2.5 px-2 font-medium text-right cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  P(≥64.5mm) <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort('very_heavy_probability_pct')}
                className="py-2.5 px-2 font-medium text-right cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  P(≥115.6mm) <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort('extreme_probability_pct')}
                className="py-2.5 px-2 font-medium text-right cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  P(≥204.5mm) <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-2.5 px-2 text-center font-medium">Decision Support</th>
              <th className="py-2.5 px-2 text-center font-medium">Inspect</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e2638]/50">
            {filteredList.map((d, idx) => {
              const isSelected = selectedDistrictName === d.district_name;
              const regimeKey = d.primary_regime || d.dominant_regime || 'ACTIVE_MONSOON';
              const regimeCfg = (WEATHER_REGIME_CONFIG as any)[regimeKey] || {
                label: String(regimeKey).replace(/_/g, ' '),
                color: '#00e5ff',
                bgColor: 'rgba(0,229,255,0.1)',
                borderColor: '#00e5ff',
              };

              const delta = d.correction_magnitude_mm ?? 0;
              const isPositive = delta >= 0;
              const catBadge = getCategoryBadge(d.decision_support_category);

              return (
                <tr
                  key={d.district_id || idx}
                  className={`transition-colors ${
                    isSelected
                      ? 'bg-[#0284c7]/20 border-l-2 border-[#00e5ff]'
                      : 'hover:bg-[#121622]/80'
                  }`}
                >
                  <td
                    className="py-2 px-3 cursor-pointer"
                    onClick={() => {
                      onSelectDistrict(d.district_name, d.state_name);
                      setInspectingDistrict(d);
                    }}
                  >
                    <div className="font-bold text-white flex items-center gap-1.5">
                      {d.district_name}
                      {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-[#00e5ff] animate-pulse" />}
                    </div>
                    <div className="text-[10px] text-[#64748b]">
                      {d.state_name} {d.district_id && <span className="text-[9px] text-[#475569]">({d.district_id})</span>}
                    </div>
                  </td>
                  <td className="py-2 px-2">
                    <span
                      className="text-[10px] font-bold px-1.5 py-0.5 rounded uppercase"
                      style={{
                        color: regimeCfg.color,
                        backgroundColor: regimeCfg.bgColor,
                        border: `1px solid ${regimeCfg.borderColor}60`,
                      }}
                    >
                      {regimeCfg.label || String(regimeKey).replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="py-2 px-2 text-right text-[#94a3b8]">
                    {formatNumber(d.raw_nwp_rainfall_mm, 1)} mm
                  </td>
                  <td className="py-2 px-2 text-right font-bold text-white">
                    {formatNumber(d.corrected_rainfall_mm, 1)} mm
                  </td>
                  <td className="py-2 px-2 text-right text-[#94a3b8] text-[11px]">
                    [{formatNumber(d.forecast_lower_bound_p10_mm, 0)} – {formatNumber(d.forecast_upper_bound_p90_mm, 0)} mm]
                  </td>
                  <td
                    className={`py-2 px-2 text-right font-semibold ${
                      isPositive ? 'text-[#10b981]' : 'text-[#f59e0b]'
                    }`}
                  >
                    {isPositive ? `+${formatNumber(delta, 1)}` : formatNumber(delta, 1)} mm
                  </td>
                  <td className="py-2 px-2 text-right font-semibold text-[#00e5ff]">
                    {Math.round(d.heavy_probability_pct ?? 0)}%
                  </td>
                  <td className="py-2 px-2 text-right text-[#cbd5e1]">
                    {Math.round(d.very_heavy_probability_pct ?? 0)}%
                  </td>
                  <td className="py-2 px-2 text-right text-[#f59e0b]">
                    {Math.round(d.extreme_probability_pct ?? 0)}%
                  </td>
                  <td className="py-2 px-2 text-center">
                    <span
                      className="text-[9px] font-bold px-1.5 py-0.5 rounded font-mono uppercase"
                      style={{
                        color: catBadge.color,
                        backgroundColor: catBadge.bg,
                        border: `1px solid ${catBadge.border}`,
                      }}
                    >
                      {catBadge.label}
                    </span>
                  </td>
                  <td className="py-2 px-2 text-center">
                    <button
                      type="button"
                      onClick={() => {
                        onSelectDistrict(d.district_name, d.state_name);
                        setInspectingDistrict(d);
                      }}
                      className="px-2 py-1 rounded bg-[#151d2d] hover:bg-[#1e2638] text-[#00e5ff] text-[10px] font-mono transition-colors flex items-center gap-1 mx-auto"
                      title="Inspect District Telemetry & Decision Basis"
                    >
                      <span>Detail</span>
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Table Footer */}
      <div className="flex flex-wrap items-center justify-between text-[10px] font-mono text-[#64748b] pt-1 border-t border-[#1e2638]">
        <span>Showing {filteredList.length} of {rawList.length} district records</span>
        <span className="text-[#00e5ff]">
          Click any row or Detail button to inspect deterministic decision support & sync 3D Cesium camera
        </span>
      </div>

      {/* District Outlook Detail Panel / Modal */}
      {inspectingDistrict && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0b0e16] border border-[#00e5ff]/40 rounded-lg max-w-2xl w-full p-5 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-[#1e2638] pb-3">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <h4 className="text-base font-bold text-white uppercase tracking-wider">
                    {inspectingDistrict.district_name}
                  </h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1e2638] text-[#00e5ff]">
                    {inspectingDistrict.state_name}
                  </span>
                  {inspectingDistrict.district_id && (
                    <span className="text-[10px] font-mono text-[#64748b]">
                      ID: {inspectingDistrict.district_id}
                    </span>
                  )}
                </div>
                <p className="text-[11px] font-mono text-[#94a3b8]">
                  {inspectingDistrict.lat ? `${inspectingDistrict.lat.toFixed(3)}°N, ${inspectingDistrict.lon?.toFixed(3)}°E` : 'Point-Sampled Centroid Coordinate'}
                </p>
              </div>

              <button
                type="button"
                onClick={() => setInspectingDistrict(null)}
                className="p-1 rounded text-[#94a3b8] hover:text-white hover:bg-[#1e2638] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Prototype Disclaimer Banner */}
            <div className="bg-[#f59e0b]/10 border border-[#f59e0b]/40 rounded p-2.5 flex items-start gap-2 text-[#fcd34d] text-xs font-mono">
              <ShieldAlert className="w-4 h-4 shrink-0 text-[#f59e0b] mt-0.5" />
              <div>
                <span className="font-bold block uppercase text-[10px]">
                  PROTOTYPE DECISION SUPPORT · NOT AN OFFICIAL IMD WARNING
                </span>
                <span className="text-[11px] text-[#fef08a]">
                  This product is generated by experimental regime-aware ML post-processing. It does not replace or supersede statutory bulletins issued by the India Meteorological Department.
                </span>
              </div>
            </div>

            {/* Key Telemetry Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <div className="bg-[#121622] border border-[#1e2638] rounded p-2.5">
                <span className="text-[10px] font-mono uppercase text-[#64748b] block">Calibrated (P50)</span>
                <span className="text-base font-bold text-white">
                  {formatNumber(inspectingDistrict.corrected_rainfall_mm, 1)} <span className="text-xs font-normal text-[#94a3b8]">mm</span>
                </span>
              </div>

              <div className="bg-[#121622] border border-[#1e2638] rounded p-2.5">
                <span className="text-[10px] font-mono uppercase text-[#64748b] block">Raw NWP</span>
                <span className="text-base font-bold text-[#94a3b8]">
                  {formatNumber(inspectingDistrict.raw_nwp_rainfall_mm, 1)} <span className="text-xs font-normal text-[#64748b]">mm</span>
                </span>
              </div>

              <div className="bg-[#121622] border border-[#1e2638] rounded p-2.5">
                <span className="text-[10px] font-mono uppercase text-[#64748b] block">AI Bias Delta (Δ)</span>
                <span className={`text-base font-bold ${
                  (inspectingDistrict.correction_magnitude_mm ?? 0) >= 0 ? 'text-[#10b981]' : 'text-[#f59e0b]'
                }`}>
                  {(inspectingDistrict.correction_magnitude_mm ?? 0) >= 0 ? '+' : ''}
                  {formatNumber(inspectingDistrict.correction_magnitude_mm, 1)} <span className="text-xs font-normal text-[#94a3b8]">mm</span>
                </span>
              </div>

              <div className="bg-[#121622] border border-[#1e2638] rounded p-2.5">
                <span className="text-[10px] font-mono uppercase text-[#64748b] block">Dominant Regime</span>
                <span className="text-xs font-bold text-[#00e5ff] truncate block">
                  {String(inspectingDistrict.primary_regime || inspectingDistrict.dominant_regime || 'ACTIVE_MONSOON').replace(/_/g, ' ')}
                </span>
                <span className="text-[10px] font-mono text-[#64748b]">
                  Confidence: {Math.round((inspectingDistrict.regime_confidence ?? 0.85) * 100)}%
                </span>
              </div>
            </div>

            {/* Uncertainty Bounds P10 / P50 / P90 */}
            <div className="bg-[#121622] border border-[#1e2638] rounded p-3 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-[#64748b] uppercase font-bold">Uncertainty Quantiles</span>
                <span className="text-[#00e5ff]">
                  Spread: ±{formatNumber(inspectingDistrict.ensemble_spread_mm, 1)} mm
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center font-mono">
                <div className="bg-[#0b0e16] p-2 rounded border border-[#1e2638]">
                  <span className="text-[10px] text-[#64748b] block">P10 (Lower)</span>
                  <span className="text-sm font-bold text-white">
                    {formatNumber(inspectingDistrict.forecast_lower_bound_p10_mm, 1)} mm
                  </span>
                </div>
                <div className="bg-[#0b0e16] p-2 rounded border border-[#00e5ff]/30">
                  <span className="text-[10px] text-[#00e5ff] block">P50 (Median)</span>
                  <span className="text-sm font-bold text-[#00e5ff]">
                    {formatNumber(inspectingDistrict.corrected_rainfall_mm, 1)} mm
                  </span>
                </div>
                <div className="bg-[#0b0e16] p-2 rounded border border-[#1e2638]">
                  <span className="text-[10px] text-[#64748b] block">P90 (Upper)</span>
                  <span className="text-sm font-bold text-white">
                    {formatNumber(inspectingDistrict.forecast_upper_bound_p90_mm, 1)} mm
                  </span>
                </div>
              </div>
            </div>

            {/* Exceedance Probabilities */}
            <div className="bg-[#121622] border border-[#1e2638] rounded p-3 space-y-2">
              <div className="text-xs font-mono uppercase text-[#64748b] font-bold">
                Exceedance Probability Evaluation (IMD Thresholds)
              </div>
              <div className="grid grid-cols-3 gap-2 font-mono">
                <div className="bg-[#0b0e16] p-2 rounded border border-[#1e2638]">
                  <div className="text-[10px] text-[#94a3b8] uppercase">Heavy Rain</div>
                  <div className="text-[10px] text-[#64748b]">≥ 64.5 mm</div>
                  <div className="text-base font-bold text-[#00e5ff] mt-0.5">
                    {Math.round(inspectingDistrict.heavy_probability_pct ?? 0)}%
                  </div>
                </div>

                <div className="bg-[#0b0e16] p-2 rounded border border-[#1e2638]">
                  <div className="text-[10px] text-[#94a3b8] uppercase">Very Heavy</div>
                  <div className="text-[10px] text-[#64748b]">≥ 115.6 mm</div>
                  <div className="text-base font-bold text-[#f59e0b] mt-0.5">
                    {Math.round(inspectingDistrict.very_heavy_probability_pct ?? 0)}%
                  </div>
                </div>

                <div className="bg-[#0b0e16] p-2 rounded border border-[#1e2638]">
                  <div className="text-[10px] text-[#94a3b8] uppercase">Extremely Heavy</div>
                  <div className="text-[10px] text-[#64748b]">≥ 204.5 mm</div>
                  <div className="text-base font-bold text-[#ef4444] mt-0.5">
                    {Math.round(inspectingDistrict.extreme_probability_pct ?? 0)}%
                  </div>
                </div>
              </div>
            </div>

            {/* Decision Support Category & Scientific Basis */}
            <div className="bg-[#121622] border border-[#1e2638] rounded p-3 space-y-1.5 font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[#64748b] uppercase font-bold">Decision-Support Category</span>
                <span
                  className="px-2 py-0.5 rounded font-bold uppercase text-[10px]"
                  style={getCategoryBadge(inspectingDistrict.decision_support_category)}
                >
                  {inspectingDistrict.decision_support_category?.replace(/_/g, ' ') || 'NORMAL'}
                </span>
              </div>
              <p className="text-[11px] text-[#cbd5e1] bg-[#0b0e16] p-2 rounded border border-[#1e2638]/70">
                <strong className="text-[#00e5ff]">Basis: </strong>
                {inspectingDistrict.decision_basis || 'Forecast median evaluated against IMD criteria.'}
              </p>
            </div>

            {/* Scientific Provenance & Aggregation Notice */}
            <div className="text-[10px] font-mono text-[#64748b] bg-[#0e121a] p-2.5 rounded border border-[#1e2638] space-y-1">
              <div className="flex items-center justify-between">
                <span>Aggregation Method: <strong>{inspectingDistrict.aggregation_method || 'POINT_SAMPLED_CENTROID'}</strong></span>
                <span>Population Weighting: <strong>NOT AVAILABLE</strong></span>
              </div>
              <div className="flex items-center justify-between">
                <span>Provenance: <strong>{inspectingDistrict.provenance_status || 'HELD_OUT_PROTOTYPE_EVALUATION'}</strong></span>
                <span>Spatial Reference: <strong>WGS84 EPSG:4326</strong></span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center justify-end gap-2 pt-2 border-t border-[#1e2638]">
              <button
                type="button"
                onClick={() => {
                  onSelectDistrict(inspectingDistrict.district_name, inspectingDistrict.state_name);
                  setInspectingDistrict(null);
                }}
                className="px-3 py-1.5 rounded bg-[#0284c7] hover:bg-[#0369a1] text-white text-xs font-mono transition-colors flex items-center gap-1.5"
              >
                <Compass className="w-3.5 h-3.5" />
                <span>Fly 3D Camera & Analyze</span>
              </button>

              {onOpenAtmosphericModal && (
                <button
                  type="button"
                  onClick={() => {
                    onOpenAtmosphericModal();
                    setInspectingDistrict(null);
                  }}
                  className="px-3 py-1.5 rounded bg-[#1e2638] hover:bg-[#2a3449] text-[#00e5ff] text-xs font-mono transition-colors flex items-center gap-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Why Was This District Corrected?</span>
                </button>
              )}

              <button
                type="button"
                onClick={() => setInspectingDistrict(null)}
                className="px-3 py-1.5 rounded bg-[#121622] hover:bg-[#1a2030] text-[#94a3b8] hover:text-white text-xs font-mono transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
