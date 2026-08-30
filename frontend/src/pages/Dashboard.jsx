import React, { useState, useEffect } from 'react';
import api from '../api';

const Dashboard = () => {
  const [stats, setStats] = useState({ agents: 0, tasks: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const agentsRes = await api.get('/agents');
        setStats(prev => ({ ...prev, agents: agentsRes.data.length }));
      } catch (err) {
        setError('Failed to fetch dashboard stats');
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return <div className="text-center py-10">Loading Dashboard...</div>;
  if (error) return <div className="text-center py-10 text-red-500">{error}</div>;

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">System Overview</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="text-sm font-medium text-gray-500 uppercase tracking-wider">Registered Agents</div>
          <div className="text-3xl font-bold text-slate-800">{stats.agents}</div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="text-sm font-medium text-gray-500 uppercase tracking-wider">Active Tasks</div>
          <div className="text-3xl font-bold text-slate-800">—</div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="text-sm font-medium text-gray-500 uppercase tracking-wider">System Health</div>
          <div className="text-3xl font-bold text-green-500">Online</div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h2 className="text-lg font-semibold text-gray-800">Quick Start</h2>
        </div>
        <div className="p-6">
          <p className="text-gray-600 mb-4">
            Welcome to the AgentX multi-agent collaboration framework. Start by registering specialized
            legal agents or submitting a new legal task for analysis.
          </p>
          <div className="flex space-x-4">
            <a href="/tasks" className="bg-slate-800 text-white px-4 py-2 rounded-md hover:bg-slate-700 transition-colors text-sm font-medium">
              Submit New Task
            </a>
            <a href="/agents" className="bg-white text-slate-800 border border-slate-300 px-4 py-2 rounded-md hover:bg-gray-50 transition-colors text-sm font-medium">
              Manage Agents
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
