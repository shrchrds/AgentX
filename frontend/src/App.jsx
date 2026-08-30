import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import TaskManagement from './pages/TaskManagement';
import AgentRegistry from './pages/AgentRegistry';
import LogsViewer from './pages/LogsViewer';

const Layout = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <nav className="bg-slate-800 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="text-xl font-bold tracking-tight hover:text-slate-300 transition-colors">
                AgentX <span className="text-slate-400 font-normal">Legal Framework</span>
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-700 transition-colors">Dashboard</Link>
              <Link to="/tasks" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-700 transition-colors">Tasks</Link>
              <Link to="/agents" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-slate-700 transition-colors">Agents</Link>
            </div>
          </div>
        </div>
      </nav>
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      <footer className="bg-white border-t py-4 text-center text-gray-500 text-xs">
        &copy; 2026 AgentX Multi-Agent System. All rights reserved.
      </footer>
    </div>
  );
};

const App = () => {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tasks" element={<TaskManagement />} />
          <Route path="/agents" element={<AgentRegistry />} />
          <Route path="/tasks/:taskId/logs" element={<LogsViewer />} />
        </Routes>
      </Layout>
    </Router>
  );
};

export default App;
