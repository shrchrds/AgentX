import React, { useState, useEffect } from 'react';
import api from '../api';
const AgentType = [
  'contract_review',
  'case_analysis',
  'risk_analysis',
];

const AgentRegistry = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [registering, setRegistering] = useState(false);

  const [newAgentType, setNewAgentType] = useState('contract_review');
  const [newAgentId, setNewAgentId] = useState('');

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await api.get('/agents');
      setAgents(response.data);
    } catch (err) {
      setError('Failed to load agents.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setRegistering(true);
    setError(null);

    try {
      await api.post('/agents', {
        agent_type: newAgentType,
        agent_id: newAgentId || undefined,
      });
      await fetchAgents();
      setNewAgentId('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to register agent.');
    } finally {
      setRegistering(false);
    }
  };

  if (loading) return <div className="text-center py-10">Loading Agents...</div>;
  if (error && agents.length === 0) return <div className="text-center py-10 text-red-500">{error}</div>;

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Agent Registry</h1>

      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 mb-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Register a New Agent</h2>
        <form onSubmit={handleRegister} className="flex flex-col sm:flex-row gap-4">
          <select
            value={newAgentType}
            onChange={(e) => setNewAgentType(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-slate-500 focus:border-slate-500"
          >
            {AgentType.map((type) => (
              <option key={type} value={type}>
                {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </option>
            ))}
          </select>
          <input
            type="text"
            value={newAgentId}
            onChange={(e) => setNewAgentId(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-slate-500 focus:border-slate-500"
            placeholder="Optional Agent ID"
          />
          <button
            type="submit"
            disabled={registering}
            className="bg-slate-800 text-white px-6 py-2 rounded-md hover:bg-slate-700 transition-colors font-medium disabled:opacity-50"
          >
            {registering ? 'Registering...' : 'Register'}
          </button>
        </form>
        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
            {error}
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h2 className="text-lg font-semibold text-gray-800">Registered Agents ({agents.length})</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {agents.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500 text-sm">No agents registered yet.</div>
          ) : (
            agents.map((agent) => (
              <div key={agent.agent_id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                <div>
                  <span className="font-medium text-gray-900">{agent.agent_id}</span>
                  <span className="text-sm text-gray-500 ml-3">
                    {agent.agent_type.replace(/_/g, ' ')}
                  </span>
                </div>
                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                  agent.agent_type === 'contract_review' ? 'bg-blue-100 text-blue-800' :
                  agent.agent_type === 'case_analysis' ? 'bg-purple-100 text-purple-800' :
                  'bg-green-100 text-green-800'
                }`}>
                  Active
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentRegistry;
