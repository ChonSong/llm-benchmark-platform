import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Play, Trash2, Eye, RefreshCw } from 'lucide-react';
import { benchmarksApi, modelsApi, testCasesApi } from '../services/api';

export default function Benchmarks() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data: benchmarksData, isLoading } = useQuery({
    queryKey: ['benchmarks'],
    queryFn: benchmarksApi.list,
    refetchInterval: 5000,
  });

  const deleteMutation = useMutation({
    mutationFn: benchmarksApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['benchmarks'] });
    },
  });

  const benchmarks = benchmarksData?.benchmarks || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Benchmarks</h1>
          <p className="text-slate-400">Run and compare LLM performance across test cases</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          <Play className="w-4 h-4" />
          New Benchmark
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      ) : benchmarks.length === 0 ? (
        <div className="bg-slate-800 rounded-xl p-12 text-center">
          <Play className="w-12 h-12 mx-auto mb-4 text-slate-500" />
          <h3 className="text-lg font-medium mb-2">No benchmarks yet</h3>
          <p className="text-slate-400 mb-4">Run your first benchmark to compare model performance</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            Create Benchmark
          </button>
        </div>
      ) : (
        <div className="bg-slate-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-700">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-medium">Name</th>
                <th className="px-6 py-3 text-left text-sm font-medium">Status</th>
                <th className="px-6 py-3 text-left text-sm font-medium">Created</th>
                <th className="px-6 py-3 text-left text-sm font-medium">Completed</th>
                <th className="px-6 py-3 text-right text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {benchmarks.map((benchmark) => (
                <tr key={benchmark.id} className="hover:bg-slate-700/50">
                  <td className="px-6 py-4">
                    <div>
                      <p className="font-medium">{benchmark.name}</p>
                      {benchmark.description && (
                        <p className="text-sm text-slate-400">{benchmark.description}</p>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={benchmark.status} />
                  </td>
                  <td className="px-6 py-4 text-slate-400">
                    {new Date(benchmark.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-slate-400">
                    {benchmark.completed_at
                      ? new Date(benchmark.completed_at).toLocaleString()
                      : '-'}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex justify-end gap-2">
                      <Link
                        to={`/benchmarks/${benchmark.id}`}
                        className="p-2 hover:bg-slate-600 rounded-lg transition-colors"
                        title="View Results"
                      >
                        <Eye className="w-4 h-4" />
                      </Link>
                      <button
                        onClick={() => deleteMutation.mutate(benchmark.id)}
                        className="p-2 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCreateModal && (
        <CreateBenchmarkModal onClose={() => setShowCreateModal(false)} />
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const statusClasses = {
    pending: 'bg-yellow-500/20 text-yellow-400',
    running: 'bg-blue-500/20 text-blue-400',
    completed: 'bg-green-500/20 text-green-400',
    failed: 'bg-red-500/20 text-red-400',
  };

  return (
    <span className={`px-3 py-1 rounded-full text-sm ${statusClasses[status as keyof typeof statusClasses] || statusClasses.pending}`}>
      {status}
    </span>
  );
}

function CreateBenchmarkModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [selectedTestCases, setSelectedTestCases] = useState<string[]>([]);
  const [useMock, setUseMock] = useState(true);

  const { data: models } = useQuery({
    queryKey: ['models'],
    queryFn: modelsApi.list,
  });

  const { data: testCases } = useQuery({
    queryKey: ['testCases'],
    queryFn: testCasesApi.list,
  });

  const createMutation = useMutation({
    mutationFn: benchmarksApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['benchmarks'] });
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      name,
      description,
      model_names: selectedModels,
      test_case_names: selectedTestCases,
      use_mock: useMock,
    });
  };

  const toggleModel = (modelName: string) => {
    setSelectedModels((prev) =>
      prev.includes(modelName)
        ? prev.filter((m) => m !== modelName)
        : [...prev, modelName]
    );
  };

  const toggleTestCase = (testCaseName: string) => {
    setSelectedTestCases((prev) =>
      prev.includes(testCaseName)
        ? prev.filter((t) => t !== testCaseName)
        : [...prev, testCaseName]
    );
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">Create New Benchmark</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
              placeholder="Benchmark name"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
              placeholder="Optional description"
              rows={2}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Select Models</label>
            <div className="grid grid-cols-2 gap-2">
              {models?.map((model) => (
                <label
                  key={model.name}
                  className={`flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedModels.includes(model.name)
                      ? 'bg-blue-600'
                      : 'bg-slate-700 hover:bg-slate-600'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedModels.includes(model.name)}
                    onChange={() => toggleModel(model.name)}
                    className="hidden"
                  />
                  <span>{model.display_name}</span>
                </label>
              ))}
            </div>
            {(!models || models.length === 0) && (
              <p className="text-slate-400 text-sm">No models configured. Go to Models page to add some.</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Select Test Cases</label>
            <div className="grid grid-cols-1 gap-2">
              {testCases?.map((testCase) => (
                <label
                  key={testCase.name}
                  className={`flex items-center gap-2 p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedTestCases.includes(testCase.name)
                      ? 'bg-blue-600'
                      : 'bg-slate-700 hover:bg-slate-600'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedTestCases.includes(testCase.name)}
                    onChange={() => toggleTestCase(testCase.name)}
                    className="hidden"
                  />
                  <div>
                    <span className="font-medium">{testCase.name}</span>
                    <span className="ml-2 text-xs px-2 py-0.5 bg-slate-600 rounded">
                      {testCase.task_type}
                    </span>
                  </div>
                </label>
              ))}
            </div>
            {(!testCases || testCases.length === 0) && (
              <p className="text-slate-400 text-sm">No test cases configured. Go to Test Cases page to add some.</p>
            )}
          </div>

          <div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={useMock}
                onChange={(e) => setUseMock(e.target.checked)}
                className="w-4 h-4 rounded"
              />
              <span>Use mock data (no API calls)</span>
            </label>
            <p className="text-sm text-slate-400 mt-1">
              Enable this to test the UI without making actual LLM API calls
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!name || selectedModels.length === 0 || selectedTestCases.length === 0 || createMutation.isPending}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Benchmark'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
