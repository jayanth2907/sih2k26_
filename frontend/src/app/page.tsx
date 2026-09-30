'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import dynamic from 'next/dynamic';
import { Header } from '@/components/app-shell/Header';
import { AnalysisCommand } from '@/components/location/AnalysisCommand';
import { MapHud } from '@/components/map/MapHud';
import { WarningPanel } from '@/components/warning/WarningPanel';
import { EvidenceStrip } from '@/components/common/EvidenceStrip';
import { RadarModal } from '@/components/radar/RadarModal';
import { WhyAssessment } from '@/components/explainability/WhyAssessment';
import { DistrictForecastTable } from '@/components/forecast/DistrictForecastTable';
import { VerificationModal } from '@/components/verification/VerificationModal';
import { FreshnessTimeline } from '@/components/source-status/FreshnessTimeline';
import { AuditPanel } from '@/components/provenance/AuditPanel';
import { AnalysisProgress } from '@/components/loading/AnalysisProgress';
import { ErrorState } from '@/components/common/ErrorState';
import { PRESET_LOCATIONS } from '@/lib/constants';
import {
  PresetLocation,
  UnifiedPredictionResponse,
  PostProcessingModelId,
  CesiumRainfallLayerId,
  DistrictForecast,
} from '@/lib/types';
import {
  runUnifiedPrediction,
  checkBackendHealth,
  fetchDistrictForecasts,
} from '@/lib/api';

// Dynamically import Cesium with SSR disabled to prevent Node canvas errors
const DynamicCesiumGlobe = dynamic(
  () => import('@/components/map/CesiumGlobe').then((mod) => mod.CesiumGlobe),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[540px] md:h-[620px] bg-[#08090c] rounded-lg flex flex-col items-center justify-center border border-[#1e2638] text-xs font-mono text-[#64748b]">
        <div className="w-8 h-8 border-2 border-[#00e5ff] border-t-transparent rounded-full animate-spin mb-3" />
        <span>INITIALIZING GEOSPATIAL 3D ENGINE...</span>
      </div>
    ),
  }
);

export default function HydroWatchDashboard() {
  // Location State (Default: Mumbai, Maharashtra)
  const [selectedLocation, setSelectedLocation] = useState<PresetLocation>(PRESET_LOCATIONS[0]);
  const [latitude, setLatitude] = useState<number>(PRESET_LOCATIONS[0].latitude);
  const [longitude, setLongitude] = useState<number>(PRESET_LOCATIONS[0].longitude);
  const [locationName, setLocationName] = useState<string>(PRESET_LOCATIONS[0].name);

  // Analysis Parameters (Default: 2024-07-15 peak monsoon validation benchmark)
  const [predictionDate, setPredictionDate] = useState<string>('2024-07-15');
  const [nwpHorizonHours, setNwpHorizonHours] = useState<number>(24);
  const [satelliteMaxCloud, setSatelliteMaxCloud] = useState<number>(60);

  // Model & Layer Selection State
  const [selectedModel, setSelectedModel] = useState<PostProcessingModelId>('regime_aware_ml');
  const [activeLayer, setActiveLayer] = useState<CesiumRainfallLayerId>('ai_calibrated');

  // Execution & Telemetry State
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [data, setData] = useState<UnifiedPredictionResponse | null>(null);
  const [districtList, setDistrictList] = useState<DistrictForecast[]>([]);
  const [error, setError] = useState<{ message: string; details?: string } | null>(null);
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean>(true);
  const [isRadarModalOpen, setIsRadarModalOpen] = useState<boolean>(false);
  const [isVerificationModalOpen, setIsVerificationModalOpen] = useState<boolean>(false);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Check backend health & fetch district forecast list on initial mount
  useEffect(() => {
    checkBackendHealth()
      .then(() => setIsBackendHealthy(true))
      .catch((err) => {
        console.warn('[HydroWatch] Backend connection warning:', err);
        setIsBackendHealthy(false);
      });

    fetchDistrictForecasts(predictionDate)
      .then((res) => {
        if (res?.districts && res.districts.length > 0) {
          setDistrictList(res.districts);
        }
      })
      .catch((err) => {
        console.warn('[HydroWatch] District forecasts fetch fallback:', err);
      });
  }, [predictionDate]);

  // Execute Unified Prediction Pipeline
  const handleRunAnalysis = useCallback(async () => {
    if (isLoading) return;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsLoading(true);
    setError(null);

    try {
      const response = await runUnifiedPrediction(
        {
          latitude,
          longitude,
          prediction_date: predictionDate,
          nwp_horizon_hours: nwpHorizonHours,
          satellite_max_cloud: satelliteMaxCloud,
          location_name: locationName,
        },
        controller.signal
      );

      setData(response);
      setIsBackendHealthy(true);
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        return; // Cleanly cancelled
      }
      console.error('[HydroWatch] Analysis failed:', err);
      const errMsg = err instanceof Error ? err.message : 'Environmental synthesis failed.';
      setError({
        message: 'Could not complete multi-source environmental assessment for target location.',
        details: errMsg,
      });
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  }, [latitude, longitude, predictionDate, nwpHorizonHours, satelliteMaxCloud, locationName, isLoading]);

  // Run initial forecast prediction on mount
  useEffect(() => {
    handleRunAnalysis();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Location Preset Switch: STRICT STATE ISOLATION
  const handleSelectPreset = useCallback((preset: PresetLocation) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setData(null);
    setError(null);
    setSelectedLocation(preset);
    setLatitude(preset.latitude);
    setLongitude(preset.longitude);
    setLocationName(preset.name);
  }, []);

  // Custom Coordinates Selection
  const handleSelectCustom = useCallback((lat: number, lon: number, name: string) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setData(null);
    setError(null);
    setSelectedLocation({
      id: 'custom',
      name: name || 'Custom Point',
      state: 'User Defined',
      latitude: lat,
      longitude: lon,
      defaultZoomAltitude: 18000,
    });
    setLatitude(lat);
    setLongitude(lon);
    setLocationName(name || 'Custom Point');
  }, []);

  // District Table Selection Handler
  const handleSelectDistrictFromTable = useCallback(
    (distName: string, stateName: string) => {
      // Find matching preset if available
      const matchingPreset = PRESET_LOCATIONS.find(
        (p) => p.name.toLowerCase().includes(distName.toLowerCase()) || distName.toLowerCase().includes(p.name.toLowerCase())
      );

      if (matchingPreset) {
        handleSelectPreset(matchingPreset);
      } else {
        // Find in district list coordinates if available or fallback
        const distCoordMap: Record<string, [number, number]> = {
          'Mumbai City': [18.9388, 72.8354],
          Satara: [17.6805, 73.993],
          Puri: [19.8135, 85.8312],
          Nagpur: [21.1458, 79.0882],
          'East Khasi Hills': [25.5788, 91.8933],
          Ernakulam: [9.9816, 76.2999],
          Pune: [18.5204, 73.8567],
          Ratnagiri: [16.9902, 73.312],
          Uttara_Kannada: [14.8136, 74.1298],
          Wayand: [11.6854, 76.132],
        };

        const coords = distCoordMap[distName] || [latitude, longitude];
        handleSelectCustom(coords[0], coords[1], `${distName}, ${stateName}`);
      }
    },
    [handleSelectPreset, handleSelectCustom, latitude, longitude]
  );

  // Extract Forecast Summary for CesiumGlobe & Legends
  const rawNwpVal = data?.post_processing?.raw_nwp?.accumulated_24h_mm ?? data?.nwp?.accumulated_precipitation_mm ?? 38.5;
  const correctedVal =
    selectedModel === 'raw_nwp'
      ? rawNwpVal
      : selectedModel === 'quantile_mapping'
      ? data?.post_processing?.quantile_mapping?.accumulated_24h_mm ?? rawNwpVal * 1.15
      : selectedModel === 'global_ml'
      ? data?.post_processing?.global_ml_correction?.accumulated_24h_mm ?? rawNwpVal * 1.25
      : data?.post_processing?.regime_aware_ml_correction?.accumulated_24h_mm ?? (rawNwpVal + 17.3);

  const deltaVal = correctedVal - rawNwpVal;
  const heavyProbVal = data?.probabilities?.heavy_rain_ge_64_5mm ?? (correctedVal >= 64.5 ? 0.78 : 0.45);
  const uncertaintyWidthVal = (data?.post_processing?.regime_aware_ml_correction?.uncertainty_upper_p90_mm ?? correctedVal * 1.45) -
    (data?.post_processing?.regime_aware_ml_correction?.uncertainty_lower_p10_mm ?? correctedVal * 0.65);

  const primaryRegimeKey =
    typeof data?.regime?.primary_regime === 'object' && data?.regime?.primary_regime !== null
      ? (data.regime.primary_regime as any).regime
      : (data?.regime?.primary_regime as string | undefined) || 'ACTIVE_MONSOON';

  return (
    <div className="min-h-screen bg-[#08090c] flex flex-col selection:bg-[#0284c7]/30 selection:text-[#00e5ff]">
      {/* 1. Authoritative Header */}
      <Header
        locationName={locationName}
        latitude={latitude}
        longitude={longitude}
        generatedAt={data?.generated_at}
        isBackendHealthy={isBackendHealthy}
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        onOpenVerificationModal={() => setIsVerificationModalOpen(true)}
        isDemo={true}
        streamsOnlineCount={
          data?.source_status
            ? Object.values(data.source_status).filter((s) => s.available).length
            : isBackendHealthy
            ? 4
            : 0
        }
      />

      {/* Main Dashboard Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-3 sm:p-5 space-y-5">
        {/* 2. Floating Command Bar */}
        <AnalysisCommand
          selectedLocation={selectedLocation}
          onSelectPreset={handleSelectPreset}
          onSelectCustom={handleSelectCustom}
          onRunAnalysis={handleRunAnalysis}
          isLoading={isLoading}
          predictionDate={predictionDate}
          onChangeDate={setPredictionDate}
          nwpHorizonHours={nwpHorizonHours}
          onChangeNwpHorizon={setNwpHorizonHours}
          satelliteMaxCloud={satelliteMaxCloud}
          onChangeSatelliteMaxCloud={setSatelliteMaxCloud}
        />

        {/* 3. Hero Geospatial Section: Real 3D Terrain Globe & Map HUD */}
        <section className="relative">
          <DynamicCesiumGlobe
            latitude={latitude}
            longitude={longitude}
            locationName={locationName}
            geojson={data?.contours?.geojson || data?.inundation?.geojson}
            polygonCount={data?.contours?.polygon_count || data?.inundation?.polygon_count}
            activeLayer={activeLayer}
            onSelectLayer={setActiveLayer}
            isDemo={true}
            forecastSummary={{
              rawNwpMm: rawNwpVal,
              correctedMm: correctedVal,
              deltaMm: deltaVal,
              regime: primaryRegimeKey.replace(/_/g, ' '),
              heavyProb: heavyProbVal,
              uncertaintyWidth: uncertaintyWidthVal,
            }}
          />

          {/* Floating Map HUD (Overlay on desktop) */}
          <div className="mt-3 lg:mt-0 lg:absolute lg:top-14 lg:left-3 z-20">
            <MapHud
              locationName={locationName}
              latitude={latitude}
              longitude={longitude}
              riskScore={data?.risk?.score}
              riskLevel={data?.risk?.level}
              warningStatus={data?.warning?.status}
              primaryRegime={primaryRegimeKey as any}
              regimeConfidence={
                data?.regime?.confidence ??
                data?.regime?.primary_confidence ??
                (typeof data?.regime?.primary_regime === 'object' && data?.regime?.primary_regime !== null
                  ? (data.regime.primary_regime as any).confidence
                  : 0.85)
              }
              postProcessing={data?.post_processing}
              probabilities={data?.probabilities}
              selectedModel={selectedModel}
              rawNwpMm={rawNwpVal}
              correctedMm={correctedVal}
              deltaMm={deltaVal}
              isDemo={true}
            />
          </div>
        </section>

        {/* Loading Progress State */}
        {isLoading && (
          <section className="py-4">
            <AnalysisProgress locationName={locationName} stagesCompleted={2} />
          </section>
        )}

        {/* Error Notification State */}
        {error && !isLoading && (
          <section className="py-2">
            <ErrorState
              message={error.message}
              details={error.details}
              onRetry={handleRunAnalysis}
            />
          </section>
        )}

        {/* 4. Prototype Early Warning Instrument */}
        <section>
          <WarningPanel warning={data?.warning} />
        </section>

        {/* 5. Physical Telemetry 4-Method Evidence Strip */}
        <section>
          <EvidenceStrip
            rainfall={data?.rainfall_prediction}
            radar={data?.radar}
            nwp={data?.nwp}
            regime={data?.regime}
            postProcessing={data?.post_processing}
            probabilities={data?.probabilities}
            selectedModel={selectedModel}
            onSelectModel={setSelectedModel}
            onOpenRadarModal={() => setIsRadarModalOpen(true)}
          />
        </section>

        {/* 6. District Forecasts Hierarchy Table */}
        <section>
          <DistrictForecastTable
            districts={districtList}
            selectedDistrictName={locationName}
            onSelectDistrict={handleSelectDistrictFromTable}
          />
        </section>

        {/* 7. Explainability: 4-Product Comparison Benchmark, Synoptic Feeds & Tree SHAP */}
        <section>
          <WhyAssessment
            risk={data?.risk}
            xai={data?.rainfall_prediction?.xai}
            radar={data?.radar}
            nwp={data?.nwp}
            regime={data?.regime}
            postProcessing={data?.post_processing}
            probabilities={data?.probabilities}
            verification={data?.verification}
            districtForecast={data?.district_forecast}
            lat={latitude}
            lon={longitude}
            onOpenRadarModal={() => setIsRadarModalOpen(true)}
          />
        </section>

        {/* 8. Source Freshness & Latency Breakdown */}
        <section>
          <FreshnessTimeline
            sourceStatus={data?.source_status}
            timing={data?.timing}
          />
        </section>

        {/* 9. Technical Diagnostic Provenance Drawer */}
        <section>
          <AuditPanel
            data={data}
            selectedModel={selectedModel}
            isDemo={true}
          />
        </section>
      </main>

      {/* Dedicated RainViewer Doppler Radar Modal */}
      <RadarModal
        isOpen={isRadarModalOpen}
        onClose={() => setIsRadarModalOpen(false)}
        radar={data?.radar}
        latitude={latitude}
        longitude={longitude}
        locationName={locationName}
      />

      {/* Verification Benchmark Hub Modal */}
      <VerificationModal
        isOpen={isVerificationModalOpen}
        onClose={() => setIsVerificationModalOpen(false)}
        verificationData={data?.verification}
      />
    </div>
  );
}
