import React, { useEffect, useState } from 'react';
import {
  Settings as SettingsIcon,
  Shield,
  Cpu,
  Sliders,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Terminal,
  RefreshCw
} from 'lucide-react';
import { fetchConfigStatus, ConfigStatus } from '../api/client';

export const Settings: React.FC = () => {
  const [config, setConfig] = useState<ConfigStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchConfigStatus()
      .then(setConfig)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold text-[#0f172a] flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-[#047857]" />
          Platform Settings & Configuration
        </h2>
        <p className="text-xs text-[#64748b] mt-0.5">
          Inspect active AI providers, Playwright browser limits, security boundaries, and local demonstration defaults.
        </p>
      </div>

      {/* AI Provider Configuration */}
      <div className="bg-white p-6 rounded-xl border border-[#e2e8f0] shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#e2e8f0]">
          <h3 className="font-semibold text-sm text-[#0f172a] flex items-center gap-2">
            <Cpu className="w-4 h-4 text-[#047857]" />
            AI Reasoning Engine Status
          </h3>
          <span
            className={`text-xs font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider ${
              config?.demo_mode_active
                ? 'bg-amber-100 text-amber-800'
                : 'bg-emerald-100 text-emerald-800'
            }`}
          >
            {config?.demo_mode_active ? 'Deterministic Demo Mode' : 'Real AI Connected'}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-3 bg-[#f8fafc] rounded-lg border border-[#e2e8f0]">
            <span className="text-[#64748b] font-medium block">Configured Provider:</span>
            <strong className="text-[#0f172a] text-sm capitalize">{config?.llm_provider || 'demo'}</strong>
          </div>
          <div className="p-3 bg-[#f8fafc] rounded-lg border border-[#e2e8f0]">
            <span className="text-[#64748b] font-medium block">Active Model:</span>
            <strong className="text-[#0f172a] text-sm font-mono">{config?.llm_model || 'N/A'}</strong>
          </div>
          <div className="p-3 bg-[#f8fafc] rounded-lg border border-[#e2e8f0]">
            <span className="text-[#64748b] font-medium block">API Key Status:</span>
            <strong className="text-[#0f172a] text-sm font-mono">
              {config?.api_key_configured ? config.api_key_masked : 'None (Using Local Demo Mode)'}
            </strong>
          </div>
          <div className="p-3 bg-[#f8fafc] rounded-lg border border-[#e2e8f0]">
            <span className="text-[#64748b] font-medium block">Structured Output Schema:</span>
            <strong className="text-emerald-700 text-sm">Pydantic Schema Validation Active</strong>
          </div>
        </div>

        <div className="text-[11px] text-[#64748b] bg-slate-50 p-3 rounded-lg border border-slate-200">
          <strong>How to enable Real AI Mode:</strong> Set <code>LLM_PROVIDER=gemini</code> and <code>LLM_API_KEY=your_key</code> in your <code>.env</code> file. No raw keys are ever displayed in UI or logged in reports.
        </div>
      </div>

      {/* Security & Boundaries */}
      <div className="bg-white p-6 rounded-xl border border-[#e2e8f0] shadow-sm space-y-4">
        <h3 className="font-semibold text-sm text-[#0f172a] flex items-center gap-2 pb-3 border-b border-[#e2e8f0]">
          <Shield className="w-4 h-4 text-[#047857]" />
          Target Whitelist & SSRF Security Boundaries
        </h3>

        <div className="space-y-2 text-xs">
          <p className="text-[#64748b]">
            To prevent SSRF and unauthorized cloud metadata access, tests are restricted to approved local targets:
          </p>
          <div className="flex flex-wrap gap-2">
            {config?.allowed_hosts.map(h => (
              <span key={h} className="bg-slate-100 text-slate-800 font-mono text-xs px-2.5 py-1 rounded border border-slate-200">
                {h}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Execution Limits */}
      <div className="bg-white p-6 rounded-xl border border-[#e2e8f0] shadow-sm space-y-4">
        <h3 className="font-semibold text-sm text-[#0f172a] flex items-center gap-2 pb-3 border-b border-[#e2e8f0]">
          <Sliders className="w-4 h-4 text-[#047857]" />
          Browser Execution Budgets
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 bg-[#f8fafc] rounded-lg border border-[#e2e8f0]">
            <span className="text-[#64748b] block">Max Pages</span>
            <strong className="text-sm text-[#0f172a]">{config?.boundaries.max_pages || 10}</strong>
          </div>
          <div className="p-3 bg-[#f8fafc] rounded-lg border border-[#e2e8f0]">
            <span className="text-[#64748b] block">Max Actions</span>
            <strong className="text-sm text-[#0f172a]">{config?.boundaries.max_actions || 30}</strong>
          </div>
          <div className="p-3 bg-[#f8fafc] rounded-lg border border-[#e2e8f0]">
            <span className="text-[#64748b] block">Max Duration</span>
            <strong className="text-sm text-[#0f172a]">{config?.boundaries.max_duration_sec || 300}s</strong>
          </div>
          <div className="p-3 bg-[#f8fafc] rounded-lg border border-[#e2e8f0]">
            <span className="text-[#64748b] block">Replay Retries</span>
            <strong className="text-sm text-[#0f172a]">{config?.boundaries.max_retries || 2}</strong>
          </div>
        </div>
      </div>
    </div>
  );
};
