/**
 * HydroWatch Frontend Type Definitions
 * Directly mirrors backend Pydantic models from FastAPI OpenAPI specification.
 */

export interface Coordinates {
  latitude: floatNumber;
  longitude: floatNumber;
}

type floatNumber = number;

export interface GeoBoundingBox {
  min_lat: number;
  max_lat: number;
  min_lon: number;
  max_lon: number;
}

export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME';
export type WarningStatus = 'NO_ALERT' | 'MONITOR' | 'PREPARE' | 'ACTION' | 'INSUFFICIENT_DATA';
export type WarningUrgency = 'NONE' | 'MONITOR' | 'PREPARE' | 'ACTION';

export interface FeatureShapContribution {
  feature_name: string;
  display_name: string;
  category: 'moisture' | 'instability_pressure' | 'antecedent_rainfall' | 'temperature_wind' | 'climatology' | string;
  observed_value: number;
  shap_value: number;
  impact: 'increases_risk' | 'decreases_risk' | 'neutral';
  percentage_contribution: number;
  description: string;
}

export interface RainfallXaiSummary {
  base_margin: number;
  model_score_margin: number;
  top_positive_drivers: FeatureShapContribution[];
  top_negative_drivers: FeatureShapContribution[];
  all_contributions: FeatureShapContribution[];
  narrative: string;
  causality_chain: string[];
}

export interface UnifiedRainfallSummary {
  probability: number;
  predicted: boolean;
  threshold: number;
  observation_date: string;
  model_version: string;
  historical_records_used: number;
  latest_precipitation_mm: number;
  xai?: RainfallXaiSummary | null;
}

export interface NWPForecastSummary {
  forecast_start_time: string;
  forecast_end_time: string;
  forecast_horizon_hours: number;
  mean_precipitation_mm_hr: number;
  max_hourly_precipitation_mm_hr: number;
  total_precipitation_mm: number;
  max_cape_j_kg?: number | null;
  mean_temperature_c?: number | null;
  mean_humidity_pct?: number | null;
}

export interface UnifiedNwpSummary {
  source: string;
  model_name: string;
  forecast_summary: NWPForecastSummary;
  forecast_horizon_hours: number;
  valid_times: string[];
  peak_hourly_precipitation_mm_hr: number;
  accumulated_precipitation_mm: number;
  max_cape_j_kg?: number | null;
  hourly_precipitation: number[];
}

export interface UnifiedRadarSummary {
  source: string;
  timestamp?: string | null;
  max_reflectivity_dbz: number;
  mean_reflectivity_dbz: number;
  estimated_rain_rate_mm_hr: number;
  coverage_percentage: number;
  tile_url?: string | null;
}

export interface InundationPolygonProperties {
  flooded_area_sq_m: number;
  perimeter_m: number;
  scene_id?: string;
  source?: string;
  acquisition_date?: string;
  water_type?: string;
  is_permanent_water?: boolean;
  [key: string]: unknown;
}

export interface GeoJSONFeature {
  type: 'Feature';
  geometry: {
    type: 'Polygon' | 'MultiPolygon';
    coordinates: number[][][] | number[][][][];
  };
  properties: InundationPolygonProperties;
}

export interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
}

export interface UnifiedInundationSummary {
  source: string;
  scene: {
    scene_id?: string;
    acquisition_datetime?: string;
    cloud_coverage_percentage?: number;
    sensor?: string;
    resolution_m?: number;
    [key: string]: unknown;
  };
  flooded_area_sq_km: number;
  valid_area_sq_km: number;
  flooded_percentage: number;
  polygon_count: number;
  geojson: GeoJSONFeatureCollection;
  metadata?: {
    raw_water_area_sq_km?: number;
    raw_polygon_count?: number;
    excluded_permanent_water_sq_km?: number;
    permanent_water_polygon_count?: number;
    water_label?: string;
    [key: string]: unknown;
  };
}

export interface SourceExplanation {
  source: string;
  name: string;
  description: string;
  raw_value: unknown;
  normalized_score: number;
  original_weight: number;
  effective_weight: number;
  contribution: number;
  timestamp?: string | null;
  status: string;
}

export interface FusionMetadata {
  policy_applied: 'FULL_EVIDENCE' | 'PARTIAL_EVIDENCE' | 'INSUFFICIENT_EVIDENCE' | string;
  original_weights: Record<string, number>;
  effective_weights: Record<string, number>;
  available_sources: string[];
  unavailable_sources: string[];
  freshness: Record<string, unknown>;
}

export interface UnifiedRiskSummary {
  score: number;
  level: RiskLevel;
  thresholds: Record<string, number>;
  fusion: FusionMetadata;
  explanations: SourceExplanation[];
}

export interface PhysicalTrigger {
  source: string;
  metric: string;
  observed_value: unknown;
  threshold: number;
  triggered: boolean;
  unit: string;
  timestamp?: string | null;
  description: string;
}

export interface WarningDecision {
  status: WarningStatus;
  risk_level: RiskLevel;
  urgency: WarningUrgency;
  triggered: boolean;
  trigger_reasons: string[];
  triggers: PhysicalTrigger[];
  generated_at: string;
  valid_until?: string | null;
  validity_reason: string;
  prototype_only: boolean;
  official_warning_issued: boolean;
  disclaimer: string;
  escalation_notes?: string | null;
}

export interface SourceStatusDetail {
  available: boolean;
  status: 'success' | 'unavailable' | 'failed' | string;
  source: string;
  latency_ms: number;
  timestamp?: string | null;
  error?: string | null;
}

export interface UnifiedTimingDetail {
  weather_model1_ms: number;
  nwp_ms: number;
  radar_ms: number;
  satellite_model2_ms: number;
  fusion_ms: number;
  warning_ms: number;
  total_ms: number;
}

export interface WarningProvenance {
  risk_assessment_id?: string | null;
  model_versions: Record<string, string>;
  source_providers: Record<string, string>;
  source_timestamps: Record<string, string | null>;
  configured_thresholds: Record<string, number>;
  configured_risk_weights: Record<string, number>;
  rules_version: string;
}

// ==========================================
// PS26080: REGIME-AWARE METEOROLOGICAL TYPES
// ==========================================

export type WeatherRegimeType =
  | 'ACTIVE_MONSOON'
  | 'BREAK_MONSOON'
  | 'MONSOON_LOW_LPS'
  | 'COASTAL_CONVERGENCE'
  | 'OROGRAPHIC_RAINFALL'
  | 'WESTERN_DISTURBANCE'
  | 'NEUTRAL';

export interface SynopticFeatures {
  low_level_jet_speed_kts: number;
  low_level_jet_direction_deg: number;
  monsoon_trough_lat: number;
  trough_position: 'normal' | 'active_south' | 'break_foothills' | 'transition';
  olr_w_m2: number;
  mid_tropospheric_vorticity_1e5_s: number;
  surface_pressure_anomaly_hpa: number;
  cape_j_kg: number;
  integrated_vapor_transport_kg_m_s: number;
  orographic_lift_index: number;
  coastal_convergence_index: number;
}

export interface AtmosphericDriver {
  feature: string;
  value: number;
  importance: number;
  description?: string;
}

export interface RegimeClassification {
  regime: WeatherRegimeType;
  confidence: number;
  description: string;
  synoptic_drivers: string[];
}

export interface RegimeResponse {
  status?: string;
  location?: Coordinates;
  location_name?: string | null;
  target_date?: string;
  target_month?: number;
  primary_regime: WeatherRegimeType | RegimeClassification | string;
  confidence?: number;
  primary_confidence?: number;
  secondary_regimes: (WeatherRegimeType | RegimeClassification | string)[];
  probabilities?: Record<string, number>;
  drivers?: AtmosphericDriver[];
  synoptic_features: SynopticFeatures;
  active_regimes_summary?: string[];
  diagnostic_narrative?: string;
  regime_narrative?: string;
  model_version?: string;
  data_source?: string;
  is_demo?: boolean;
  timestamp?: string;
}


export interface ProductDetail {
  product_id: 'raw_nwp' | 'quantile_mapping' | 'global_ml' | 'regime_aware_ml';
  name: string;
  methodology: string;
  accumulated_24h_mm: number;
  peak_hourly_rate_mm_hr: number;
  hourly_series_mm: number[];
  bias_correction_delta_mm: number;
  uncertainty_lower_p10_mm: number;
  uncertainty_upper_p90_mm: number;
  ensemble_spread_mm: number;
}

export interface PostProcessingComparison {
  raw_nwp: ProductDetail;
  quantile_mapping: ProductDetail;
  global_ml_correction: ProductDetail;
  regime_aware_ml_correction: ProductDetail;
  best_performing_product: string;
  skill_gain_vs_raw_pct: number;
  skill_gain_vs_global_pct: number;
}

export interface HeavyRainfallProbabilities {
  heavy_rain_ge_64_5mm: number;
  very_heavy_rain_ge_115_6mm: number;
  extremely_heavy_rain_ge_204_5mm: number;
  imd_category: 'No Warning' | 'Watch (Heavy Rain)' | 'Alert (Very Heavy Rain)' | 'Warning (Extremely Heavy Rain)';
  probability_source: string;
}

export interface DistrictForecast {
  district_name: string;
  state_name: string;
  forecast_date: string;
  raw_nwp_rainfall_mm: number;
  corrected_rainfall_mm: number;
  correction_magnitude_mm: number;
  forecast_lower_bound_p10_mm: number;
  forecast_upper_bound_p90_mm: number;
  ensemble_spread_mm: number;
  heavy_probability_pct: number;
  very_heavy_probability_pct: number;
  extreme_probability_pct: number;
  primary_regime: WeatherRegimeType;
  uncertainty_category: 'LOW' | 'MODERATE' | 'HIGH' | 'EXTREME';
}

export interface VerificationMetricSet {
  rmse: number;
  ets: number;
  csi: number;
  pod: number;
  far: number;
  fss: number;
}

export interface VerificationResponse {
  reference_source: string;
  verification_period: string;
  lead_time_hours: number;
  sample_size_events: number;
  raw_nwp: VerificationMetricSet;
  quantile_mapping: VerificationMetricSet;
  global_ml: VerificationMetricSet;
  regime_aware_ml: VerificationMetricSet;
  regime_specific_skill: Record<string, { ets: number; csi: number; rmse: number }>;
}

export interface UnifiedSpatialContours {
  contour_levels_mm: number[];
  geojson: GeoJSONFeatureCollection;
  polygon_count: number;
  max_calibrated_mm: number;
}

export interface UnifiedPredictionResponse {
  status: string;
  request: {
    latitude: number;
    longitude: number;
    prediction_date?: string | null;
    analysis_datetime?: string | null;
    nwp_horizon_hours?: number;
    satellite_date?: string | null;
    satellite_max_cloud?: number;
    min_polygon_area_sq_m?: number;
    location_name?: string | null;
    [key: string]: unknown;
  };
  generated_at: string;
  
  // PS26080 Core Intelligence
  regime: RegimeResponse;
  post_processing: PostProcessingComparison;
  probabilities: HeavyRainfallProbabilities;
  district_forecast: DistrictForecast;
  verification: VerificationResponse;
  contours?: UnifiedSpatialContours | null;

  // Feeds & Observations
  rainfall_prediction?: UnifiedRainfallSummary | null;
  nwp?: UnifiedNwpSummary | null;
  radar?: UnifiedRadarSummary | null;
  inundation?: UnifiedInundationSummary | null;
  risk: UnifiedRiskSummary;
  warning: WarningDecision;
  source_status: Record<string, SourceStatusDetail>;
  timing: UnifiedTimingDetail;
  provenance: WarningProvenance;
}

export interface UnifiedPredictionRequest {
  latitude: number;
  longitude: number;
  prediction_date?: string;
  analysis_datetime?: string;
  nwp_horizon_hours?: number;
  nwp_source_preference?: string;
  satellite_date?: string;
  satellite_max_cloud?: number;
  min_polygon_area_sq_m?: number;
  location_name?: string;
  include_geojson_contours?: boolean;
}

export interface PresetLocation {
  id: string;
  name: string;
  state: string;
  latitude: number;
  longitude: number;
  defaultZoomAltitude: number;
  regimeHint?: WeatherRegimeType;
}

export interface ModelRegistryEntry {
  model_id: string;
  model_name: string;
  version: string;
  architecture: string;
  training_period: string;
  validation_period: string;
  test_period: string;
  feature_schema_version: string;
  regime_schema_version: string;
  data_sources: string[];
  test_metrics: Record<string, number>;
  is_operational_ncmrwf: boolean;
  is_demo: boolean;
  registered_at: string;
}

export interface DataSourceStatusResponse {
  source_id: string;
  name: string;
  role: string;
  is_live_operational: boolean;
  is_demo_fallback: boolean;
  last_ingestion_time: string;
  sample_record_count: number;
  quality_status: string;
  error_detail?: string | null;
}

export type PostProcessingModelId = 'raw_nwp' | 'quantile_mapping' | 'global_ml' | 'regime_aware_ml';

export type CesiumRainfallLayerId =
  | 'ai_calibrated'
  | 'raw_nwp'
  | 'bias_delta'
  | 'heavy_prob'
  | 'regime'
  | 'uncertainty';

export interface ForecastState {
  timestamp: string;
  forecast_initialization: string;
  lead_time_hours: number;
  latitude: number;
  longitude: number;
  district_name: string;
  state_name: string;
  data_source: string;
  is_demo: boolean;
  selected_model: PostProcessingModelId;
  active_layer: CesiumRainfallLayerId;
  regime: WeatherRegimeType;
  regime_probabilities: Record<string, number>;
  regime_confidence: number;
  raw_nwp_mm: number;
  eqm_mm: number;
  global_ml_mm: number;
  regime_aware_mm: number;
  bias_delta_mm: number;
  heavy_probability: number;
  very_heavy_probability: number;
  extreme_probability: number;
  p10_mm: number;
  p50_mm: number;
  p90_mm: number;
  uncertainty_width_mm: number;
  model_version: string;
  data_freshness_status: string;
}
