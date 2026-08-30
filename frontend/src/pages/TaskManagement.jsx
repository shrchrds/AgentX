import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import api from '../api';

const TaskManagement = () => {
  const [taskId, setTaskId] = useState('');
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await api.post('/tasks', {
        task_id: taskId,
        input: input,
      });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit task.');
    } finally {
      setLoading(false);
    }
  };

  const handleViewLogs = () => {
    if (result?.task_id) {
      navigate(`/tasks/${result.task_id}/logs`);
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Task Management</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Submit a New Legal Task</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Task ID</label>
              <input
                type="text"
                value={taskId}
                onChange={(e) => setTaskId(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-slate-500 focus:border-slate-500"
                placeholder="e.g., task-001"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Legal Problem</label>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                required
                rows="6"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-slate-500 focus:border-slate-500"
                placeholder="Describe the legal issue for analysis..."
              ></textarea>
            </div>
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                loading ? 'bg-slate-400 cursor-not-allowed' : 'bg-slate-800 hover:bg-slate-700'
              } transition-colors`}
            >
              {loading ? 'Submitting Task...' : 'Submit Task'}
            </button>
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                {error}
              </div>
            )}
          </form>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Task Result</h2>
          {!result && !loading && (
            <div className="text-gray-500 text-sm py-8 text-center italic">
              Submit a task to see the aggregated result here.
            </div>
          )}
          {loading && (
            <div className="text-slate-600 text-sm py-8 text-center">
              Agents are working on your task... This may take up to a few minutes.
            </div>
          )}
          {result && (
            <div className="space-y-4">
              <div className="flex items-center justify-between bg-gray-50 p-3 rounded-md">
                <div>
                  <span className="text-xs text-gray-500 block">Status</span>
                  <span className={`text-sm font-bold ${
                    result.status === 'completed' ? 'text-green-600' :
                    result.status === 'failed' ? 'text-red-600' : 'text-yellow-600'
                  } uppercase`}>
                    {result.status}
                  </span>
                </div>
                <button
                  onClick={handleViewLogs}
                  className="text-xs bg-white border border-gray-300 px-3 py-1 rounded-md hover:bg-gray-100 transition-colors"
                >
                  View Execution Logs
                </button>
              </div>
              <div className="border-t pt-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Aggregated Output</h3>
                <div className="prose prose-sm max-w-none text-gray-800 bg-gray-50 p-4 rounded-md overflow-auto max-h-96">
                  <ReactMarkdown>{result.result || "No result returned."}</ReactMarkdown>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TaskManagement;
