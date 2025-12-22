export interface ModelConfig {
  id: number;
  name: string;
  provider: string;
  model_id: string;
  display_name: string;
  temperature: number;
  max_tokens: number;
  cost_per_1k_input: number;
  cost_per_1k_output: number;
  is_active: boolean;
  supports_code_mode: boolean;
  supports_ask_mode: boolean;
  extra_params: Record<string, unknown>;
}

export interface TestCase {
  id: number;
  name: string;
  task_type: string;
  description: string | null;
  prompt: string;
  input_code: string | null;
  rules: Array<{ id: number; description: string }>;
  golden_output: string | null;
  scoring_config: Record<string, unknown>;
  mode: string;
}

export interface Benchmark {
  id: number;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  completed_at: string | null;
}

export interface BenchmarkResult {
  id: number;
  benchmark_id: number;
  model_name: string;
  test_case_name: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  latency_ms: number | null;
  input_tokens: number;
  output_tokens: number;
  total_cost: number;
  generated_code: string | null;
  lines_of_code: number;
  overall_score: number;
  adherence_score: number;
  completeness_score: number;
  security_score: number;
  architecture_score: number;
  defensiveness_score: number;
  precision_score: number;
  verbosity_score: number;
  score_breakdown: Record<string, unknown>;
  issues_found: string[];
  error_message: string | null;
}

export interface RadarChartData {
  model_name: string;
  completeness: number;
  defensiveness: number;
  precision: number;
  security: number;
  architecture: number;
}

export interface ComparisonResponse {
  benchmark_id: number;
  results: BenchmarkResult[];
  summary: {
    by_model: Record<string, {
      avg_score: number;
      total_cost: number;
      avg_latency_ms: number;
      avg_loc: number;
    }>;
    best_overall: string;
    most_cost_effective: string;
    fastest: string;
  };
}
