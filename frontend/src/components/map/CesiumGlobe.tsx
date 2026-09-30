'use client';

import React, { useEffect, useRef, useState } from 'react';
import type * as CesiumType from 'cesium';
import {
  Compass,
  Maximize2,
  Minimize2,
  Layers,
  ZoomIn,
  ZoomOut,
  Crosshair,
  MapPin,
  AlertTriangle,
} from 'lucide-react';
import { CesiumRainfallLayerId, GeoJSONFeatureCollection } from '@/lib/types';
import { formatCoordinates, formatNumber } from '@/lib/formatters';

interface CesiumGlobeProps {
  latitude: number;
  longitude: number;
  locationName: string;
  geojson?: GeoJSONFeatureCollection | null;
  polygonCount?: number;
  activeLayer?: CesiumRainfallLayerId;
  onSelectLayer?: (layer: CesiumRainfallLayerId) => void;
  isDemo?: boolean;
  forecastSummary?: {
    rawNwpMm?: number;
    correctedMm?: number;
    deltaMm?: number;
    regime?: string;
    heavyProb?: number;
    uncertaintyWidth?: number;
  } | null;
}

export const CesiumGlobe: React.FC<CesiumGlobeProps> = ({
  latitude,
  longitude,
  locationName,
  geojson,
  polygonCount = 0,
  activeLayer = 'ai_calibrated',
  onSelectLayer,
  isDemo = true,
  forecastSummary,
}) => {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<CesiumType.Viewer | null>(null);
  const geojsonDataSourceRef = useRef<CesiumType.GeoJsonDataSource | null>(null);
  const locationPinEntityRef = useRef<CesiumType.Entity | null>(null);
  const isCesiumLoadedRef = useRef(false);

  const [isInitializing, setIsInitializing] = useState(true);
  const [terrainLoaded, setTerrainLoaded] = useState(false);
  const [satelliteLoaded, setSatelliteLoaded] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedPolygonMeta, setSelectedPolygonMeta] = useState<Record<string, unknown> | null>(null);
  const [inspectedLocation, setInspectedLocation] = useState<{
    lat: number;
    lon: number;
    name?: string;
  } | null>(null);
  const [isLayerMenuOpen, setIsLayerMenuOpen] = useState(false);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement));
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  // Initialize Cesium viewer once
  useEffect(() => {
    let isCancelled = false;

    async function initCesium() {
      if (!containerRef.current || viewerRef.current) return;

      try {
        // Set Cesium base URL for static assets (Workers, Assets, Widgets)
        (window as unknown as { CESIUM_BASE_URL: string }).CESIUM_BASE_URL = '/cesium';

        const Cesium: typeof CesiumType = await import('cesium');
        if (isCancelled || !containerRef.current) return;

        // Configure optional Cesium Ion Token
        const ionToken = process.env.NEXT_PUBLIC_CESIUM_ION_TOKEN;
        if (ionToken) {
          Cesium.Ion.defaultAccessToken = ionToken;
        }

        // Initialize Cesium Viewer with clean minimalist interface
        const viewer = new Cesium.Viewer(containerRef.current, {
          animation: false,
          baseLayerPicker: false,
          fullscreenButton: false,
          geocoder: false,
          homeButton: false,
          infoBox: false, // We use custom precision popover
          sceneModePicker: false,
          selectionIndicator: false,
          timeline: false,
          navigationHelpButton: false,
          navigationInstructionsInitiallyVisible: false,
          scene3DOnly: true,
          shouldAnimate: false,
          contextOptions: {
            webgl: {
              preserveDrawingBuffer: true,
            },
          },
        });

        viewerRef.current = viewer;

        // Hide raw Cesium Ion bottom container, watermarks, and credit popups
        if (viewer.bottomContainer) {
          (viewer.bottomContainer as HTMLElement).style.display = 'none';
        }

        // Suppress raw Cesium Ion error popup panel on UI
        if (viewer.cesiumWidget) {
          (viewer.cesiumWidget as unknown as { showErrorPanel: () => void }).showErrorPanel = () => {};
        }

        // High-fidelity scene optimization: crisp Retina scaling, low SSE, HDR
        viewer.resolutionScale = Math.min(window.devicePixelRatio || 1.0, 2.0);
        viewer.scene.globe.maximumScreenSpaceError = 1.25; // Sharp tile resolution without blurring
        viewer.scene.globe.tileCacheSize = 300;
        viewer.scene.globe.depthTestAgainstTerrain = true;
        viewer.scene.globe.enableLighting = false; // Vivid satellite imagery day and night
        viewer.scene.globe.showWaterEffect = true;
        if (viewer.scene.postProcessStages?.fxaa) {
          viewer.scene.postProcessStages.fxaa.enabled = true;
        }
        viewer.scene.highDynamicRange = true;

        // 1. Configure Base Satellite Imagery
        // Priority 1: Cesium Ion World Imagery (Aerial with labels) using user token
        // Priority 2: ArcGIS MapServer Imagery Provider (reads level limits, avoids grey "data not available" tiles)
        try {
          viewer.imageryLayers.removeAll();
          let baseProvider: CesiumType.ImageryProvider | null = null;

          if (ionToken && typeof Cesium.createWorldImageryAsync === 'function') {
            try {
              baseProvider = await Cesium.createWorldImageryAsync({
                style: Cesium.IonWorldImageryStyle.AERIAL_WITH_LABELS,
              });
            } catch (ionErr) {
              console.warn('[HydroWatch Cesium] Ion World Imagery initialization fallback:', ionErr);
            }
          }

          if (!baseProvider) {
            if (typeof Cesium.ArcGisMapServerImageryProvider?.fromUrl === 'function') {
              baseProvider = await Cesium.ArcGisMapServerImageryProvider.fromUrl(
                'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer',
                { enablePickFeatures: false }
              );
            } else {
              baseProvider = new Cesium.UrlTemplateImageryProvider({
                url: 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                maximumLevel: 18,
              });
            }
          }

          if (baseProvider && !isCancelled && viewerRef.current) {
            viewer.imageryLayers.addImageryProvider(baseProvider);
            setSatelliteLoaded(true);
          }
        } catch (imageryErr) {
          console.warn('[HydroWatch Cesium] Base satellite imagery error:', imageryErr);
        }

        // 2. Configure 3D World Terrain with realistic relief & water mask
        try {
          if (typeof Cesium.createWorldTerrainAsync === 'function') {
            const terrain = await Cesium.createWorldTerrainAsync({
              requestWaterMask: true,
              requestVertexNormals: true,
            });
            if (!isCancelled && viewerRef.current) {
              (terrain as unknown as { errorEvent?: { addEventListener: (cb: () => void) => void } }).errorEvent?.addEventListener(() => {
                setTerrainLoaded(false);
              });
              viewer.terrainProvider = terrain;
              setTerrainLoaded(true);
            }
          } else if (typeof Cesium.Terrain?.fromWorldTerrain === 'function') {
            const terrain = Cesium.Terrain.fromWorldTerrain({
              requestWaterMask: true,
              requestVertexNormals: true,
            });
            if (!isCancelled && viewerRef.current) {
              (terrain as unknown as { errorEvent?: { addEventListener: (cb: () => void) => void } }).errorEvent?.addEventListener(() => {
                setTerrainLoaded(false);
              });
              viewer.scene.setTerrain(terrain);
              setTerrainLoaded(true);
            }
          }
        } catch (terrainErr) {
          console.warn('[HydroWatch Cesium] 3D World Terrain fallback to ellipsoid:', terrainErr);
          setTerrainLoaded(false);
        }

        // 3. Configure Click / Hover Handler for Inundation Polygons
        const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
        handler.setInputAction((movement: { position: CesiumType.Cartesian2 }) => {
          const pickedObject = viewer.scene.pick(movement.position);
          if (Cesium.defined(pickedObject) && pickedObject.id && pickedObject.id.properties) {
            const props: Record<string, unknown> = {};
            const propertyNames = pickedObject.id.properties.propertyNames;
            for (const name of propertyNames) {
              props[name] = pickedObject.id.properties[name]?.getValue();
            }
            setSelectedPolygonMeta(props);
          } else {
            setSelectedPolygonMeta(null);
          }
        }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

        isCesiumLoadedRef.current = true;
        setIsInitializing(false);

        // Fly initial camera to target coordinates
        flyCameraToCoordinates(viewer, latitude, longitude, 18000, -38);
        updateLocationPin(viewer, latitude, longitude, locationName);
      } catch (err) {
        console.error('[HydroWatch Cesium] Viewer initialization failure:', err);
        setErrorMessage('Geospatial view initialization failed. WebGL2 or 3D canvas unavailable.');
        setIsInitializing(false);
      }
    }

    initCesium();

    return () => {
      isCancelled = true;
      if (viewerRef.current && !viewerRef.current.isDestroyed()) {
        viewerRef.current.destroy();
        viewerRef.current = null;
      }
    };
  }, []);

  // Camera Helper Functions
  const flyCameraToCoordinates = async (
    viewer: CesiumType.Viewer,
    lat: number,
    lon: number,
    height: number,
    pitchDeg: number
  ) => {
    const Cesium: typeof CesiumType = await import('cesium');
    if (!viewer || viewer.isDestroyed()) return;
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(lon, lat, height),
      orientation: {
        heading: Cesium.Math.toRadians(0.0),
        pitch: Cesium.Math.toRadians(pitchDeg),
        roll: 0.0,
      },
      duration: 1.8,
    });
  };

  const updateLocationPin = async (
    viewer: CesiumType.Viewer,
    lat: number,
    lon: number,
    name: string
  ) => {
    const Cesium: typeof CesiumType = await import('cesium');
    if (!viewer || viewer.isDestroyed()) return;

    if (locationPinEntityRef.current) {
      viewer.entities.remove(locationPinEntityRef.current);
      locationPinEntityRef.current = null;
    }

    const pinEntity = viewer.entities.add({
      name: `Analysis Point: ${name}`,
      position: Cesium.Cartesian3.fromDegrees(lon, lat),
      point: {
        pixelSize: 10,
        color: Cesium.Color.fromCssColorString('#00E5FF'),
        outlineColor: Cesium.Color.WHITE,
        outlineWidth: 2,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
      label: {
        text: name.toUpperCase(),
        font: 'bold 11px monospace',
        fillColor: Cesium.Color.WHITE,
        outlineColor: Cesium.Color.fromCssColorString('#08090C'),
        outlineWidth: 3,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
        pixelOffset: new Cesium.Cartesian2(0, -12),
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
      },
    });

    locationPinEntityRef.current = pinEntity;
  };

  // Handle Location changes
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || !isCesiumLoadedRef.current || viewer.isDestroyed()) return;

    flyCameraToCoordinates(viewer, latitude, longitude, 18000, -38);
    updateLocationPin(viewer, latitude, longitude, locationName);
  }, [latitude, longitude, locationName]);

  // Handle GeoJSON inundation polygon updates
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || !isCesiumLoadedRef.current || viewer.isDestroyed()) return;

    if (geojsonDataSourceRef.current) {
      viewer.dataSources.remove(geojsonDataSourceRef.current, true);
      geojsonDataSourceRef.current = null;
    }
    setSelectedPolygonMeta(null);

    if (!geojson || !geojson.features || geojson.features.length === 0) {
      return;
    }

    const currentGeoJson = geojson;

    async function loadGeoJson() {
      if (!viewer || viewer.isDestroyed() || !currentGeoJson) return;
      try {
        const Cesium: typeof CesiumType = await import('cesium');

        const validFeatures = (currentGeoJson.features || []).filter((feat) => {
          const props = feat.properties || {};
          if (props.is_permanent_water === true || props.water_type === 'coastal_ocean') {
            return false;
          }
          return true;
        });

        if (validFeatures.length === 0) {
          flyCameraToCoordinates(viewer, latitude, longitude, 18000, -38);
          return;
        }

        const sanitizedGeoJson = {
          ...currentGeoJson,
          features: validFeatures,
        };

        const dataSource = await Cesium.GeoJsonDataSource.load(sanitizedGeoJson as unknown as Record<string, unknown>, {
          stroke: Cesium.Color.fromCssColorString('#00E5FF'),
          fill: Cesium.Color.fromCssColorString('rgba(0, 180, 216, 0.42)'),
          strokeWidth: 2.5,
          clampToGround: true,
        });

        if (viewer.isDestroyed()) return;
        geojsonDataSourceRef.current = dataSource;
        await viewer.dataSources.add(dataSource);

        viewer.flyTo(dataSource, {
          duration: 2.0,
          offset: new Cesium.HeadingPitchRange(0, Cesium.Math.toRadians(-38), 0),
        });
      } catch (geoErr) {
        console.warn('[HydroWatch Cesium] GeoJSON polygon rendering error:', geoErr);
      }
    }

    loadGeoJson();
  }, [geojson, latitude, longitude]);

  // Map Controls Callbacks
  const handleFocusLocation = () => {
    if (!viewerRef.current) return;
    flyCameraToCoordinates(viewerRef.current, latitude, longitude, 16000, -38);
  };

  const handleFocusInundation = () => {
    if (!viewerRef.current || !geojsonDataSourceRef.current) return;
    viewerRef.current.flyTo(geojsonDataSourceRef.current, { duration: 1.5 });
  };

  const handleResetNorth = async () => {
    if (!viewerRef.current) return;
    const Cesium: typeof CesiumType = await import('cesium');
    const camera = viewerRef.current.camera;
    camera.flyTo({
      destination: camera.position,
      orientation: {
        heading: 0,
        pitch: camera.pitch,
        roll: 0,
      },
      duration: 1.0,
    });
  };

  const handleZoom = (inward: boolean) => {
    if (!viewerRef.current) return;
    const camera = viewerRef.current.camera;
    const moveAmount = camera.positionCartographic.height * 0.35;
    if (inward) {
      camera.zoomIn(moveAmount);
    } else {
      camera.zoomOut(moveAmount);
    }
  };

  const toggleFullscreen = () => {
    if (!wrapperRef.current) return;
    if (!document.fullscreenElement) {
      wrapperRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  // Handle Globe Point Click inspection
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || !isCesiumLoadedRef.current || viewer.isDestroyed()) return;

    const CesiumModule = (window as unknown as { Cesium: typeof CesiumType }).Cesium;
    async function setupGlobeClickHandler() {
      const Cesium = CesiumModule || (await import('cesium'));
      if (!viewerRef.current || viewerRef.current.isDestroyed()) return;
      const currentViewer = viewerRef.current;

      const handler = new Cesium.ScreenSpaceEventHandler(currentViewer.scene.canvas);

      handler.setInputAction((click: { position: CesiumType.Cartesian2 }) => {
        if (!viewerRef.current || viewerRef.current.isDestroyed()) return;
        const v = viewerRef.current;

        const pickedObject = v.scene.pick(click.position);
        if (Cesium.defined(pickedObject) && pickedObject.id && pickedObject.id.properties) {
          const props: Record<string, unknown> = {};
          const propertyNames = pickedObject.id.properties.propertyNames;
          for (const name of propertyNames) {
            props[name] = pickedObject.id.properties[name]?.getValue();
          }
          setSelectedPolygonMeta(props);
          return;
        }

        const cartesian = v.camera.pickEllipsoid(click.position, v.scene.globe.ellipsoid);
        if (cartesian) {
          const cartographic = Cesium.Cartographic.fromCartesian(cartesian);
          const clickedLat = Cesium.Math.toDegrees(cartographic.latitude);
          const clickedLon = Cesium.Math.toDegrees(cartographic.longitude);
          setInspectedLocation({
            lat: clickedLat,
            lon: clickedLon,
            name: `${clickedLat.toFixed(3)}°N, ${clickedLon.toFixed(3)}°E`,
          });
        }
      }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
    }

    setupGlobeClickHandler();
  }, []);

  const RAINFALL_LAYERS: { id: CesiumRainfallLayerId; label: string; badge: string; color: string }[] = [
    { id: 'ai_calibrated', label: 'AI Calibrated', badge: 'Regime-Aware', color: '#00e5ff' },
    { id: 'raw_nwp', label: 'Raw NWP', badge: 'Baseline', color: '#94a3b8' },
    { id: 'bias_delta', label: 'Bias Delta (Δ)', badge: 'Error Corr.', color: '#10b981' },
    { id: 'heavy_prob', label: 'Heavy Rain Prob', badge: '≥64.5mm', color: '#f59e0b' },
    { id: 'regime', label: 'Monsoon Regime', badge: 'Synoptic', color: '#8b5cf6' },
    { id: 'uncertainty', label: 'Uncertainty Width', badge: 'P90 - P10', color: '#ec4899' },
  ];

  return (
    <div
      ref={wrapperRef}
      className={`relative w-full ${
        isFullscreen ? 'h-screen w-screen rounded-none' : 'h-[540px] md:h-[620px] rounded-lg'
      } bg-[#08090c] overflow-hidden border border-[#1e2638] shadow-2xl transition-all`}
    >
      {/* Cesium Canvas Container */}
      <div ref={containerRef} className="w-full h-full" id="cesium-container" />

      {/* Loading Indicator */}
      {isInitializing && (
        <div className="absolute inset-0 bg-[#08090c]/90 flex flex-col items-center justify-center gap-3 z-30">
          <div className="w-8 h-8 border-2 border-[#00e5ff] border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-mono uppercase tracking-widest text-[#94a3b8]">
            Initializing 3D World Globe & Terrain Mesh...
          </p>
        </div>
      )}

      {/* Error Fallback */}
      {errorMessage && (
        <div className="absolute inset-0 bg-[#08090c]/95 flex flex-col items-center justify-center p-6 text-center z-30">
          <AlertTriangle className="w-10 h-10 text-[#f59e0b] mb-2" />
          <h3 className="text-sm font-semibold text-white mb-1">Geospatial View Unavailable</h3>
          <p className="text-xs text-[#94a3b8] max-w-md mb-4">{errorMessage}</p>
        </div>
      )}

      {/* Demo Mode Overlay Banner */}
      {isDemo && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-20 pointer-events-none">
          <div className="flex items-center gap-2 bg-[#0e121a]/90 backdrop-blur-md border border-[#f59e0b]/50 px-3 py-1 rounded-full text-[10px] font-mono text-[#f59e0b] shadow-lg">
            <span className="w-1.5 h-1.5 rounded-full bg-[#f59e0b] animate-pulse" />
            <span className="font-bold uppercase tracking-wider">DEMO DATA · SYNTHETIC / FALLBACK MODE</span>
          </div>
        </div>
      )}

      {/* Floating 6-Layer Selector Bar (Top-Left) */}
      <div className="absolute top-3 left-3 z-20 hidden sm:flex items-center gap-1 bg-[#0a0d14]/90 backdrop-blur-md border border-[#1e2638] p-1 rounded-md shadow-xl">
        <div className="flex items-center gap-1 px-2 py-1 text-[10px] font-mono uppercase text-[#64748b] border-r border-[#1e2638]">
          <Layers className="w-3.5 h-3.5 text-[#00e5ff]" />
          <span>Layer:</span>
        </div>
        {RAINFALL_LAYERS.map((layer) => {
          const isActive = activeLayer === layer.id;
          return (
            <button
              key={layer.id}
              type="button"
              onClick={() => onSelectLayer?.(layer.id)}
              className={`flex items-center gap-1.5 px-2 py-1 rounded text-[11px] font-mono transition-all ${
                isActive
                  ? 'bg-[#151d2d] text-white font-bold border shadow-sm'
                  : 'text-[#94a3b8] hover:text-white hover:bg-[#121622]'
              }`}
              style={{
                borderColor: isActive ? layer.color : 'transparent',
              }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: layer.color }}
              />
              <span>{layer.label}</span>
            </button>
          );
        })}
      </div>

      {/* Minimal Floating Map Controls (Top-Right) */}
      <div className="absolute top-3 right-3 z-20 flex flex-col gap-1.5 bg-[#0e121a]/85 backdrop-blur-md border border-[#1e2638] p-1 rounded-md shadow-lg">
        <button
          type="button"
          onClick={handleFocusLocation}
          title="Center on Selected Location"
          className="p-1.5 rounded hover:bg-[#1b2234] text-[#94a3b8] hover:text-[#00e5ff] transition-colors"
        >
          <Crosshair className="w-4 h-4" />
        </button>
        {polygonCount > 0 && (
          <button
            type="button"
            onClick={handleFocusInundation}
            title="Fit to Detected Water Extent"
            className="p-1.5 rounded hover:bg-[#1b2234] text-[#00e5ff] hover:text-white transition-colors"
          >
            <Layers className="w-4 h-4" />
          </button>
        )}
        <button
          type="button"
          onClick={handleResetNorth}
          title="Reset North Heading"
          className="p-1.5 rounded hover:bg-[#1b2234] text-[#94a3b8] hover:text-white transition-colors"
        >
          <Compass className="w-4 h-4" />
        </button>
        <div className="border-t border-[#1e2638] my-0.5" />
        <button
          type="button"
          onClick={() => handleZoom(true)}
          title="Zoom In"
          className="p-1.5 rounded hover:bg-[#1b2234] text-[#94a3b8] hover:text-white transition-colors"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => handleZoom(false)}
          title="Zoom Out"
          className="p-1.5 rounded hover:bg-[#1b2234] text-[#94a3b8] hover:text-white transition-colors"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={toggleFullscreen}
          title="Toggle Fullscreen"
          className="p-1.5 rounded hover:bg-[#1b2234] text-[#94a3b8] hover:text-white transition-colors"
        >
          {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
        </button>
      </div>

      {/* Geospatial Active Layer Dynamic Legend (Bottom-Left) */}
      <div className="absolute bottom-3 left-3 z-20 bg-[#0e121a]/90 backdrop-blur-md border border-[#1e2638] px-3 py-2 rounded-md shadow-lg text-[11px] font-mono space-y-1.5 max-w-xs">
        <div className="flex items-center justify-between border-b border-[#1e2638] pb-1">
          <div className="flex items-center gap-1.5">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{
                backgroundColor:
                  activeLayer === 'ai_calibrated'
                    ? '#00e5ff'
                    : activeLayer === 'bias_delta'
                    ? '#10b981'
                    : activeLayer === 'heavy_prob'
                    ? '#f59e0b'
                    : activeLayer === 'regime'
                    ? '#8b5cf6'
                    : activeLayer === 'uncertainty'
                    ? '#ec4899'
                    : '#94a3b8',
              }}
            />
            <span className="text-white font-bold uppercase text-[10px]">
              {RAINFALL_LAYERS.find((l) => l.id === activeLayer)?.label || 'Rainfall Layer'}
            </span>
          </div>
          <span className="text-[10px] text-[#00e5ff] uppercase font-bold">
            {locationName}
          </span>
        </div>

        {/* Dynamic Scale indicator according to activeLayer */}
        {activeLayer === 'ai_calibrated' && (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-[10px] text-[#cbd5e1]">
              <span>Calibrated 24h:</span>
              <span className="font-bold text-[#00e5ff]">{formatNumber(forecastSummary?.correctedMm ?? 0, 1)} mm</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-gradient-to-r from-[#0284c7]/40 via-[#00e5ff] to-[#f59e0b]" />
            <div className="flex justify-between text-[9px] text-[#64748b]">
              <span>0mm</span>
              <span>35mm</span>
              <span>64.5mm</span>
              <span>115.5mm+</span>
            </div>
          </div>
        )}

        {activeLayer === 'raw_nwp' && (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-[10px] text-[#cbd5e1]">
              <span>Raw NWP (Baseline):</span>
              <span className="font-bold text-white">{formatNumber(forecastSummary?.rawNwpMm ?? 0, 1)} mm</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-gradient-to-r from-[#334155] via-[#64748b] to-[#94a3b8]" />
            <div className="flex justify-between text-[9px] text-[#64748b]">
              <span>0mm</span>
              <span>30mm</span>
              <span>60mm</span>
              <span>100mm+</span>
            </div>
          </div>
        )}

        {activeLayer === 'bias_delta' && (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-[10px] text-[#cbd5e1]">
              <span>AI Correction Δ:</span>
              <span className="font-bold text-[#10b981]">
                {(forecastSummary?.deltaMm ?? 0) >= 0 ? '+' : ''}
                {formatNumber(forecastSummary?.deltaMm ?? 0, 1)} mm
              </span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-gradient-to-r from-[#ef4444] via-[#64748b] to-[#10b981]" />
            <div className="flex justify-between text-[9px] text-[#64748b]">
              <span>-30mm (Dampen)</span>
              <span>0mm</span>
              <span>+30mm (Enhance)</span>
            </div>
          </div>
        )}

        {activeLayer === 'heavy_prob' && (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-[10px] text-[#cbd5e1]">
              <span>P(≥64.5mm Heavy):</span>
              <span className="font-bold text-[#f59e0b]">{Math.round((forecastSummary?.heavyProb ?? 0) * 100)}%</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-gradient-to-r from-[#1e293b] via-[#f59e0b] to-[#ef4444]" />
            <div className="flex justify-between text-[9px] text-[#64748b]">
              <span>0% Low</span>
              <span>50% Watch</span>
              <span>80%+ Warning</span>
            </div>
          </div>
        )}

        {activeLayer === 'regime' && (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-[10px] text-[#cbd5e1]">
              <span>Monsoon Regime:</span>
              <span className="font-bold text-[#8b5cf6]">{forecastSummary?.regime || 'Active Monsoon'}</span>
            </div>
            <div className="text-[9px] text-[#94a3b8]">
              Synoptically diagnosed dynamical regime
            </div>
          </div>
        )}

        {activeLayer === 'uncertainty' && (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-[10px] text-[#cbd5e1]">
              <span>Uncertainty Width:</span>
              <span className="font-bold text-[#ec4899]">{formatNumber(forecastSummary?.uncertaintyWidth ?? 0, 1)} mm</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-gradient-to-r from-[#0284c7] via-[#ec4899] to-[#ef4444]" />
            <div className="flex justify-between text-[9px] text-[#64748b]">
              <span>Narrow (High Conf)</span>
              <span>Wide (Spread)</span>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between text-[9px] text-[#64748b] pt-1 border-t border-[#1e2638]">
          <span className="flex items-center gap-1">
            <span className={`w-1.5 h-1.5 rounded-full ${terrainLoaded ? 'bg-[#10b981]' : 'bg-[#94a3b8]'}`} />
            3D Terrain
          </span>
          <span className="flex items-center gap-1">
            <span className={`w-1.5 h-1.5 rounded-full ${satelliteLoaded ? 'bg-[#10b981]' : 'bg-[#94a3b8]'}`} />
            Esri World Imagery
          </span>
        </div>
      </div>

      {/* Inspected Point Popover (When clicking anywhere on the globe) */}
      {inspectedLocation && (
        <div className="absolute top-14 right-3 z-20 bg-[#0f131d]/95 backdrop-blur-md border border-[#00e5ff]/50 p-3.5 rounded-md shadow-2xl max-w-xs text-xs space-y-2">
          <div className="flex items-center justify-between border-b border-[#1e2638] pb-1.5">
            <div className="flex items-center gap-1.5 text-[#00e5ff] font-mono font-bold uppercase tracking-wide text-[11px]">
              <MapPin className="w-3.5 h-3.5" />
              <span>Inspected Coordinates</span>
            </div>
            <button
              type="button"
              onClick={() => setInspectedLocation(null)}
              className="text-[#64748b] hover:text-white text-xs px-1"
            >
              ✕
            </button>
          </div>

          <div className="space-y-1 font-mono text-[11px]">
            <div className="flex justify-between">
              <span className="text-[#94a3b8]">Lat / Lon:</span>
              <span className="text-white font-semibold">{formatCoordinates(inspectedLocation.lat, inspectedLocation.lon)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#94a3b8]">Regime:</span>
              <span className="text-[#8b5cf6] font-semibold">{forecastSummary?.regime || 'Active Monsoon'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#94a3b8]">Raw NWP:</span>
              <span className="text-white">{formatNumber(forecastSummary?.rawNwpMm ?? 0, 1)} mm</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#94a3b8]">AI Calibrated:</span>
              <span className="text-[#00e5ff] font-bold">{formatNumber(forecastSummary?.correctedMm ?? 0, 1)} mm</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#94a3b8]">Bias Delta (Δ):</span>
              <span className="text-[#10b981]">
                {(forecastSummary?.deltaMm ?? 0) >= 0 ? '+' : ''}
                {formatNumber(forecastSummary?.deltaMm ?? 0, 1)} mm
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#94a3b8]">Heavy Rain Prob:</span>
              <span className="text-[#f59e0b] font-semibold">{Math.round((forecastSummary?.heavyProb ?? 0) * 100)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#94a3b8]">Data Status:</span>
              <span className="text-[#f59e0b] font-semibold">{isDemo ? 'DEMO FALLBACK' : 'OPERATIONAL'}</span>
            </div>
          </div>

          <div className="text-[10px] text-[#64748b] border-t border-[#1e2638] pt-1 mt-1">
            Click any point on the 3D globe to inspect local forecast & regime telemetry.
          </div>
        </div>
      )}

      {/* Polygon Inspection Popover (when user clicks an inundation vector) */}
      {selectedPolygonMeta && (
        <div className="absolute top-14 left-3 z-20 bg-[#0f131d]/95 backdrop-blur-md border border-[#00e5ff]/40 p-3 rounded-md shadow-2xl max-w-xs text-xs">
          <div className="flex items-center justify-between border-b border-[#1e2638] pb-1.5 mb-2">
            <span className="font-bold text-[#00e5ff] uppercase tracking-wider text-[11px]">
              Detected Surface Water Polygon
            </span>
            <button
              type="button"
              onClick={() => setSelectedPolygonMeta(null)}
              className="text-[#64748b] hover:text-white text-xs px-1"
            >
              ✕
            </button>
          </div>
          <div className="space-y-1 font-mono text-[11px]">
            {selectedPolygonMeta.flooded_area_sq_m !== undefined && (
              <div className="flex justify-between">
                <span className="text-[#94a3b8]">Surface Area:</span>
                <span className="text-white font-semibold">
                  {(Number(selectedPolygonMeta.flooded_area_sq_m) / 1000000).toFixed(4)} km²
                </span>
              </div>
            )}
            {selectedPolygonMeta.water_type !== undefined && (
              <div className="flex justify-between">
                <span className="text-[#94a3b8]">Classification:</span>
                <span className="text-[#00e5ff] capitalize font-medium">
                  {String(selectedPolygonMeta.water_type).replace('_', ' ')}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
