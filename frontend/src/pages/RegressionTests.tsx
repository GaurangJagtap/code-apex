import React, { useEffect, useState } from 'react';
import {
  History,
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
  Sparkles
} from 'lucide-react';
import {
  fetchRegressionTests,
  rerunRegressionTest,
  RegressionTest,
  RegressionRunResult
} from '../api/client';

export const RegressionTests: React.FC = () => {
  const [tests, setTests] = useState<RegressionTest[]>([]);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<RegressionRunResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRegressionTests()
      .then(setTests)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleRunTest = async (testId: string) => {
    setRunningId(testId);
    setLastResult(null);
    try {
      const res = await rerunRegressionTest(testId);
      setLastResult(res);
      // Refresh list
      const updated = await fetchRegressionTests();
      setTests(updated);
    } catch (e: any) {
      alert(e?.response?.data?.detail || e.message || 'Error executing regression test.');
    } finally {
      setRunningId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-[#e2e8f0] shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-[#0f172a] flex items-center gap-2">
            <History className="w-5 h-5 text-[#047857]" />
            Reusable Regression Test Suite
          </h2>
          <p className="text-xs text-[#64748b] mt-0.5">
            Successful exploratory user journeys saved as automated regression tests. Rerun to detect regressions in new builds.
          </p>
        </div>

        <div className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200">
          {tests.length} Saved Regression Journey(s)
        </div>
      </div>

      {/* Regression Run Result Diff Banner */}
      {lastResult && (
        <div
          className={`p-4 rounded-xl border flex items-start justify-between text-xs transition-all ${
            lastResult.status === 'Passed'
              ? 'bg-emerald-50 border-emerald-300 text-emerald-950'
              : 'bg-rose-50 border-rose-300 text-rose-950'
          }`}
        >
          <div className="space-y-1">
            <div className="font-bold text-sm flex items-center gap-2">
              {lastResult.status === 'Passed' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              ) : (
                <XCircle className="w-4 h-4 text-rose-600" />
              )}
              Regression Execution Outcome: {lastResult.status.toUpperCase()}
            </div>
            <div className="font-mono text-xs">{lastResult.diff_summary}</div>
            <div className="text-[11px] opacity-80">
              Duration: {lastResult.duration_sec.toFixed(2)}s &bull; Executed at: {lastResult.executed_at.substring(11, 19)}
            </div>
          </div>
          <button
            onClick={() => setLastResult(null)}
            className="text-xs underline opacity-70 hover:opacity-100"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Regression Tests List */}
      <div className="bg-white rounded-xl border border-[#e2e8f0] shadow-sm overflow-hidden">
        {tests.length === 0 ? (
          <div className="p-12 text-center text-sm text-[#94a3b8] space-y-2">
            <Sparkles className="w-8 h-8 text-slate-300 mx-auto mb-1" />
            <p>No regression tests saved yet.</p>
            <p className="text-xs text-[#64748b]">
              Execute a test run in the Test Runs console and click <strong>"Save as Regression Test"</strong> on any successful journey to populate your suite.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-[#e2e8f0]">
            {tests.map(test => {
              const isRunning = runningId === test.id;
              const isPassed = test.last_status === 'Passed';
              const isFailed = test.last_status === 'Failed';

              return (
                <div key={test.id} className="p-5 hover:bg-[#f8fafc] transition-colors flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold bg-[#f1f5f9] px-2 py-0.5 rounded text-[#0f172a]">
                        {test.id}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          isPassed
                            ? 'bg-emerald-100 text-emerald-800'
                            : isFailed
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {test.last_status}
                      </span>
                      <span className="text-xs text-[#64748b]">Executions: <strong>{test.executions_count}</strong></span>
                    </div>

                    <h3 className="font-bold text-sm text-[#0f172a]">{test.name}</h3>
                    <div className="text-xs text-[#64748b] flex flex-wrap items-center gap-3">
                      <span>Target: <code className="text-[#334155]">{test.target_url}</code></span>
                      <span>&bull;</span>
                      <span>Steps: {test.steps_count}</span>
                      <span>&bull;</span>
                      <span>Assertions: {test.assertions_count}</span>
                      {test.last_run_at && (
                        <>
                          <span>&bull;</span>
                          <span>Last run: {test.last_run_at.substring(0, 10)}</span>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="shrink-0">
                    <button
                      onClick={() => handleRunTest(test.id)}
                      disabled={isRunning}
                      className="text-xs font-semibold bg-[#065f46] hover:bg-[#047857] text-white px-4 py-2 rounded-lg flex items-center gap-2 transition shadow-sm disabled:opacity-50"
                    >
                      <Play className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : ''}`} />
                      <span>{isRunning ? 'Re-executing Browser...' : 'Rerun Journey'}</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
