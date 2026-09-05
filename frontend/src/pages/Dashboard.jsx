import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';

const Dashboard = () => {
  const [stats, setStats] = useState({ agents: 0, totalTasks: 0, completedTasks: 0 });
  const [recentTasks, setRecentTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [agentsRes, tasksRes] = await Promise.all([
          api.get('/agents'),
          api.get('/tasks').catch(() => ({ data: [] })),
        ]);
        const tasks = tasksRes.data || [];
        const completed = tasks.filter(t => t.status === 'completed').length;

        setStats({
          agents: agentsRes.data?.length || 0,
          totalTasks: tasks.length,
          completedTasks: completed,
        });
        setRecentTasks(tasks.slice(0, 5));
      } catch {
        setError('Failed to fetch dashboard stats. Ensure the backend server is running.');
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center space-y-3">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800"></div>
          <p className="text-slate-600 font-medium">Connecting to AgentX Framework...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto my-12 bg-red-50 border border-red-200 p-6 rounded-xl text-center space-y-3">
        <h3 className="text-red-800 font-semibold text-lg">Connection Error</h3>
        <p className="text-red-600 text-sm">{error}</p>
        <p className="text-xs text-gray-500 font-mono">Backend expected at: http://localhost:8000</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">System Overview</h1>
        <p className="text-gray-600">Real-time status of legal multi-agent orchestrator and memory store.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Registered Agents</div>
          <div className="text-3xl font-bold text-slate-900 mt-2">{stats.agents}</div>
          <div className="text-xs text-blue-600 mt-1">Contract, Case & Risk</div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total Tasks Submitted</div>
          <div className="text-3xl font-bold text-slate-900 mt-2">{stats.totalTasks}</div>
          <div className="text-xs text-gray-500 mt-1">Processed by Orchestrator</div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Completed Tasks</div>
          <div className="text-3xl font-bold text-green-600 mt-2">{stats.completedTasks}</div>
          <div className="text-xs text-gray-500 mt-1">Successful resolutions</div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider">System Health</div>
          <div className="text-3xl font-bold text-emerald-500 mt-2 flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></span>
            Online
          </div>
          <div className="text-xs text-gray-500 mt-1">FastAPI + LangGraph active</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Quick Launch */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Quick Actions</h2>
            <p className="text-gray-600 text-sm mb-6">
              AgentX orchestrates autonomous specialized agents that collaborate to review contracts,
              identify risks, and cite precedents.
            </p>
          </div>
          <div className="space-y-3">
            <Link
              to="/tasks"
              className="block w-full text-center bg-slate-900 hover:bg-slate-800 text-white font-medium py-2.5 px-4 rounded-lg transition-colors text-sm shadow-sm"
            >
              Submit Legal Task
            </Link>
            <Link
              to="/agents"
              className="block w-full text-center bg-white hover:bg-gray-50 border border-gray-300 text-slate-800 font-medium py-2.5 px-4 rounded-lg transition-colors text-sm"
            >
              View & Register Agents
            </Link>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Recent Tasks</h2>
            <Link to="/tasks" className="text-xs font-medium text-blue-600 hover:underline">
              View all tasks →
            </Link>
          </div>
          <div className="divide-y divide-gray-200">
            {recentTasks.length === 0 ? (
              <div className="px-6 py-12 text-center text-gray-500 text-sm">
                No tasks executed yet. <Link to="/tasks" className="text-blue-600 underline">Submit your first task</Link>.
              </div>
            ) : (
              recentTasks.map((t) => (
                <div key={t.task_id} className="px-6 py-3.5 flex items-center justify-between hover:bg-gray-50 transition-colors">
                  <div className="flex items-center space-x-3">
                    <span className={`w-2 h-2 rounded-full ${
                      t.status === 'completed' ? 'bg-green-500' :
                      t.status === 'failed' ? 'bg-red-500' : 'bg-yellow-500'
                    }`} />
                    <span className="font-mono text-sm font-medium text-gray-800">{t.task_id}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-700 font-medium">
                      {t.status}
                    </span>
                    <Link
                      to={`/tasks/${t.task_id}/logs`}
                      className="text-xs text-blue-600 hover:underline font-medium"
                    >
                      Logs
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
