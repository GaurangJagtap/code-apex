import React, { useEffect, useState } from 'react';
import { useParams, NavLink } from 'react-router-dom';
import {
  Bug,
  ArrowLeft,
  Download,
  FileCode,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Camera,
  ExternalLink,
  Layers,
  Terminal
} from 'lucide-react';
import { fetchBug, BugFinding } from '../api/client';

export const BugDetail: React.FC = () => {
  const { bugId } = useParams<{ bugId: string }>();
  const [bug, setBug] = useState<BugFinding | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!bugId) return;
    fetchBug(bugId)
      .then(setBug)
      .catch(err => setError(err.message || 'Finding not found'))
      .finally(() => setLoading(false));
  }, [bugId]);

  if (loading) {
    return <div className="p-12 text-center text-sm text-[#94a3b8]">Loading proof-carrying bug report...</div>;
  }

  if (error || !bug) {
    return (
      <div className="p-8 max-w-2xl mx-auto text-center space-y-4">
        <div className="text-rose-600 font-bold">Error loading bug report</div>
        <p className="text-sm text-[#64748b]">{error}</p>
        <NavLink to="/bugs" className="text-xs text-[#047857] underline">
          &larr; Back to Bug Reports
        </NavLink>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Top Breadcrumb & Export Actions */}
      <div className="flex items-center justify-between">
        <NavLink
          to="/bugs"
          className="text-xs font-semibold text-[#047857] hover:underline flex items-center gap-1.5"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Bug Reports</span>
        </NavLink>

        <div className="flex items-center gap-2">
          <a
            href={`/api/v1/bugs/${bug.id}/export?format=markdown`}
            target="_blank"
            rel="noreferrer"
            className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-[#cbd5e1] bg-white hover:bg-slate-50 flex items-center gap-1.5 text-[#334155] shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-emerald-700" />
            <span>Export Markdown</span>
          </a>
          <a
            href={`/api/v1/bugs/${bug.id}/export?format=html`}
            target="_blank"
            rel="noreferrer"
            className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-[#cbd5e1] bg-white hover:bg-slate-50 flex items-center gap-1.5 text-[#334155] shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export HTML</span>
          </a>
          <a
            href={`/api/v1/bugs/${bug.id}/export?format=json`}
            target="_blank"
            rel="noreferrer"
            className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-[#cbd5e1] bg-white hover:bg-slate-50 flex items-center gap-1.5 text-[#334155] shadow-sm"
          >
            <FileCode className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </a>
        </div>
      </div>

      {/* Main Report Card */}
      <div className="bg-white rounded-xl border border-[#e2e8f0] shadow-sm overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-[#e2e8f0] bg-[#f8fafc]">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span
              className={`text-xs font-bold px-2.5 py-0.5 rounded uppercase tracking-wider ${
                bug.severity === 'Critical'
                  ? 'bg-rose-100 text-rose-800 border border-rose-300'
                  : bug.severity === 'High'
                  ? 'bg-amber-100 text-amber-800 border border-amber-300'
                  : 'bg-blue-100 text-blue-800 border border-blue-300'
              }`}
            >
              {bug.severity} Severity
            </span>
            <span
              className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                bug.status === 'Verified' || bug.status === 'Confirmed'
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                  : bug.status === 'Likely'
                  ? 'bg-amber-100 text-amber-800 border border-amber-300'
                  : bug.status === 'Inconclusive'
                  ? 'bg-purple-100 text-purple-800 border border-purple-300'
                  : 'bg-rose-100 text-rose-800 border border-rose-300'
              }`}
            >
              {bug.status}
            </span>
            <span className="text-xs font-mono text-[#64748b]">ID: {bug.id}</span>
          </div>

          <h2 className="text-xl font-bold text-[#0f172a]">{bug.title}</h2>
          <div className="text-xs text-[#64748b] mt-1 flex flex-wrap items-center gap-3">
            <span>Affected Route: <code>{bug.affected_url}</code></span>
            <span>&bull;</span>
            <span>Associated Run: <NavLink to={`/runs?selected=${bug.run_id}`} className="text-[#047857] underline">{bug.run_id}</NavLink></span>
            <span>&bull;</span>
            <span>Confidence: {(bug.confidence_score * 100).toFixed(0)}%</span>
          </div>
        </div>

        {/* Report Content */}
        <div className="p-6 space-y-6 text-sm text-[#334155]">
          {/* Verification & Reproducibility Rationale */}
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
            <h4 className="font-bold text-xs text-[#065f46] uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-700" />
              Reproducibility Verification Notes
            </h4>
            <p className="text-xs text-[#064e3b] mt-1">{bug.verification_notes}</p>
            <div className="text-[11px] text-[#047857] mt-2 font-mono">
              Replay Sessions: {bug.replay_attempts} independent cycles executed & verified.
            </div>
          </div>

          {/* Severity Rationale */}
          {bug.severity_reason && (
            <div>
              <h4 className="text-xs font-bold text-[#64748b] uppercase tracking-wider mb-1">Severity Assignment Rationale</h4>
              <p className="text-xs bg-[#f8fafc] p-3 rounded-lg border border-[#e2e8f0]">{bug.severity_reason}</p>
            </div>
          )}

          {/* Numbered Steps to Reproduce */}
          <div>
            <h4 className="text-xs font-bold text-[#64748b] uppercase tracking-wider mb-2">Step-by-Step Reproduction Instructions</h4>
            <ol className="list-decimal pl-5 space-y-1.5 bg-[#f8fafc] p-4 rounded-lg border border-[#e2e8f0] text-xs font-mono">
              {bug.reproduction_steps.map((step, idx) => (
                <li key={idx} className="text-[#1e293b]">{step}</li>
              ))}
            </ol>
          </div>

          {/* Expected vs Actual Behavior Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-emerald-200 bg-emerald-50/50 rounded-xl p-4">
              <h4 className="text-xs font-bold text-emerald-800 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Expected Behavior
              </h4>
              <p className="text-xs text-emerald-950">{bug.expected_behavior}</p>
            </div>

            <div className="border border-rose-200 bg-rose-50/50 rounded-xl p-4">
              <h4 className="text-xs font-bold text-rose-800 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <XCircle className="w-4 h-4 text-rose-600" />
                Actual Observed Defect
              </h4>
              <p className="text-xs text-rose-950 font-mono">{bug.actual_behavior}</p>
            </div>
          </div>

          {/* Failure Screenshot Evidence */}
          {bug.screenshot_url && (
            <div>
              <h4 className="text-xs font-bold text-[#64748b] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Camera className="w-4 h-4 text-[#047857]" />
                Captured Evidence Screenshot
              </h4>
              <div className="border border-[#cbd5e1] rounded-xl overflow-hidden shadow-sm">
                <img
                  src={bug.screenshot_url}
                  alt="Defect screenshot"
                  className="w-full max-h-[500px] object-contain bg-slate-900"
                />
              </div>
            </div>
          )}

          {/* Browser Console & Page Errors */}
          {bug.console_errors?.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-[#64748b] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Terminal className="w-4 h-4 text-[#dc2626]" />
                Browser Console Errors
              </h4>
              <pre className="bg-[#0f172a] text-rose-400 p-3 rounded-lg text-xs font-mono whitespace-pre-wrap max-h-36 overflow-y-auto">
                {bug.console_errors.join('\n')}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
