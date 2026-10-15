import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  Bug,
  Filter,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ExternalLink,
  ShieldAlert,
  Search
} from 'lucide-react';
import { fetchBugs, BugFinding } from '../api/client';

export const BugReports: React.FC = () => {
  const [bugs, setBugs] = useState<BugFinding[]>([]);
  const [severityFilter, setSeverityFilter] = useState<string>('All');
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBugs()
      .then(setBugs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filteredBugs = bugs.filter(b => {
    if (severityFilter !== 'All' && b.severity !== severityFilter) return false;
    if (statusFilter !== 'All' && b.status !== statusFilter) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      return b.title.toLowerCase().includes(q) || b.id.toLowerCase().includes(q) || b.affected_url.toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-[#e2e8f0] shadow-sm">
        <div>
          <h2 className="text-lg font-bold text-[#0f172a] flex items-center gap-2">
            <Bug className="w-5 h-5 text-[#dc2626]" />
            Proof-Carrying Bug Reports
          </h2>
          <p className="text-xs text-[#64748b] mt-0.5">
            Verified software defects backed by replay attempts, deterministic assertions, and screenshot evidence.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-[#94a3b8] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search defects..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="text-xs pl-8 pr-3 py-1.5 border border-[#cbd5e1] rounded-lg bg-white focus:outline-none focus:border-[#047857]"
            />
          </div>

          <select
            value={severityFilter}
            onChange={e => setSeverityFilter(e.target.value)}
            className="text-xs border border-[#cbd5e1] rounded-lg px-2.5 py-1.5 bg-white text-[#334155]"
          >
            <option value="All">All Severities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>

          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="text-xs border border-[#cbd5e1] rounded-lg px-2.5 py-1.5 bg-white text-[#334155]"
          >
            <option value="All">All Statuses</option>
            <option value="Confirmed">Confirmed</option>
            <option value="Suspected">Suspected</option>
            <option value="Inconclusive">Inconclusive</option>
            <option value="Not Reproducible">Not Reproducible</option>
          </select>
        </div>
      </div>

      {/* Findings List */}
      <div className="bg-white rounded-xl border border-[#e2e8f0] shadow-sm overflow-hidden">
        {filteredBugs.length === 0 ? (
          <div className="p-12 text-center text-sm text-[#94a3b8]">
            {loading ? 'Loading findings...' : 'No bug reports matching the selected filters.'}
          </div>
        ) : (
          <div className="divide-y divide-[#e2e8f0]">
            {filteredBugs.map(bug => (
              <div key={bug.id} className="p-5 hover:bg-[#f8fafc] transition-colors flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                        bug.severity === 'Critical'
                          ? 'bg-rose-100 text-rose-800 border border-rose-300'
                          : bug.severity === 'High'
                          ? 'bg-amber-100 text-amber-800 border border-amber-300'
                          : 'bg-blue-100 text-blue-800 border border-blue-300'
                      }`}
                    >
                      {bug.severity}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        bug.status === 'Confirmed'
                          ? 'bg-emerald-100 text-emerald-800'
                          : bug.status === 'Suspected'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {bug.status}
                    </span>
                    <span className="text-xs font-mono text-[#64748b]">Run: {bug.run_id}</span>
                  </div>

                  <h3 className="font-bold text-sm text-[#0f172a]">
                    <NavLink to={`/bugs/${bug.id}`} className="hover:text-[#047857] transition">
                      [{bug.id}] {bug.title}
                    </NavLink>
                  </h3>

                  <p className="text-xs text-[#64748b] line-clamp-1">{bug.description}</p>

                  <div className="text-[11px] text-[#64748b] flex flex-wrap items-center gap-3 pt-1">
                    <span>Target: <code className="text-[#334155]">{bug.affected_url}</code></span>
                    <span>&bull;</span>
                    <span>Replay cycles: <strong className="text-[#0f172a]">{bug.replay_attempts}</strong></span>
                    <span>&bull;</span>
                    <span>Confidence: <strong className="text-emerald-700">{(bug.confidence_score * 100).toFixed(0)}%</strong></span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <NavLink
                    to={`/bugs/${bug.id}`}
                    className="text-xs font-semibold text-[#047857] bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 px-3.5 py-2 rounded-lg flex items-center gap-1.5 transition"
                  >
                    <span>View Report</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </NavLink>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
