'use client';

import React from 'react';
import { Activity, Globe, Radio, BarChart3, Sparkles } from 'lucide-react';
import { formatCoordinates, formatTimestamp } from '@/lib/formatters';
import { PostProcessingModelId } from '@/lib/types';

interface HeaderProps {
  locationName: string;
  latitude: number;
  longitude: number;
  generatedAt?: string | null;
  isBackendHealthy: boolean;
  streamsOnlineCount?: number;
  selectedModel?: PostProcessingModelId;
  onSelectModel?: (model: PostProcessingModelId) => void;
  onOpenVerificationModal?: () => void;
  isDemo?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  locationName,
  latitude,
  longitude,
  generatedAt,
  isBackendHealthy,
  streamsOnlineCount = 4,
  selectedModel = 'regime_aware_ml',
  onSelectModel,
  onOpenVerificationModal,
  isDemo = true,
}) => {
  const POST_PROCESSING_MODELS: { id: PostProcessingModelId; label: string; badge: string; color: string }[] = [
    { id: 'raw_nwp', label: 'Raw NWP', badge: 'Baseline', color: '#94a3b8' },
    { id: 'quantile_mapping', label: 'EQM', badge: 'Quantile', color: '#06b6d4' },
    { id: 'global_ml', label: 'Global ML', badge: 'Stationary', color: '#f59e0b' },
    { id: 'regime_aware_ml', label: 'Regime-Aware AI', badge: 'PS26080', color: '#00e5ff' },
  ];

  return (
    <header className="sticky top-0 z-40 w-full bg-[#0a0c12]/95 backdrop-blur-md border-b border-[#1e2638] px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-sm">
      {/* Brand & Product Identity */}
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-8 h-8 rounded-md bg-[#0284c7]/20 border border-[#00e5ff]/40 text-[#00e5ff]">
          <Activity className="w-4 h-4 text-[#00e5ff]" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold tracking-wider text-base text-white">HydroWatch AI</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#1e2638] text-[#00e5ff] uppercase tracking-widest border border-[#00e5ff]/30">
              MoES · NCMRWF
            </span>
            {isDemo && (
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#f59e0b]/15 text-[#f59e0b] border border-[#f59e0b]/30 font-semibold uppercase">
                Demo Mode
              </span>
            )}
          </div>
          <p className="text-[11px] text-[#64748b] tracking-wide uppercase font-medium">
            Regime-Aware AI Post-Processing of Monsoon Rainfall (PS26080)
          </p>
        </div>
      </div>

      {/* Model Selection Switcher Bar */}
      <div className="flex items-center gap-1 bg-[#10141e] border border-[#1e2638] p-1 rounded-md">
        <div className="hidden lg:flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono uppercase text-[#64748b] border-r border-[#1e2638]">
          <Sparkles className="w-3 h-3 text-[#00e5ff]" />
          <span>Active Post-Processor:</span>
        </div>
        {POST_PROCESSING_MODELS.map((m) => {
          const isActive = selectedModel === m.id;
          return (
            <button
              key={m.id}
              type="button"
              onClick={() => onSelectModel?.(m.id)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono transition-all ${
                isActive
                  ? 'bg-[#151d2d] text-white font-bold border shadow-sm'
                  : 'text-[#94a3b8] hover:text-white hover:bg-[#121622]'
              }`}
              style={{
                borderColor: isActive ? m.color : 'transparent',
              }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: m.color }}
              />
              <span>{m.label}</span>
              <span
                className="text-[9px] font-normal px-1 rounded uppercase tracking-wider hidden sm:inline"
                style={{
                  color: m.color,
                  backgroundColor: `${m.color}15`,
                }}
              >
                {m.badge}
              </span>
            </button>
          );
        })}
      </div>

      {/* Action Controls & Provenance Status */}
      <div className="flex items-center gap-2.5 text-xs">
        {/* Verification Hub Button */}
        <button
          type="button"
          onClick={onOpenVerificationModal}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#10141e] hover:bg-[#182030] border border-[#00e5ff]/40 hover:border-[#00e5ff] text-[#00e5ff] text-xs font-mono font-semibold transition-all shadow-sm"
          title="Open Post-Processing Verification & Verification Hub"
        >
          <BarChart3 className="w-3.5 h-3.5" />
          <span>Verification Hub</span>
        </button>

        {/* Target Location & Coordinates */}
        <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-md bg-[#10141e] border border-[#1e2638] text-xs">
          <Globe className="w-3.5 h-3.5 text-[#00e5ff]" />
          <span className="text-white font-medium">{locationName}</span>
          <span className="text-[#64748b]">·</span>
          <span className="font-mono text-[#94a3b8]">{formatCoordinates(latitude, longitude)}</span>
        </div>

        {/* Gateway Telemetry Indicator */}
        <div className="flex items-center gap-2 px-2.5 py-1.5 rounded bg-[#10141e] border border-[#1e2638]">
          <Radio className={`w-3.5 h-3.5 ${isBackendHealthy ? 'text-[#10b981]' : 'text-[#ef4444]'}`} />
          <span className="text-[#cbd5e1] font-mono text-[11px] hidden sm:inline">
            {isBackendHealthy ? `${streamsOnlineCount}/4 ACTIVE` : 'OFFLINE'}
          </span>
          <span
            className={`w-2 h-2 rounded-full ${
              isBackendHealthy ? 'bg-[#10b981] animate-pulse-subtle' : 'bg-[#ef4444]'
            }`}
          />
        </div>
      </div>
    </header>
  );
};
