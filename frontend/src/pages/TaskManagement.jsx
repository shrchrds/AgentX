import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import api from '../api';

const TaskManagement = () => {
  const [taskId, setTaskId] = useState('');
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [recentTasks, setRecentTasks] = useState([]);

  // Document upload states
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [docInfo, setDocInfo] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const navigate = useNavigate();

  const fetchRecentTasks = async () => {
    try {
      const response = await api.get('/tasks');
      setRecentTasks(response.data || []);
    } catch {
      // Non-critical, ignore if fails
    }
  };

  useEffect(() => {
    fetchRecentTasks();
  }, []);

  const handleDocumentExtract = async (file) => {
    if (!file) return;

    const validExtensions = ['.pdf', '.docx', '.txt', '.md'];
    const fileName = file.name.toLowerCase();
    const isValid = validExtensions.some((ext) => fileName.endsWith(ext));

    if (!isValid) {
      setError(`Unsupported file format. Please upload ${validExtensions.join(', ')}`);
      return;
    }

    setUploadingDoc(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/tasks/extract-text', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const extracted = response.data;
      setInput(extracted.content);
      setDocInfo({
        name: extracted.filename,
        charCount: extracted.char_count,
        format: extracted.format.toUpperCase(),
        truncated: extracted.truncated,
        size: (file.size / 1024).toFixed(1) + ' KB',
      });

      // Suggest task_id if empty
      if (!taskId.trim()) {
        const cleanBase = extracted.filename
          .replace(/\.[^/.]+$/, '')
          .toLowerCase()
          .replace(/[^a-z0-9_-]/g, '-');
        setTaskId(`${cleanBase}-analysis`);
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Failed to extract text from document. Please check file format or password protection.'
      );
    } finally {
      setUploadingDoc(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      handleDocumentExtract(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      handleDocumentExtract(files[0]);
    }
  };

  const clearUploadedDocument = () => {
    setDocInfo(null);
    setInput('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        input_data: input,
        input: input,
      };
      if (taskId.trim()) {
        payload.task_id = taskId.trim();
      }
      if (docInfo) {
        payload.metadata = {
          source_file: docInfo.name,
          document_format: docInfo.format,
          extracted_chars: docInfo.charCount,
        };
      }

      const response = await api.post('/tasks', payload);
      setResult(response.data);
      fetchRecentTasks();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit task.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTask = (task) => {
    setResult(task);
  };

  const handleViewLogs = (id) => {
    const targetId = id || result?.task_id;
    if (targetId) {
      navigate(`/tasks/${targetId}/logs`);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Task Management</h1>
        <p className="text-gray-600">
          Submit legal issues, NDAs, or contracts for multi-agent review via text or document upload.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Task Submission Form */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Submit a New Legal Task</h2>

          {/* Document Upload Dropzone */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Upload Legal Document <span className="text-gray-400 font-normal">(PDF, Word DOCX, TXT, MD)</span>
            </label>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
                isDragOver
                  ? 'border-slate-800 bg-slate-50'
                  : 'border-gray-300 hover:border-slate-500 bg-gray-50/50'
              }`}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                accept=".pdf,.docx,.txt,.md"
                className="hidden"
              />
              <div className="flex flex-col items-center justify-center space-y-1.5">
                <svg
                  className="w-8 h-8 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="1.5"
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                <p className="text-sm font-medium text-gray-700">
                  {uploadingDoc ? (
                    <span className="text-slate-800 font-semibold animate-pulse">
                      Extracting document content...
                    </span>
                  ) : (
                    <span>
                      <strong className="text-slate-800 font-semibold">Click to browse</strong> or drag & drop file
                    </span>
                  )}
                </p>
                <p className="text-xs text-gray-400">PDF, Word (.docx), or Text/Markdown (up to 10 MB)</p>
              </div>
            </div>

            {/* Document badge if extracted */}
            {docInfo && (
              <div className="mt-3 flex items-center justify-between bg-slate-50 border border-slate-200 rounded-md px-3 py-2 text-xs">
                <div className="flex items-center space-x-2">
                  <span className="bg-slate-800 text-white font-semibold px-2 py-0.5 rounded text-[10px]">
                    {docInfo.format}
                  </span>
                  <span className="font-medium text-slate-800 truncate max-w-[200px]" title={docInfo.name}>
                    {docInfo.name}
                  </span>
                  <span className="text-gray-400">({docInfo.size}, {docInfo.charCount.toLocaleString()} chars)</span>
                  {docInfo.truncated && (
                    <span className="text-amber-600 bg-amber-50 border border-amber-200 px-1.5 py-0.2 rounded font-medium">
                      Truncated to 50k chars
                    </span>
                  )}
                </div>
                <button
                  type="button"
                  onClick={clearUploadedDocument}
                  className="text-gray-400 hover:text-red-600 transition-colors font-semibold ml-2"
                  title="Remove document and clear text"
                >
                  ✕ Clear
                </button>
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Task ID <span className="text-gray-400 font-normal">(Optional - auto-generated if blank)</span>
              </label>
              <input
                type="text"
                value={taskId}
                onChange={(e) => setTaskId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-slate-500 focus:border-slate-500"
                placeholder="e.g., nda-review-2026"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="block text-sm font-medium text-gray-700">
                  Legal Problem / Document Content
                </label>
                <span className="text-xs text-gray-400">
                  {input.length.toLocaleString()} / 50,000 chars
                </span>
              </div>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                required
                rows="7"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-1 focus:ring-slate-500 focus:border-slate-500 font-mono text-sm"
                placeholder="Paste contract terms, NDA clauses, or upload a document above..."
              ></textarea>
            </div>

            <button
              type="submit"
              disabled={loading || uploadingDoc}
              className={`w-full py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                loading || uploadingDoc ? 'bg-slate-400 cursor-not-allowed' : 'bg-slate-800 hover:bg-slate-700'
              } transition-colors`}
            >
              {loading ? 'Collaborating Agents at Work...' : 'Execute Multi-Agent Analysis'}
            </button>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                {error}
              </div>
            )}
          </form>
        </div>

        {/* Task Result Panel */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex flex-col">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Task Result</h2>
          {!result && !loading && (
            <div className="text-gray-500 text-sm py-16 text-center italic my-auto">
              Submit a task or select one from history below to see the multi-agent analysis.
            </div>
          )}
          {loading && (
            <div className="text-slate-600 text-sm py-16 text-center my-auto space-y-3">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-slate-800"></div>
              <p className="font-medium text-slate-700">Agents are analyzing your legal task...</p>
              <p className="text-xs text-gray-400">Classifying domain → Running specialized agents → Aggregating findings</p>
            </div>
          )}
          {result && (
            <div className="space-y-4">
              <div className="flex items-center justify-between bg-gray-50 p-3 rounded-md border border-gray-100">
                <div>
                  <span className="text-xs text-gray-500 block">Task ID</span>
                  <span className="font-mono text-xs text-gray-800 font-bold">{result.task_id}</span>
                </div>
                <div className="text-right">
                  <span className="text-xs text-gray-500 block">Status</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                    result.status === 'completed' ? 'bg-green-100 text-green-700' :
                    result.status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                  } uppercase`}>
                    {result.status}
                  </span>
                </div>
                <button
                  onClick={() => handleViewLogs(result.task_id)}
                  className="text-xs bg-white border border-gray-300 px-3 py-1.5 rounded-md hover:bg-gray-50 transition-colors font-medium text-slate-700"
                >
                  View Execution Logs →
                </button>
              </div>

              {result.errors && result.errors.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 text-amber-800 p-3 rounded-md text-xs">
                  <strong>Warnings/Errors:</strong>
                  <ul className="list-disc pl-4 mt-1">
                    {result.errors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="border-t pt-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Aggregated Multi-Agent Output</h3>
                <div className="prose prose-sm max-w-none text-gray-800 bg-gray-50 p-4 rounded-md overflow-auto max-h-[420px] border border-gray-100 font-sans leading-relaxed">
                  <ReactMarkdown>{result.output_data || result.result || "No output returned."}</ReactMarkdown>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recent Tasks List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">Task Execution History ({recentTasks.length})</h2>
          <button
            onClick={fetchRecentTasks}
            className="text-xs text-slate-600 hover:text-slate-900 border border-gray-200 bg-white px-2.5 py-1 rounded"
          >
            Refresh
          </button>
        </div>
        <div className="divide-y divide-gray-200">
          {recentTasks.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500 text-sm">No tasks submitted yet.</div>
          ) : (
            recentTasks.map((t) => (
              <div
                key={t.task_id}
                onClick={() => handleSelectTask(t)}
                className="px-6 py-3.5 flex items-center justify-between hover:bg-gray-50 transition-colors cursor-pointer"
              >
                <div className="flex items-center space-x-3">
                  <span className={`w-2 h-2 rounded-full ${
                    t.status === 'completed' ? 'bg-green-500' :
                    t.status === 'failed' ? 'bg-red-500' : 'bg-yellow-500'
                  }`} />
                  <span className="font-mono text-sm text-gray-900">{t.task_id}</span>
                  <span className="text-xs text-gray-400">
                    {t.created_at ? new Date(t.created_at).toLocaleString() : ''}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                    {t.status}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleViewLogs(t.task_id);
                    }}
                    className="text-xs text-blue-600 hover:underline px-2 py-1"
                  >
                    Logs
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default TaskManagement;
