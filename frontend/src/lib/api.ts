import { UnifiedPredictionRequest, UnifiedPredictionResponse } from './types';

const RAW_API_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://127.0.0.1:8001';
const API_BASE_URL = RAW_API_URL.replace(/\/+$/, '');

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Trigger the unified end-to-end multi-source flood prediction pipeline.
 */
export async function runUnifiedPrediction(
  params: UnifiedPredictionRequest,
  signal?: AbortSignal
): Promise<UnifiedPredictionResponse> {
  const url = `${API_BASE_URL}/api/v1/predict`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(params),
      signal,
    });

    if (!response.ok) {
      let errorDetail = `HTTP ${response.status} ${response.statusText}`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) {
          if (typeof errorJson.detail === 'string') {
            errorDetail = errorJson.detail;
          } else if (Array.isArray(errorJson.detail)) {
            errorDetail = errorJson.detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ');
          } else {
            errorDetail = JSON.stringify(errorJson.detail);
          }
        } else if (errorJson.message) {
          errorDetail = errorJson.message;
        } else if (errorJson.error?.message) {
          errorDetail = errorJson.error.message;
        }
      } catch {
        // Fallback to text if not JSON
        const rawText = await response.text().catch(() => '');
        if (rawText) errorDetail = rawText;
      }

      throw new ApiError(errorDetail, response.status);
    }

    const data: UnifiedPredictionResponse = await response.json();
    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof Error && error.name === 'AbortError') {
      throw error;
    }
    const isNetworkError =
      error instanceof TypeError &&
      (error.message.includes('fetch') || error.message.includes('Network') || error.message.includes('Failed'));
    throw new ApiError(
      isNetworkError
        ? `Backend service connection failed at ${API_BASE_URL}. Ensure FastAPI is running on port 8001.`
        : (error instanceof Error ? error.message : 'Network failure connecting to HydroWatch backend service.')
    );
  }
}

/**
 * Query backend health status.
 */
export async function checkBackendHealth(): Promise<{ status: string; version: string; project: string }> {
  const url = `${API_BASE_URL}/health`;
  const response = await fetch(url, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) {
    throw new ApiError(`Health check failed with status ${response.status}`);
  }
  return response.json();
}

/**
 * Fetch all registered post-processing models from model registry.
 */
export async function fetchPostprocessingModels() {
  const url = `${API_BASE_URL}/api/v1/postprocess/models`;
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new ApiError(`Failed fetching models: ${res.statusText}`, res.status);
  return res.json();
}

/**
 * Fetch 4-product post-processing comparison for a target location.
 */
export async function fetchPostprocessingComparison(params: {
  raw_rainfall_mm?: number;
  latitude?: number;
  longitude?: number;
  lead_time_hours?: number;
  month?: number;
}) {
  const query = new URLSearchParams();
  if (params.raw_rainfall_mm !== undefined) query.set('raw_rainfall_mm', params.raw_rainfall_mm.toString());
  if (params.latitude !== undefined) query.set('latitude', params.latitude.toString());
  if (params.longitude !== undefined) query.set('longitude', params.longitude.toString());
  if (params.lead_time_hours !== undefined) query.set('lead_time_hours', params.lead_time_hours.toString());
  if (params.month !== undefined) query.set('month', params.month.toString());

  const url = `${API_BASE_URL}/api/v1/postprocess/compare?${query.toString()}`;
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new ApiError(`Failed fetching comparison: ${res.statusText}`, res.status);
  return res.json();
}

/**
 * Fetch district-level post-processed forecasts across India.
 */
export async function fetchDistrictForecasts(date?: string) {
  const query = new URLSearchParams();
  if (date) query.set('date', date);
  const url = `${API_BASE_URL}/api/v1/postprocess/districts${date ? `?${query.toString()}` : ''}`;
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new ApiError(`Failed fetching district forecasts: ${res.statusText}`, res.status);
  return res.json();
}

/**
 * Fetch prospective verification benchmarks evaluated on held-out test data.
 */
export async function fetchVerificationBenchmarks(regime?: string, threshold_mm = 64.5) {
  const query = new URLSearchParams();
  if (regime) query.set('regime', regime);
  query.set('threshold_mm', threshold_mm.toString());

  const url = `${API_BASE_URL}/api/v1/postprocess/verification?${query.toString()}`;
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new ApiError(`Failed fetching verification: ${res.statusText}`, res.status);
  return res.json();
}

/**
 * Fetch operational data sources status and ingestion health.
 */
export async function fetchDataSourcesStatus() {
  const url = `${API_BASE_URL}/api/v1/data/status`;
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new ApiError(`Failed fetching data sources status: ${res.statusText}`, res.status);
  return res.json();
}

/**
 * Fetch data sources catalog.
 */
export async function fetchDataSourcesCatalog() {
  const url = `${API_BASE_URL}/api/v1/data/sources`;
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new ApiError(`Failed fetching data sources catalog: ${res.statusText}`, res.status);
  return res.json();
}
