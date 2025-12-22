import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Edit, RefreshCw, Settings, ToggleLeft, ToggleRight, Key, Eye, EyeOff, Check, X } from 'lucide-react';
import { modelsApi, settingsApi } from '../services/api';
import type { ModelConfig } from '../types';

export default function Models() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingModel, setEditingModel] = useState<ModelConfig | null>(null);

  const { data: models, isLoading } = useQuery({
    queryKey: ['models'],
    queryFn: modelsApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: modelsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
  });

  const seedMutation = useMutation({
    mutationFn: modelsApi.seedDefaults,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ name, is_active }: { name: string; is_active: boolean }) =>
      modelsApi.update(name, { is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
  });

  const providerColors = {
    openai: 'bg-green-500/20 text-green-400',
    anthropic: 'bg-orange-500/20 text-orange-400',
    google: 'bg-blue-500/20 text-blue-400',
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Model Configuration</h1>
          <p className="text-slate-400">Configure LLM providers and parameters</p>
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
            Add Model
          </button>
        </div>
      </div>

      <APIKeysConfig />

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      ) : !models || models.length === 0 ? (
        <div className="bg-slate-800 rounded-xl p-12 text-center">
          <Settings className="w-12 h-12 mx-auto mb-4 text-slate-500" />
          <h3 className="text-lg font-medium mb-2">No models configured</h3>
          <p className="text-slate-400 mb-4">Add models or seed the defaults to get started</p>
          <button
            onClick={() => seedMutation.mutate()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            Seed Default Models
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {models.map((model) => (
            <div
              key={model.id}
              className={`bg-slate-800 rounded-xl p-6 ${!model.is_active ? 'opacity-60' : ''}`}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold">{model.display_name}</h3>
                  <span className={`inline-block px-2 py-1 rounded text-xs mt-1 ${providerColors[model.provider as keyof typeof providerColors] || 'bg-slate-600'}`}>
                    {model.provider}
                  </span>
                </div>
                <button
                  onClick={() => toggleMutation.mutate({ name: model.name, is_active: !model.is_active })}
                  className="p-1"
                  title={model.is_active ? 'Disable' : 'Enable'}
                >
                  {model.is_active ? (
                    <ToggleRight className="w-6 h-6 text-green-400" />
                  ) : (
                    <ToggleLeft className="w-6 h-6 text-slate-400" />
                  )}
                </button>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Model ID</span>
                  <span className="font-mono">{model.model_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Temperature</span>
                  <span>{model.temperature}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Max Tokens</span>
                  <span>{model.max_tokens}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Cost (Input/Output)</span>
                  <span>${model.cost_per_1k_input}/${model.cost_per_1k_output} per 1K</span>
                </div>
              </div>

              <div className="flex gap-2 mt-4 pt-4 border-t border-slate-700">
                <button
                  onClick={() => setEditingModel(model)}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                >
                  <Edit className="w-4 h-4" />
                  Edit
                </button>
                <button
                  onClick={() => deleteMutation.mutate(model.name)}
                  className="px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {(showCreateModal || editingModel) && (
        <ModelModal
          model={editingModel}
          onClose={() => {
            setShowCreateModal(false);
            setEditingModel(null);
          }}
        />
      )}
    </div>
  );
}

function APIKeysConfig() {
  const queryClient = useQueryClient();
  const [showKeys, setShowKeys] = useState<{ openai: boolean; anthropic: boolean; google: boolean }>({
    openai: false,
    anthropic: false,
    google: false,
  });
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [keyValue, setKeyValue] = useState('');

  const { data: keysStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['apiKeysStatus'],
    queryFn: settingsApi.getApiKeysStatus,
  });

  const { data: maskedKeys } = useQuery({
    queryKey: ['maskedApiKeys'],
    queryFn: settingsApi.getMaskedApiKeys,
  });

  const updateMutation = useMutation({
    mutationFn: settingsApi.updateApiKeys,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['apiKeysStatus'] });
      queryClient.invalidateQueries({ queryKey: ['maskedApiKeys'] });
      setEditingKey(null);
      setKeyValue('');
    },
  });

  const handleSaveKey = (provider: 'openai' | 'anthropic' | 'google') => {
    const data: { openai_api_key?: string; anthropic_api_key?: string; google_api_key?: string } = {};
    if (provider === 'openai') data.openai_api_key = keyValue;
    if (provider === 'anthropic') data.anthropic_api_key = keyValue;
    if (provider === 'google') data.google_api_key = keyValue;
    updateMutation.mutate(data);
  };

  const handleClearKey = (provider: 'openai' | 'anthropic' | 'google') => {
    const data: { openai_api_key?: string; anthropic_api_key?: string; google_api_key?: string } = {};
    if (provider === 'openai') data.openai_api_key = '';
    if (provider === 'anthropic') data.anthropic_api_key = '';
    if (provider === 'google') data.google_api_key = '';
    updateMutation.mutate(data);
  };

  const providers = [
    { key: 'openai' as const, name: 'OpenAI', dotClass: 'bg-green-500', badgeClass: 'bg-green-500/20 text-green-400' },
    { key: 'anthropic' as const, name: 'Anthropic', dotClass: 'bg-orange-500', badgeClass: 'bg-orange-500/20 text-orange-400' },
    { key: 'google' as const, name: 'Google', dotClass: 'bg-blue-500', badgeClass: 'bg-blue-500/20 text-blue-400' },
  ];

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <Key className="w-5 h-5 text-blue-400" />
        <h2 className="text-lg font-semibold">API Keys Configuration</h2>
      </div>
      <p className="text-slate-400 text-sm mb-6">
        Configure your API keys to enable real LLM benchmarking. Keys are stored in memory and will be cleared on server restart.
      </p>

      {statusLoading ? (
        <div className="flex items-center justify-center py-4">
          <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />
        </div>
      ) : (
        <div className="space-y-4">
          {providers.map(({ key, name, ...color }) => {
            const isConfigured = keysStatus?.[`${key}_configured` as keyof typeof keysStatus];
            const maskedValue = maskedKeys?.[key] || '';
            const isEditing = editingKey === key;

            return (
              <div key={key} className="bg-slate-900 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${isConfigured ? color.dotClass : 'bg-slate-500'}`} />
                    <span className="font-medium">{name}</span>
                    {isConfigured && (
                      <span className={`text-xs px-2 py-0.5 rounded ${color.badgeClass}`}>
                        Configured
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {!isEditing && (
                      <>
                        <button
                          onClick={() => setShowKeys(prev => ({ ...prev, [key]: !prev[key] }))}
                          className="p-1.5 hover:bg-slate-700 rounded transition-colors"
                          title={showKeys[key] ? 'Hide' : 'Show'}
                        >
                          {showKeys[key] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                        <button
                          onClick={() => {
                            setEditingKey(key);
                            setKeyValue('');
                          }}
                          className="px-3 py-1.5 text-sm bg-slate-700 hover:bg-slate-600 rounded transition-colors"
                        >
                          {isConfigured ? 'Update' : 'Add Key'}
                        </button>
                        {isConfigured && (
                          <button
                            onClick={() => handleClearKey(key)}
                            className="p-1.5 hover:bg-red-500/20 text-red-400 rounded transition-colors"
                            title="Clear key"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </>
                    )}
                  </div>
                </div>

                {isEditing ? (
                  <div className="flex gap-2 mt-3">
                    <input
                      type="password"
                      value={keyValue}
                      onChange={(e) => setKeyValue(e.target.value)}
                      placeholder={`Enter ${name} API key`}
                      className="flex-1 px-3 py-2 bg-slate-800 rounded border border-slate-600 focus:border-blue-500 focus:outline-none text-sm font-mono"
                      autoFocus
                    />
                    <button
                      onClick={() => handleSaveKey(key)}
                      disabled={!keyValue || updateMutation.isPending}
                      className="px-3 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 rounded transition-colors"
                      title="Save"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => {
                        setEditingKey(null);
                        setKeyValue('');
                      }}
                      className="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded transition-colors"
                      title="Cancel"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  isConfigured && showKeys[key] && (
                    <div className="mt-2 px-3 py-2 bg-slate-800 rounded font-mono text-sm text-slate-400">
                      {maskedValue}
                    </div>
                  )
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function ModelModal({ model, onClose }: { model: ModelConfig | null; onClose: () => void }) {
  const queryClient = useQueryClient();
  const isEditing = !!model;

  const [name, setName] = useState(model?.name || '');
  const [provider, setProvider] = useState(model?.provider || 'openai');
  const [modelId, setModelId] = useState(model?.model_id || '');
  const [displayName, setDisplayName] = useState(model?.display_name || '');
  const [temperature, setTemperature] = useState(model?.temperature || 0);
  const [maxTokens, setMaxTokens] = useState(model?.max_tokens || 4096);
  const [costInput, setCostInput] = useState(model?.cost_per_1k_input || 0);
  const [costOutput, setCostOutput] = useState(model?.cost_per_1k_output || 0);

  const createMutation = useMutation({
    mutationFn: modelsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
      onClose();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ name, data }: { name: string; data: Partial<ModelConfig> }) =>
      modelsApi.update(name, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = {
      name,
      provider,
      model_id: modelId,
      display_name: displayName,
      temperature,
      max_tokens: maxTokens,
      cost_per_1k_input: costInput,
      cost_per_1k_output: costOutput,
    };

    if (isEditing) {
      updateMutation.mutate({ name: model.name, data });
    } else {
      createMutation.mutate(data);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-xl p-6 w-full max-w-lg">
        <h2 className="text-xl font-bold mb-4">
          {isEditing ? 'Edit Model' : 'Add Model'}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name (unique ID)</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={isEditing}
                className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none disabled:opacity-50"
                placeholder="gpt-4o"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Display Name</label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                placeholder="GPT-4o"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Provider</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
              >
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="google">Google</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Model ID</label>
              <input
                type="text"
                value={modelId}
                onChange={(e) => setModelId(e.target.value)}
                className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
                placeholder="gpt-4o"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Temperature</label>
              <input
                type="number"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                step="0.1"
                min="0"
                max="2"
                className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Max Tokens</label>
              <input
                type="number"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Cost per 1K Input Tokens ($)</label>
              <input
                type="number"
                value={costInput}
                onChange={(e) => setCostInput(parseFloat(e.target.value))}
                step="0.0001"
                min="0"
                className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Cost per 1K Output Tokens ($)</label>
              <input
                type="number"
                value={costOutput}
                onChange={(e) => setCostOutput(parseFloat(e.target.value))}
                step="0.0001"
                min="0"
                className="w-full px-4 py-2 bg-slate-700 rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
              />
            </div>
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
