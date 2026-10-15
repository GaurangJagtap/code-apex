import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { NewRun } from './pages/NewRun';
import { Exploration } from './pages/Exploration';
import { TestRuns } from './pages/TestRuns';
import { BugReports } from './pages/BugReports';
import { BugDetail } from './pages/BugDetail';
import { RegressionTests } from './pages/RegressionTests';
import { Settings } from './pages/Settings';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="new-run" element={<NewRun />} />
          <Route path="explore" element={<Exploration />} />
          <Route path="runs" element={<TestRuns />} />
          <Route path="bugs" element={<BugReports />} />
          <Route path="bugs/:bugId" element={<BugDetail />} />
          <Route path="regression" element={<RegressionTests />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
