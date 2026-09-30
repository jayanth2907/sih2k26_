import { PresetLocation, WeatherRegimeType } from './types';

export const PRESET_LOCATIONS: PresetLocation[] = [
  {
    id: 'mumbai',
    name: 'Mumbai (Konkan Coast)',
    state: 'Maharashtra',
    latitude: 19.0760,
    longitude: 72.8777,
    defaultZoomAltitude: 22000,
    regimeHint: 'COASTAL_CONVERGENCE',
  },
  {
    id: 'mahabaleshwar',
    name: 'Mahabaleshwar (Western Ghats Core)',
    state: 'Maharashtra',
    latitude: 17.9237,
    longitude: 73.6586,
    defaultZoomAltitude: 20000,
    regimeHint: 'OROGRAPHIC_RAINFALL',
  },
  {
    id: 'nagpur',
    name: 'Nagpur (Central India LPS Core)',
    state: 'Maharashtra',
    latitude: 21.1458,
    longitude: 79.0882,
    defaultZoomAltitude: 25000,
    regimeHint: 'MONSOON_LOW_LPS',
  },
  {
    id: 'cherrapunji',
    name: 'Cherrapunji (Northeast Orographic)',
    state: 'Meghalaya',
    latitude: 25.2702,
    longitude: 91.7323,
    defaultZoomAltitude: 22000,
    regimeHint: 'OROGRAPHIC_RAINFALL',
  },
  {
    id: 'chennai',
    name: 'Chennai (Coromandel Coast)',
    state: 'Tamil Nadu',
    latitude: 13.0827,
    longitude: 80.2707,
    defaultZoomAltitude: 22000,
    regimeHint: 'COASTAL_CONVERGENCE',
  },
  {
    id: 'srinagar',
    name: 'Srinagar (NW Himalayas WD)',
    state: 'Jammu and Kashmir',
    latitude: 34.0837,
    longitude: 74.7973,
    defaultZoomAltitude: 25000,
    regimeHint: 'WESTERN_DISTURBANCE',
  },
];

export const WEATHER_REGIME_CONFIG: Record<
  WeatherRegimeType,
  { label: string; shortCode: string; color: string; bgColor: string; borderColor: string; description: string }
> = {
  ACTIVE_MONSOON: {
    label: 'Active Monsoon',
    shortCode: 'ACT-MON',
    color: '#00E5FF',
    bgColor: 'rgba(0, 229, 255, 0.12)',
    borderColor: 'rgba(0, 229, 255, 0.40)',
    description: 'Vigorous cross-equatorial monsoon low-level jet (>28 kts), southern monsoon trough position, widespread convective rain.',
  },
  BREAK_MONSOON: {
    label: 'Break Monsoon',
    shortCode: 'BRK-MON',
    color: '#F59E0B',
    bgColor: 'rgba(245, 158, 11, 0.12)',
    borderColor: 'rgba(245, 158, 11, 0.40)',
    description: 'Monsoon trough shifted north to Himalayan foothills. Suppressed peninsular rainfall with concentrated Himalayan foothill precipitation.',
  },
  MONSOON_LOW_LPS: {
    label: 'Monsoon Low / LPS',
    shortCode: 'LPS-DEP',
    color: '#A855F7',
    bgColor: 'rgba(168, 85, 247, 0.12)',
    borderColor: 'rgba(168, 85, 247, 0.40)',
    description: 'Synoptic cyclonic vortex / Low Pressure System from Bay of Bengal with intense mid-tropospheric cyclonic vorticity.',
  },
  COASTAL_CONVERGENCE: {
    label: 'Coastal Convergence',
    shortCode: 'CST-CNV',
    color: '#3B82F6',
    bgColor: 'rgba(59, 130, 246, 0.12)',
    borderColor: 'rgba(59, 130, 246, 0.40)',
    description: 'Land-sea thermal contrast and frictional convergence along coastal boundaries amplifying localized convective cells.',
  },
  OROGRAPHIC_RAINFALL: {
    label: 'Orographic Lifting',
    shortCode: 'ORO-LFT',
    color: '#10B981',
    bgColor: 'rgba(16, 185, 129, 0.12)',
    borderColor: 'rgba(16, 185, 129, 0.40)',
    description: 'Strong moist Low-Level Jet forced perpendicularly up steep terrain barriers (Western Ghats / Khasi Hills).',
  },
  WESTERN_DISTURBANCE: {
    label: 'Western Disturbance',
    shortCode: 'WST-DST',
    color: '#EC4899',
    bgColor: 'rgba(236, 72, 153, 0.12)',
    borderColor: 'rgba(236, 72, 153, 0.40)',
    description: 'Extra-tropical mid-latitude synoptic trough embedded in subtropical westerlies producing precipitation in North-West India.',
  },
  NEUTRAL: {
    label: 'Neutral / Transitional',
    shortCode: 'NEU-TRS',
    color: '#94A3B8',
    bgColor: 'rgba(148, 163, 184, 0.12)',
    borderColor: 'rgba(148, 163, 184, 0.40)',
    description: 'Weak synoptic forcing; localized diurnal convective heating dominates.',
  },
};

export const POST_PROCESSING_PRODUCTS = [
  { id: 'raw_nwp', name: 'Raw NWP', color: '#94A3B8', tag: 'Baseline' },
  { id: 'quantile_mapping', name: 'Quantile Mapping (EQM)', color: '#06B6D4', tag: 'Statistical' },
  { id: 'global_ml', name: 'Global ML Correction', color: '#F59E0B', tag: 'Static AI' },
  { id: 'regime_aware_ml', name: 'Regime-Aware AI', color: '#00E5FF', tag: 'MoES PS26080' },
];

export const RADAR_DBZ_THRESHOLDS = [
  { max: 20, label: '< 20 dBZ', description: 'Light / Mist / Clear Air', color: '#10b981' },
  { max: 35, label: '20 - 35 dBZ', description: 'Moderate Rain', color: '#06b6d4' },
  { max: 50, label: '35 - 50 dBZ', description: 'Heavy Rain / Convective', color: '#f59e0b' },
  { max: Infinity, label: '> 50 dBZ', description: 'Severe Rain / Hail Core', color: '#ef4444' },
];

export const RISK_LEVEL_CONFIG = {
  LOW: {
    label: 'LOW SEVERITY',
    color: '#10b981',
    bgColor: 'rgba(16, 185, 129, 0.12)',
    borderColor: 'rgba(16, 185, 129, 0.35)',
    description: 'Precipitation accumulation below 35 mm/day. Synoptic forcing quiescent.',
  },
  MODERATE: {
    label: 'MODERATE SEVERITY',
    color: '#06b6d4',
    bgColor: 'rgba(6, 182, 212, 0.12)',
    borderColor: 'rgba(6, 182, 212, 0.35)',
    description: 'Moderate precipitation (35.5 - 64.4 mm/day). Active monsoon orographic convergence.',
  },
  HIGH: {
    label: 'HEAVY RAINFALL',
    color: '#f59e0b',
    bgColor: 'rgba(245, 158, 11, 0.12)',
    borderColor: 'rgba(245, 158, 11, 0.35)',
    description: 'Heavy to Very Heavy Rainfall (64.5 - 204.4 mm/day). Strong dynamical forcing & Low-Level Jet.',
  },
  EXTREME: {
    label: 'EXTREME RAINFALL',
    color: '#ef4444',
    bgColor: 'rgba(239, 68, 68, 0.12)',
    borderColor: 'rgba(239, 68, 68, 0.35)',
    description: 'Extremely Heavy Rainfall (≥ 204.5 mm/day). Intense Low Pressure System with active orographic amplification.',
  },
};

export const WARNING_STATUS_CONFIG = {
  NO_ALERT: {
    label: 'NORMAL / NO ALERT',
    color: '#10b981',
    bgColor: 'rgba(16, 185, 129, 0.15)',
    borderColor: '#10b981',
  },
  MONITOR: {
    label: 'WATCH (MODERATE)',
    color: '#06b6d4',
    bgColor: 'rgba(6, 182, 212, 0.15)',
    borderColor: '#06b6d4',
  },
  PREPARE: {
    label: 'ALERT (HEAVY RAIN)',
    color: '#f59e0b',
    bgColor: 'rgba(245, 158, 11, 0.15)',
    borderColor: '#f59e0b',
  },
  ACTION: {
    label: 'WARNING (EXTREME)',
    color: '#ef4444',
    bgColor: 'rgba(239, 68, 68, 0.15)',
    borderColor: '#ef4444',
  },
  INSUFFICIENT_DATA: {
    label: 'INSUFFICIENT DATA',
    color: '#94a3b8',
    bgColor: 'rgba(148, 163, 184, 0.15)',
    borderColor: '#94a3b8',
  },
};

