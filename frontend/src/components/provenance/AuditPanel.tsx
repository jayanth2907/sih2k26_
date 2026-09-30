'use client';

import React, { useState } from 'react';
import { Terminal, ChevronDown, ChevronUp, Copy, Check, FileJson, ShieldCheck, Database } from 'lucide-react';
import { UnifiedPredictionResponse, PostProcessingModelId } from '@/lib/types';
import { formatTimestamp } from '@/lib/formatters';
import { extractProvenance } from '@/lib/provenance';

interface AuditPanelProps {
  data?: UnifiedPredictionResponse | null;
  selectedModel?: PostProcessingModelId;
  isDemo?: boolean;
}

export const AuditPanel: React.FC<AuditPanelProps> = ({
  data,
  selectedModel = 'regime_aware_ml',
  isDemo = true,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!data) return null;

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const prov = extractProvenance(data, isDemo, selectedModel);

  return (
    <div className="bg-[#0b0e16] border border-[#1e2638] rounded-lg shadow-xl overflow-hidden text-xs">
      {/* Accordion Toggle Bar */}
      <button
        type="button"
        id="audit-panel-toggle"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-3 bg-[#101420] hover:bg-[#141928] border-b border-[#1e2638] transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-[#00e5ff]" />
          <span className="font-bold text-white uppercase tracking-wider">
            Scientific Data Provenance & Operational Audit
          </span>
          <span
            className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
              isDemo
                ? 'bg-[#f59e0b]/15 text-[#f59e0b] border border-[#f59e0b]/30'
                : 'bg-[#10b981]/15 text-[#10b981] border border-[#10b981]/30'
            }`}
          >
            {isDemo ? 'DEMO MODE' : 'OPERATIONAL'}
          </span>
        </div>
        <div className="flex items-center gap-2 text-[#94a3b8]">
          <span className="text-[11px] font-mono hidden sm:inline">
            {isOpen ? 'Collapse Provenance Details' : 'Inspect Source Provenance & Raw JSON'}
          </span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Expanded Content */}
      {isOpen && (
        <div className="p-4 space-y-4">
          {/* 1. Mandatory Data Provenance Grid */}
          <div className="bg-[#121622] border border-[#1e2638] rounded-lg p-3.5 space-y-2">
            <div className="text-xs font-mono uppercase text-[#00e5ff] font-bold flex items-center gap-1.5 border-b border-[#1e2638] pb-1.5">
              <ShieldCheck className="w-4 h-4 text-[#00e5ff]" />
              Data Provenance & Operational Authenticity Ledger
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 font-mono text-[11px] pt-1">
              <div className="bg-[#0b0e16] p-2 rounded border border-[#1e2638]">
                <span className="text-[#64748b] block text-[10px] uppercase">NWP Numerical Data Source</span>
                <span className={`font-bold ${isDemo ? 'text-[#f59e0b]' : 'text-white'}`}>{prov.forecastSource}</span>
              </div>

              <div className="bg-[#0b0e16] p-2 rounded border border-[#1e2638]">
                <span className="text-[#64748b] block text-[10px] uppercase">Observation Target</span>
                <span className="text-white font-bold">{prov.observationSource}</span>
              </div>

              <div className="bg-[#0b0e16] p-2 rounded border border-[#1e2638]">
                <span className="text-[#64748b] block text-[10px] uppercase">Regime Intelligence</span>
                <span className="text-[#8b5cf6] font-bold">{prov.regimeSource}</span>
              </div>

              <div className="bg-[#0b0e16] p-2 rounded border border-[#1e2638]">
                <span className="text-[#64748b] block text-[10px] uppercase">AI Post-Processor</span>
                <span className="text-[#00e5ff] font-bold">{prov.postProcessorModel}</span>
              </div>

              <div className="bg-[#0b0e16] p-2 rounded border border-[#1e2638]">
                <span className="text-[#64748b] block text-[10px] uppercase">Forecast Initialization</span>
                <span className="text-[#cbd5e1]">{prov.forecastInit}</span>
              </div>

              <div className="bg-[#0b0e16] p-2 rounded border border-[#1e2638]">
                <span className="text-[#64748b] block text-[10px] uppercase">Forecast Lead Time / Horizon</span>
                <span className="text-[#10b981] font-bold">{prov.leadTime}</span>
              </div>
            </div>

            <div className="bg-[#0e121a] p-2 rounded border border-[#1e2638] text-[10px] font-mono text-[#94a3b8] flex items-center justify-between">
              <span>Provenance Classification:</span>
              <span className={`font-bold uppercase ${isDemo ? 'text-[#f59e0b]' : 'text-[#10b981]'}`}>
                {prov.statusLabel}
              </span>
            </div>
          </div>

          {/* 2. Model Latencies & System Diagnostics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Active Model Versions */}
            <div className="bg-[#121622] border border-[#1e2638] p-3 rounded space-y-1.5">
              <div className="text-[10px] font-mono uppercase text-[#64748b] flex items-center gap-1 font-semibold">
                <Terminal className="w-3.5 h-3.5 text-[#00e5ff]" />
                Registered Model Checkpoints
              </div>
              <div className="font-mono text-[11px] space-y-1">
                {Object.entries(data.provenance?.model_versions || {}).map(([model, ver]) => (
                  <div key={model} className="flex justify-between border-b border-[#1e2638]/50 pb-0.5">
                    <span className="text-[#94a3b8]">{model}:</span>
                    <span className="text-white truncate max-w-[160px]" title={ver}>
                      {ver}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Ingestion Timing Breakdown */}
            <div className="bg-[#121622] border border-[#1e2638] p-3 rounded space-y-1.5">
              <div className="text-[10px] font-mono uppercase text-[#64748b] font-semibold">
                Pipeline Execution Latencies
              </div>
              <div className="font-mono text-[11px] space-y-1">
                {Object.entries(data.timing || {}).map(([stage, ms]) => (
                  <div key={stage} className="flex justify-between border-b border-[#1e2638]/50 pb-0.5">
                    <span className="text-[#94a3b8]">{stage.replace('_ms', '')}:</span>
                    <span className="text-white">{Math.round(ms)} ms</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 3. Raw JSON Inspection */}
          <div className="space-y-1.5 pt-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase text-[#64748b]">
                <FileJson className="w-3.5 h-3.5 text-[#00e5ff]" />
                Raw Backend Payload Response (POST /api/v1/predict)
              </div>
              <button
                type="button"
                onClick={handleCopyJson}
                className="flex items-center gap-1 text-[11px] font-mono text-[#00e5ff] hover:underline"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-[#10b981]" /> Copied to Clipboard
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" /> Copy JSON Payload
                  </>
                )}
              </button>
            </div>
            <pre className="bg-[#080a10] border border-[#1e2638] rounded p-3 font-mono text-[11px] text-[#cbd5e1] max-h-64 overflow-y-auto leading-relaxed">
              {JSON.stringify(data, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
