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
  TrendingUp,
} from 'lucide-react';
import { DistrictForecast, WeatherRegimeType } from '@/lib/types';
import { WEATHER_REGIME_CONFIG } from '@/lib/constants';
import { formatNumber } from '@/lib/formatters';

interface DistrictForecastTableProps {
  districts?: DistrictForecast[] | null;
  selectedDistrictName?: string;
  onSelectDistrict: (districtName: string, stateName: string) => void;
}

type SortField =
  | 'district_name'
  | 'raw_nwp_rainfall_mm'
  | 'corrected_rainfall_mm'
  | 'correction_magnitude_mm'
  | 'heavy_probability_pct'
  | 'very_heavy_probability_pct'
  | 'ensemble_spread_mm';

export const DistrictForecastTable: React.FC<DistrictForecastTableProps> = ({
  districts = [],
  selectedDistrictName,
  onSelectDistrict,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<SortField>('corrected_rainfall_mm');
  const [sortAsc, setSortAsc] = useState(false);

  const fallbackDistricts: DistrictForecast[] = useMemo(
    () => [
      {
        district_name: 'Mumbai City',
        state_name: 'Maharashtra',
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
        uncertainty_category: 'MODERATE',
      },
      {
        district_name: 'Satara',
        state_name: 'Maharashtra',
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
        uncertainty_category: 'HIGH',
      },
      {
        district_name: 'Puri',
        state_name: 'Odisha',
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
        uncertainty_category: 'MODERATE',
      },
      {
        district_name: 'Nagpur',
        state_name: 'Maharashtra',
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
        uncertainty_category: 'LOW',
      },
      {
        district_name: 'East Khasi Hills',
        state_name: 'Meghalaya',
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
        uncertainty_category: 'HIGH',
      },
      {
        district_name: 'Ernakulam',
        state_name: 'Kerala',
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
        uncertainty_category: 'MODERATE',
      },
    ],
    []
  );

  const rawList = districts && districts.length > 0 ? districts : fallbackDistricts;

  // Search & Sorting Filter
  const filteredList = useMemo(() => {
    return rawList
      .filter(
        (d) =>
          d.district_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          d.state_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          d.primary_regime.toLowerCase().includes(searchTerm.toLowerCase())
      )
      .sort((a, b) => {
        let valA = a[sortField];
        let valB = b[sortField];
        if (typeof valA === 'string') {
          valA = (valA as string).toLowerCase();
          valB = (valB as string).toLowerCase();
        }
        if (valA < valB) return sortAsc ? -1 : 1;
        if (valA > valB) return sortAsc ? 1 : -1;
        return 0;
      });
  }, [rawList, searchTerm, sortField, sortAsc]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  return (
    <div className="bg-[#0b0e16] border border-[#1e2638] rounded-lg p-4 shadow-xl space-y-3.5">
      {/* Header & Search */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1e2638] pb-3">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-[#00e5ff]" />
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              District-Level Post-Processed Monsoon Forecasts
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#1e2638] text-[#00e5ff]">
                748 Administrative Districts
              </span>
            </h3>
            <p className="text-[10px] text-[#64748b] font-mono">
              Area-weighted mean precipitation, regime conditioning & calibrated probability tiers
            </p>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative min-w-[200px] max-w-xs w-full sm:w-auto">
          <Search className="w-3.5 h-3.5 text-[#64748b] absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search district, state, or regime..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-[#121622] border border-[#1e2638] focus:border-[#00e5ff] rounded py-1.5 pl-8 pr-3 text-xs font-mono text-white placeholder-[#64748b] outline-none transition-colors"
          />
        </div>
      </div>

      {/* Interactive Table */}
      <div className="overflow-x-auto max-h-[340px] overflow-y-auto">
        <table className="w-full text-left text-xs border-collapse font-mono">
          <thead className="sticky top-0 bg-[#0e121a] z-10 border-b border-[#1e2638] text-[10px] uppercase text-[#64748b]">
            <tr>
              <th
                onClick={() => handleSort('district_name')}
                className="py-2 px-2.5 font-medium cursor-pointer hover:text-white"
              >
                <div className="flex items-center gap-1">
                  District & State <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-2 px-2 font-medium">Dominant Regime</th>
              <th
                onClick={() => handleSort('raw_nwp_rainfall_mm')}
                className="py-2 px-2 font-medium text-right cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  Raw NWP <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort('corrected_rainfall_mm')}
                className="py-2 px-2 font-medium text-right cursor-pointer text-[#00e5ff] hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  AI Calibrated <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort('correction_magnitude_mm')}
                className="py-2 px-2 font-medium text-right cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  Bias Δ <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort('heavy_probability_pct')}
                className="py-2 px-2 font-medium text-right cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  P(≥64.5mm) <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort('very_heavy_probability_pct')}
                className="py-2 px-2 font-medium text-right cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  P(≥115.6mm) <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort('ensemble_spread_mm')}
                className="py-2 px-2 font-medium text-right cursor-pointer hover:text-white"
              >
                <div className="flex items-center justify-end gap-1">
                  Uncertainty <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-2 px-2 text-center font-medium">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e2638]/50">
            {filteredList.map((d, idx) => {
              const isSelected = selectedDistrictName === d.district_name;
              const regimeCfg = (WEATHER_REGIME_CONFIG as any)[d.primary_regime] || {
                label: d.primary_regime,
                color: '#00e5ff',
                bgColor: 'rgba(0,229,255,0.1)',
                borderColor: '#00e5ff',
              };

              const delta = d.correction_magnitude_mm;
              const isPositive = delta >= 0;

              return (
                <tr
                  key={idx}
                  onClick={() => onSelectDistrict(d.district_name, d.state_name)}
                  className={`cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-[#0284c7]/20 border-l-2 border-[#00e5ff]'
                      : 'hover:bg-[#121622]/80'
                  }`}
                >
                  <td className="py-2 px-2.5">
                    <div className="font-bold text-white flex items-center gap-1.5">
                      {d.district_name}
                      {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-[#00e5ff] animate-pulse" />}
                    </div>
                    <div className="text-[10px] text-[#64748b]">{d.state_name}</div>
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
                      {regimeCfg.label || d.primary_regime.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="py-2 px-2 text-right text-[#94a3b8]">
                    {formatNumber(d.raw_nwp_rainfall_mm, 1)} mm
                  </td>
                  <td className="py-2 px-2 text-right font-bold text-white">
                    {formatNumber(d.corrected_rainfall_mm, 1)} mm
                  </td>
                  <td
                    className={`py-2 px-2 text-right font-semibold ${
                      isPositive ? 'text-[#10b981]' : 'text-[#f59e0b]'
                    }`}
                  >
                    {isPositive ? `+${formatNumber(delta, 1)}` : formatNumber(delta, 1)} mm
                  </td>
                  <td className="py-2 px-2 text-right font-semibold text-[#00e5ff]">
                    {Math.round(d.heavy_probability_pct)}%
                  </td>
                  <td className="py-2 px-2 text-right text-[#cbd5e1]">
                    {Math.round(d.very_heavy_probability_pct)}%
                  </td>
                  <td className="py-2 px-2 text-right text-[#94a3b8]">
                    [{formatNumber(d.forecast_lower_bound_p10_mm, 0)}-{formatNumber(d.forecast_upper_bound_p90_mm, 0)} mm]
                  </td>
                  <td className="py-2 px-2 text-center">
                    <button
                      type="button"
                      className="p-1 rounded hover:bg-[#1e2638] text-[#00e5ff]"
                      title="Focus District on Cesium Globe"
                    >
                      <ChevronRight className="w-4 h-4" />
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
        <span>Showing {filteredList.length} district records</span>
        <span className="text-[#00e5ff]">
          Click any row to reposition 3D Cesium camera & update synoptic diagnostics
        </span>
      </div>
    </div>
  );
};
