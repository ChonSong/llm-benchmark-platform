import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Edit, RefreshCw, FileCode, Eye } from 'lucide-react';
import { testCasesApi } from '../services/api';
import type { TestCase } from '../types';

export default function TestCases() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTestCase, setEditingTestCase] = useState<TestCase | null>(null);
  const [viewingTestCase, setViewingTestCase] = useState<TestCase | null>(null);

  const { data: testCases, isLoading } = useQuery({
    queryKey: ['testCases'],
    queryFn: testCasesApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: testCasesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testCases'] });
    },
  });

  const seedMutation = useMutation({
    mutationFn: testCasesApi.seedDefaults,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testCases'] });
    },
  });

  const taskTypeColors = {
    adherence: 'bg-blue-500/20 text-blue-400',
    refactoring: 'bg-green-500/20 text-green-400',
    extension: 'bg-purple-500/20 text-purple-400',
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Test Cases</h1>
          <p className="text-slate-400">Manage evaluation prompts and scoring rules</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => seedMutation.mutate()}
            disabled={seedMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${seedMutation.isPending ? 'animate-spin' : ''}`} />
            Seed Defaults
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Test Case
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      ) : !testCases || testCases.length === 0 ? (
        <div className="bg-slate-800 rounded-xl p-12 text-center">
          <FileCode className="w-12 h-12 mx-auto mb-4 text-slate-500" />
          <h3 className="text-lg font-medium mb-2">No test cases yet</h3>
          <p className="text-slate-400 mb-4">Create test cases or seed the defaults to get started</p>
          <button
            onClick={() => seedMutation.mutate()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            Seed Default Test Cases
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {testCases.map((testCase) => (
            <div key={testCase.id} className="bg-slate-800 rounded-xl p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold">{testCase.name}</h3>
                    <span className={`px-2 py-1 rounded text-xs ${taskTypeColors[testCase.task_type as keyof typeof taskTypeColors] || 'bg-slate-600'}`}>
                      {testCase.task_type}
                    </span>
                    <span className="px-2 py-1 rounded text-xs bg-slate-600">
                      {testCase.mode} mode
                    </span>
                  </div>
                  <p className="text-slate-400 text-sm mb-3">
                    {testCase.description || 'No description'}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {testCase.rules?.slice(0, 5).map((rule, i) => (
                      <span key={i} className="px-2 py-1 bg-slate-700 rounded text-xs">
                        {typeof rule === 'object' ? rule.description : rule}
                      </span>
                    ))}
                    {testCase.rules && testCase.rules.length > 5 && (
                      <span className="px-2 py-1 bg-slate-700 rounded text-xs">
                        +{testCase.rules.length - 5} more
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setViewingTestCase(testCase)}
                    className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                    title="View"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setEditingTestCase(testCase)}
                    className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                    title="Edit"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(testCase.name)}
                    className="p-2 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {(showCreateModal || editingTestCase) && (
        <TestCaseModal
          testCase={editingTestCase}
          onClose={() => {
            setShowCreateModal(false);
            setEditingTestCase(null);
          }}
        />
      )}

      {viewingTestCase && (
        <TestCaseViewer
          testCase={viewingTestCase}
          onClose={() => setViewingTestCase(null)}
        />
      )}
    </div>
  );
}

function TestCaseModal({ testCase, onClose }: { testCase: TestCase | null; onClose: () => void }) {
  const queryClient = useQueryClient();
  const isEditing = !!testCase;

  const [name, setName] = useState(testCase?.name || '');
  const [taskType, setTaskType] = useState(testCase?.task_type || 'adherence');
  const [description, setDescription] = useState(testCase?.description || '');
  const [prompt, setPrompt] = useState(testCase?.prompt || '');
  const [inputCode, setInputCode] = useState(testCase?.input_code || '');
  const [mode, setMode] = useState(testCase?.mode || 'code');
  const [rulesText, setRulesText] = useState(
    testCase?.rules?.map((r) => (typeof r === 'object' ? r.description : r)).join('\n') || ''
  );

  const createMutation = useMutation({
    mutationFn: testCasesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testCases'] });
      onClose();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ name, data }: { name: string; data: Partial<TestCase> }) =>
      testCasesApi.update(name, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['testCases'] });
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const rules = rulesText
      .split('\n')
      .filter((r) => r.trim())
      .map((r, i) => ({ id: i + 1, description: r.trim() }));

    const data = {
      name,
      task_type: taskType,
      description,
      prompt,
      input_code: inputCode || null,
      mode,
      rules,
    };

    if (isEditing) {
      updateMutation.mutate({ name: testCase.name, data });
    } else {
      createMutation.mutate(data as Parameters<typeof testCasesApi.create>[0]);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-xl p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">
          {isEditing ? 'Edit Test Case' : 'Create Test Case'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={isEditing}
                className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none disabled:opacity-50"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Task Type</label>
              <select
                value={taskType}
                onChange={(e) => setTaskType(e.target.value)}
                className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
              >
                <option value="adherence">Adherence</option>
                <option value="refactoring">Refactoring</option>
                <option value="extension">Extension</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Mode</label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
              >
                <option value="code">Code (Generation)</option>
                <option value="ask">Ask (Analysis)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Prompt</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none font-mono text-sm"
              rows={8}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Input Code (for refactoring/extension)</label>
            <textarea
              value={inputCode}
              onChange={(e) => setInputCode(e.target.value)}
              className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none font-mono text-sm"
              rows={6}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Rules (one per line)</label>
            <textarea
              value={rulesText}
              onChange={(e) => setRulesText(e.target.value)}
              className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
              rows={4}
              placeholder="Enter each rule on a new line"
            />
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
              disabled={createMutation.isPending || updateMutation.isPending}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg transition-colors"
            >
              {createMutation.isPending || updateMutation.isPending ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function TestCaseViewer({ testCase, onClose }: { testCase: TestCase; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-xl p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">{testCase.name}</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
          >
            &times;
          </button>
        </div>

        <div className="space-y-4">
          <div className="flex gap-2">
            <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-sm">
              {testCase.task_type}
            </span>
            <span className="px-2 py-1 bg-slate-600 rounded text-sm">
              {testCase.mode} mode
            </span>
          </div>

          <div>
            <h3 className="font-medium mb-2">Prompt</h3>
            <pre className="bg-slate-900 rounded-lg p-4 text-sm overflow-x-auto whitespace-pre-wrap">
              {testCase.prompt}
            </pre>
          </div>

          {testCase.input_code && (
            <div>
              <h3 className="font-medium mb-2">Input Code</h3>
              <pre className="bg-slate-900 rounded-lg p-4 text-sm overflow-x-auto">
                {testCase.input_code}
              </pre>
            </div>
          )}

          {testCase.rules && testCase.rules.length > 0 && (
            <div>
              <h3 className="font-medium mb-2">Rules</h3>
              <ul className="space-y-1">
                {testCase.rules.map((rule, i) => (
                  <li key={i} className="text-sm text-slate-300">
                    {i + 1}. {typeof rule === 'object' ? rule.description : rule}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {testCase.golden_output && (
            <div>
              <h3 className="font-medium mb-2">Golden Output</h3>
              <pre className="bg-slate-900 rounded-lg p-4 text-sm overflow-x-auto">
                {testCase.golden_output}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
