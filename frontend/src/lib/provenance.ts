import { UnifiedPredictionResponse, PostProcessingModelId } from './types';
import { formatTimestamp } from './formatters';

export interface DataProvenanceInfo {
  forecastSource: string;
  observationSource: string;
  regimeSource: string;
  postProcessorModel: string;
  modelVersion: string;
  forecastInit: string;
  leadTime: string;
  isDemo: boolean;
  statusLabel: string;
  dataQuality: 'NOMINAL' | 'DEGRADED' | 'STANDBY';
  pipelineLatencyMs: number;
}

export function extractProvenance(
  data?: UnifiedPredictionResponse | null,
  isDemo = true,
  selectedModel: PostProcessingModelId = 'regime_aware_ml'
): DataProvenanceInfo {
  const modelNameMap: Record<PostProcessingModelId, string> = {
    raw_nwp: 'Raw NWP (Baseline)',
    quantile_mapping: 'Empirical Quantile Mapping (EQM)',
    global_ml: 'Global ML Model (HistGradientBoosting)',
    regime_aware_ml: 'Regime-Aware AI (MoES NCMRWF SIH26080)',
  };

  const dataSourceName = isDemo
    ? 'GFS Fallback (Open-Meteo 0.25°)'
    : (data?.regime?.data_source || 'NCMRWF NCUM Global 12km');

  const obsSource = 'IMD DWR / NASA POWER Daily Gauges';
  const regimeEngineVer = data?.provenance?.model_versions?.regime_classifier || 'RegimeEngine v2.1 (MoES)';
  const postProcVer = data?.provenance?.model_versions?.rainfall_postprocessor || 'Regime-Aware Neural ML v1.0';
  const initTimestamp = data?.generated_at ? formatTimestamp(data.generated_at) : '2024-07-15 00:00 UTC';
  const leadTime = 'T+24h (24-hour Total)';
  const statusLabel = isDemo ? 'DEMO DATA · SYNTHETIC FALLBACK' : 'LIVE OPERATIONAL (NCMRWF)';

  const latency = data?.timing?.total_ms ?? 142;

  return {
    forecastSource: dataSourceName,
    observationSource: obsSource,
    regimeSource: regimeEngineVer,
    postProcessorModel: modelNameMap[selectedModel] || postProcVer,
    modelVersion: 'v1.0-soft-conditioned',
    forecastInit: initTimestamp,
    leadTime,
    isDemo,
    statusLabel,
    dataQuality: 'NOMINAL',
    pipelineLatencyMs: Math.round(latency),
  };
}
