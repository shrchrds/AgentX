import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api';

const LogsViewer = () => {
  const { taskId } = useParams();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await api.get(`/logs/${taskId}`);
        setLogs(response.data.logs || []);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load logs.');
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, [taskId]);

  if (loading) return <div className="text-center py-10">Loading Logs...</div>;
  if (error) return <div className="text-center py-10 text-red-500">{error}</div>;

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Execution Logs</h1>
      <p className="text-gray-500 mb-8">Task ID: <span className="font-mono bg-gray-100 px-2 py-0.5 rounded text-sm">{taskId}</span></p>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h2 className="font-semibold text-gray-800">Event Timeline</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {logs.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500 text-sm">No execution logs found.</div>
          ) : (
            logs.map((log, index) => (
              <div key={index} className="px-6 py-4 flex gap-4 hover:bg-gray-50 transition-colors">
                <div className="flex flex-col items-center">
                  <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                  <div className="w-px h-full bg-gray-200 my-1"></div>
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-medium text-gray-900 capitalize">{(log.event || '').replace(/_/g, ' ')}</h3>
                    <span className="text-xs text-gray-400">{new Date(log.timestamp).toLocaleString()}</span>
                  </div>
                  <pre className="bg-gray-50 text-xs text-gray-600 p-2 rounded overflow-x-auto font-mono">
                    {JSON.stringify(log, null, 2)}
                  </pre>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default LogsViewer;
