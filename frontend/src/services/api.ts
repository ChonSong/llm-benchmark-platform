import axios from 'axios';
import type { 
  ModelConfig, 
  TestCase, 
  Benchmark, 
  BenchmarkResult, 
  RadarChartData,
  ComparisonResponse 
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Models API
export const modelsApi = {
  list: async (): Promise<ModelConfig[]> => {
    const response = await api.get('/api/models/');
    return response.data;
  },
  create: async (data: Partial<ModelConfig>): Promise<ModelConfig> => {
    const response = await api.post('/api/models/', data);
    return response.data;
  },
  update: async (name: string, data: Partial<ModelConfig>): Promise<ModelConfig> => {
    const response = await api.patch(`/api/models/${name}`, data);
    return response.data;
  },
  delete: async (name: string): Promise<void> => {
    await api.delete(`/api/models/${name}`);
  },
  seedDefaults: async (): Promise<{ message: string }> => {
    const response = await api.post('/api/models/seed-defaults');
    return response.data;
  },
};

// Test Cases API
export const testCasesApi = {
  list: async (): Promise<TestCase[]> => {
    const response = await api.get('/api/test-cases/');
    return response.data;
  },
  get: async (name: string): Promise<TestCase> => {
    const response = await api.get(`/api/test-cases/${name}`);
    return response.data;
  },
  create: async (data: Partial<TestCase>): Promise<TestCase> => {
    const response = await api.post('/api/test-cases/', data);
    return response.data;
  },
  update: async (name: string, data: Partial<TestCase>): Promise<TestCase> => {
    const response = await api.patch(`/api/test-cases/${name}`, data);
    return response.data;
  },
  delete: async (name: string): Promise<void> => {
    await api.delete(`/api/test-cases/${name}`);
  },
  seedDefaults: async (): Promise<{ message: string }> => {
    const response = await api.post('/api/test-cases/seed-defaults');
    return response.data;
  },
};

// Benchmarks API
export const benchmarksApi = {
  list: async (): Promise<{ benchmarks: Benchmark[]; total: number }> => {
    const response = await api.get('/api/benchmarks/');
    return response.data;
  },
  get: async (id: number): Promise<Benchmark> => {
    const response = await api.get(`/api/benchmarks/${id}`);
    return response.data;
  },
  create: async (data: {
    name: string;
    description?: string;
    model_names: string[];
    test_case_names: string[];
    use_mock?: boolean;
  }): Promise<Benchmark> => {
    const response = await api.post('/api/benchmarks/', data);
    return response.data;
  },
  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/benchmarks/${id}`);
  },
};

// Results API
export const resultsApi = {
  getByBenchmark: async (benchmarkId: number): Promise<BenchmarkResult[]> => {
    const response = await api.get(`/api/results/benchmark/${benchmarkId}`);
    return response.data;
  },
  getComparison: async (benchmarkId: number): Promise<ComparisonResponse> => {
    const response = await api.get(`/api/results/benchmark/${benchmarkId}/comparison`);
    return response.data;
  },
  getRadarData: async (benchmarkId: number): Promise<RadarChartData[]> => {
    const response = await api.get(`/api/results/benchmark/${benchmarkId}/radar`);
    return response.data;
  },
  get: async (id: number): Promise<BenchmarkResult> => {
    const response = await api.get(`/api/results/${id}`);
    return response.data;
  },
  getCode: async (id: number): Promise<{ model_name: string; test_case_name: string; generated_code: string; lines_of_code: number }> => {
    const response = await api.get(`/api/results/${id}/code`);
    return response.data;
  },
};

// Settings API
export const settingsApi = {
  getApiKeysStatus: async (): Promise<{ openai_configured: boolean; anthropic_configured: boolean; google_configured: boolean }> => {
    const response = await api.get('/api/settings/api-keys');
    return response.data;
  },
  getMaskedApiKeys: async (): Promise<{ openai: string; anthropic: string; google: string }> => {
    const response = await api.get('/api/settings/api-keys/masked');
    return response.data;
  },
  updateApiKeys: async (data: { openai_api_key?: string; anthropic_api_key?: string; google_api_key?: string }): Promise<{ message: string; status: { openai_configured: boolean; anthropic_configured: boolean; google_configured: boolean } }> => {
    const response = await api.put('/api/settings/api-keys', data);
    return response.data;
  },
};

export default api;
