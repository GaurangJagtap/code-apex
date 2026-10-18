import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PlayCircle,
  RotateCcw,
  Shield,
  Sliders,
  CheckSquare,
  AlertCircle,
  Cpu,
  Layers,
  Sparkles
} from 'lucide-react';
import { createRun } from '../api/client';

interface DemoTargetPreset {
  id: string;
  name: string;
  badge: string;
  url: string;
  description: string;
  objectives: string[];
}

const DEMO_PRESETS: DemoTargetPreset[] = [
  {
    id: 'devstore',
    name: 'Controlled DevStore',
    badge: '5 Seeded Defects',
    url: 'http://127.0.0.1:5001',
    description: 'Users should be able to register accounts, log in with valid credentials, browse product catalog items, add hardware products to their cart, increment quantities with accurate mathematical total calculations, fill checkout shipping details, and access protected customer account dashboards. Cart arithmetic and form validations must be strictly enforced.',
    objectives: ['Functional testing', 'Form validation', 'Business-rule testing', 'Negative testing']
  },
  {
    id: 'saucedemo',
    name: 'SauceDemo E-Commerce',
    badge: 'Industry Benchmark',
    url: 'https://www.saucedemo.com',
    description: 'Standard e-commerce QA benchmark. Users should be able to view login form, authenticate with standard credentials (standard_user / secret_sauce), browse catalog products, sort inventory, add items to cart, view cart subtotal, fill checkout credentials, and complete purchase workflows without UI exceptions.',
    objectives: ['Functional testing', 'Form validation', 'Navigation testing']
  },
  {
    id: 'the-internet',
    name: 'The Internet QA Playground',
    badge: 'Heroku Sandbox',
    url: 'https://the-internet.herokuapp.com',
    description: 'Autonomous exploration of UI testing sandbox. Verify navigation links, dynamic controls, authentication prompts, checkboxes, dropdown menus, and ensure error codes and status transitions resolve gracefully.',
    objectives: ['Functional testing', 'Navigation testing', 'Negative testing']
  },
  {
    id: 'example',
    name: 'Example Domain',
    badge: 'Clean Web',
    url: 'https://example.com',
    description: 'Verify standard web document accessibility, primary heading tags, informative documentation links, and responsive layout hydration without script errors.',
    objectives: ['Functional testing', 'Navigation testing']
  }
];

export const NewRun: React.FC = () => {
  const navigate = useNavigate();

  const [targetUrl, setTargetUrl] = useState('http://127.0.0.1:5001');
  const [activePreset, setActivePreset] = useState<string>('devstore');
  const [description, setDescription] = useState(DEMO_PRESETS[0].description);

  const availableObjectives = [
    'Functional testing',
    'Form validation',
    'Navigation testing',
    'Business-rule testing',
    'Negative testing',
    'Boundary testing',
    'Regression testing',
  ];
  const [selectedObjectives, setSelectedObjectives] = useState<string[]>([
    'Functional testing',
    'Form validation',
    'Business-rule testing',
    'Negative testing'
  ]);

  const [maxPages, setMaxPages] = useState(10);
  const [maxActions, setMaxActions] = useState(30);
  const [maxDurationSec, setMaxDurationSec] = useState(300);
  const [maxRetries, setMaxRetries] = useState(2);
  const [mode, setMode] = useState<'demo' | 'ai'>('demo');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleObjective = (obj: string) => {
    setSelectedObjectives(prev =>
      prev.includes(obj) ? prev.filter(o => o !== obj) : [...prev, obj]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate URL scheme
    if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
      setError('Target application URL must begin with http:// or https://');
      return;
    }

    if (!description.trim()) {
      setError('Please provide a natural-language description of intended application behavior.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await createRun({
        target_url: targetUrl,
        description,
        objectives: selectedObjectives,
        boundaries: {
          max_pages: maxPages,
          max_actions: maxActions,
          max_duration_sec: maxDurationSec,
          max_retries: maxRetries
        },
        mode
      });

      // Navigate to exploration page for this run
      navigate(`/explore?run_id=${res.run_id}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to initialize test run.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSelectPreset = (preset: DemoTargetPreset) => {
    setActivePreset(preset.id);
    setTargetUrl(preset.url);
    setDescription(preset.description);
    setSelectedObjectives(preset.objectives);
  };

  const handleResetDemoApp = async () => {
    try {
      const res = await fetch('http://127.0.0.1:5001/api/reset', { method: 'POST' });
      if (res.ok) {
        alert('Sample DevStore application state reset successfully.');
      } else {
        alert('Sample DevStore is not reachable at 127.0.0.1:5001. Please ensure the sample app is running.');
      }
    } catch (e) {
      alert('Could not connect to sample app at http://127.0.0.1:5001.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-[#0f172a]">Launch Autonomous QA Test Run</h2>
        <p className="text-sm text-[#64748b] mt-1">
          Specify target URL and intended application behavior. Scout, Tester, and Verifier agents will autonomously explore, plan, execute, and verify defects.
        </p>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl flex items-start gap-3 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>{error}</div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Target Details Card */}
        <div className="bg-white p-6 rounded-xl border border-[#e2e8f0] shadow-sm space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-[#e2e8f0]">
            <h3 className="font-semibold text-sm text-[#0f172a] flex items-center gap-2">
              <Shield className="w-4 h-4 text-[#047857]" />
              Target Application & Intended Behavior
            </h3>
            {targetUrl.includes('5001') && (
              <button
                type="button"
                onClick={handleResetDemoApp}
                className="text-xs font-semibold text-[#047857] hover:underline"
              >
                Reset Sample App Data
              </button>
            )}
          </div>

          {/* Quick Target URL Presets */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-[#475569] uppercase tracking-wider">
              Quick Target Presets (Or paste any custom web URL below)
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
              {DEMO_PRESETS.map(preset => {
                const isSelected = activePreset === preset.id && targetUrl === preset.url;
                return (
                  <button
                    key={preset.id}
                    type="button"
                    onClick={() => handleSelectPreset(preset)}
                    className={`text-left p-3 rounded-lg border transition-all flex flex-col justify-between ${
                      isSelected
                        ? 'border-[#047857] bg-emerald-50/80 ring-1 ring-[#047857]'
                        : 'border-[#cbd5e1] hover:border-[#94a3b8] bg-[#f8fafc]'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-[#0f172a]">{preset.name}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${
                          isSelected ? 'bg-emerald-200 text-emerald-900' : 'bg-slate-200 text-slate-700'
                        }`}>
                          {preset.badge}
                        </span>
                      </div>
                      <div className="text-[11px] font-mono text-[#64748b] truncate">{preset.url}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label htmlFor="target-url" className="block text-xs font-semibold text-[#475569] uppercase tracking-wider mb-1.5">
              Target Application Base URL *
            </label>
            <input
              id="target-url"
              type="url"
              required
              value={targetUrl}
              onChange={e => {
                setTargetUrl(e.target.value);
                setActivePreset('custom');
              }}
              className="w-full px-3.5 py-2 text-sm border border-[#cbd5e1] rounded-lg focus:outline-none focus:border-[#047857] focus:ring-1 focus:ring-[#047857] font-mono"
              placeholder="https://example.com or http://localhost:3000"
            />
            <div className="text-[11px] text-[#047857] mt-1 font-medium flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-[#047857]" />
              <span>Universal Target Engine: Autonomous exploration works on any valid HTTP/HTTPS URL, dev port, or web application.</span>
            </div>
          </div>

          <div>
            <label htmlFor="app-description" className="block text-xs font-semibold text-[#475569] uppercase tracking-wider mb-1.5">
              Application Description & Intended Business Rules *
            </label>
            <textarea
              id="app-description"
              required
              rows={4}
              value={description}
              onChange={e => setDescription(e.target.value)}
              className="w-full px-3.5 py-2 text-sm border border-[#cbd5e1] rounded-lg focus:outline-none focus:border-[#047857] focus:ring-1 focus:ring-[#047857] font-sans"
              placeholder="Describe requirements, expected form behavior, cart calculations, authentication rules..."
            />
            <div className="text-[11px] text-[#64748b] mt-1">
              The AI Planner and Assertion Engine use this specification to establish expectations and generate test oracles.
            </div>
          </div>
        </div>

        {/* Objectives & Mode */}
        <div className="bg-white p-6 rounded-xl border border-[#e2e8f0] shadow-sm space-y-4">
          <h3 className="font-semibold text-sm text-[#0f172a] flex items-center gap-2 pb-3 border-b border-[#e2e8f0]">
            <Layers className="w-4 h-4 text-[#047857]" />
            Testing Objectives & Agent Mode
          </h3>

          <div>
            <div className="text-xs font-semibold text-[#475569] uppercase tracking-wider mb-2">
              Select Testing Objectives
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
              {availableObjectives.map(obj => {
                const checked = selectedObjectives.includes(obj);
                return (
                  <button
                    key={obj}
                    type="button"
                    onClick={() => toggleObjective(obj)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium text-left transition ${
                      checked
                        ? 'bg-[#ecfdf5] border-[#047857] text-[#065f46]'
                        : 'bg-white border-[#e2e8f0] text-[#64748b] hover:border-[#cbd5e1]'
                    }`}
                  >
                    <CheckSquare className={`w-3.5 h-3.5 ${checked ? 'text-[#047857]' : 'text-[#cbd5e1]'}`} />
                    <span>{obj}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="pt-2">
            <div className="text-xs font-semibold text-[#475569] uppercase tracking-wider mb-2">
              Execution Mode
            </div>
            <div className="grid grid-cols-2 gap-3">
              <label
                className={`p-3.5 border rounded-lg cursor-pointer flex items-start gap-3 transition ${
                  mode === 'demo'
                    ? 'bg-[#ecfdf5] border-[#047857]'
                    : 'bg-white border-[#e2e8f0] hover:border-[#cbd5e1]'
                }`}
              >
                <input
                  type="radio"
                  name="engine_mode"
                  value="demo"
                  checked={mode === 'demo'}
                  onChange={() => setMode('demo')}
                  className="mt-1"
                />
                <div>
                  <div className="font-semibold text-sm text-[#0f172a] flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-[#047857]" />
                    Deterministic Demo Mode
                  </div>
                  <p className="text-xs text-[#64748b] mt-0.5">
                    Real Playwright browser automation with deterministic scenarios calibrated for the controlled sample app. Works without external API keys.
                  </p>
                </div>
              </label>

              <label
                className={`p-3.5 border rounded-lg cursor-pointer flex items-start gap-3 transition ${
                  mode === 'ai'
                    ? 'bg-[#ecfdf5] border-[#047857]'
                    : 'bg-white border-[#e2e8f0] hover:border-[#cbd5e1]'
                }`}
              >
                <input
                  type="radio"
                  name="engine_mode"
                  value="ai"
                  checked={mode === 'ai'}
                  onChange={() => setMode('ai')}
                  className="mt-1"
                />
                <div>
                  <div className="font-semibold text-sm text-[#0f172a] flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                    Real AI Mode (LLM Powered)
                  </div>
                  <p className="text-xs text-[#64748b] mt-0.5">
                    Uses configured LLM provider to reason about DOM state and synthesize structured test candidates with Pydantic validation.
                  </p>
                </div>
              </label>
            </div>
          </div>
        </div>

        {/* Safety Boundaries */}
        <div className="bg-white p-6 rounded-xl border border-[#e2e8f0] shadow-sm space-y-4">
          <h3 className="font-semibold text-sm text-[#0f172a] flex items-center gap-2 pb-3 border-b border-[#e2e8f0]">
            <Sliders className="w-4 h-4 text-[#047857]" />
            Autonomous Execution Boundaries
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <label htmlFor="max-pages-input" className="block text-xs font-semibold text-[#64748b] mb-1">Max Pages to Explore</label>
              <input
                id="max-pages-input"
                type="number"
                min={1}
                max={25}
                value={maxPages}
                onChange={e => setMaxPages(parseInt(e.target.value) || 10)}
                className="w-full px-3 py-1.5 border border-[#cbd5e1] rounded-lg text-sm"
              />
            </div>
            <div>
              <label htmlFor="max-actions-input" className="block text-xs font-semibold text-[#64748b] mb-1">Max Actions / Run</label>
              <input
                id="max-actions-input"
                type="number"
                min={5}
                max={100}
                value={maxActions}
                onChange={e => setMaxActions(parseInt(e.target.value) || 30)}
                className="w-full px-3 py-1.5 border border-[#cbd5e1] rounded-lg text-sm"
              />
            </div>
            <div>
              <label htmlFor="max-duration-input" className="block text-xs font-semibold text-[#64748b] mb-1">Max Timeout (sec)</label>
              <input
                id="max-duration-input"
                type="number"
                min={30}
                max={600}
                value={maxDurationSec}
                onChange={e => setMaxDurationSec(parseInt(e.target.value) || 300)}
                className="w-full px-3 py-1.5 border border-[#cbd5e1] rounded-lg text-sm"
              />
            </div>
            <div>
              <label htmlFor="max-retries-input" className="block text-xs font-semibold text-[#64748b] mb-1">Verification Replays</label>
              <input
                id="max-retries-input"
                type="number"
                min={1}
                max={3}
                value={maxRetries}
                onChange={e => setMaxRetries(parseInt(e.target.value) || 2)}
                className="w-full px-3 py-1.5 border border-[#cbd5e1] rounded-lg text-sm"
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={() => {
              setTargetUrl('http://127.0.0.1:5001');
              setSelectedObjectives(['Functional testing', 'Form validation', 'Business-rule testing']);
            }}
            className="px-4 py-2 border border-[#cbd5e1] text-[#475569] font-medium text-sm rounded-lg hover:bg-slate-50 transition"
          >
            Reset to Defaults
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="bg-[#065f46] hover:bg-[#047857] text-white font-semibold text-sm px-6 py-2 rounded-lg transition shadow-sm flex items-center gap-2 disabled:opacity-50"
          >
            <PlayCircle className="w-4 h-4" />
            <span>{submitting ? 'Initializing Session...' : 'Start Autonomous Test Run'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
