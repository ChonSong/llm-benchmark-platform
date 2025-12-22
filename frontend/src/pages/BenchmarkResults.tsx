import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, RefreshCw, Code, BarChart3, Target } from 'lucide-react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { benchmarksApi, resultsApi } from '../services/api';
import type { BenchmarkResult } from '../types';

export default function BenchmarkResults() {
  const { id } = useParams<{ id: string }>();
  const benchmarkId = parseInt(id || '0');
  const [selectedResult, setSelectedResult] = useState<BenchmarkResult | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'details' | 'code'>('overview');

  const { data: benchmark, isLoading: benchmarkLoading } = useQuery({
    queryKey: ['benchmark', benchmarkId],
    queryFn: () => benchmarksApi.get(benchmarkId),
    enabled: !!benchmarkId,
  });

  const { data: comparison, isLoading: comparisonLoading } = useQuery({
    queryKey: ['comparison', benchmarkId],
    queryFn: () => resultsApi.getComparison(benchmarkId),
    enabled: !!benchmarkId,
    refetchInterval: benchmark?.status === 'running' ? 3000 : false,
  });

  const { data: radarData } = useQuery({
    queryKey: ['radar', benchmarkId],
    queryFn: () => resultsApi.getRadarData(benchmarkId),
    enabled: !!benchmarkId && benchmark?.status === 'completed',
  });

  if (benchmarkLoading || comparisonLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!benchmark || !comparison) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Benchmark not found or no results yet</p>
        <Link to="/benchmarks" className="text-blue-400 hover:underline mt-2 inline-block">
          Back to Benchmarks
        </Link>
      </div>
    );
  }

  const results = comparison.results;
  const summary = comparison.summary;

  // Prepare data for charts
  const scoreComparisonData = Object.entries(summary.by_model).map(([model, data]) => ({
    model,
    score: Math.round(data.avg_score),
    cost: data.total_cost.toFixed(3),
    latency: Math.round(data.avg_latency_ms / 1000),
    loc: Math.round(data.avg_loc),
  }));

  // Transform radar data for recharts format
  const radarMetrics = ['Completeness', 'Defensiveness', 'Precision', 'Security', 'Architecture'];
  const transformedRadarData = radarMetrics.map((metric) => {
    const dataPoint: Record<string, string | number> = { metric };
    radarData?.forEach((model) => {
      dataPoint[model.model_name] = model[metric.toLowerCase() as keyof typeof model] as number;
    });
    return dataPoint;
  });

  const modelColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          to="/benchmarks"
          className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold">{benchmark.name}</h1>
          <p className="text-slate-400">
            {benchmark.description || 'Benchmark results and comparison'}
          </p>
        </div>
        <StatusBadge status={benchmark.status} />
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SummaryCard
          title="Best Overall"
          value={summary.best_overall}
          icon={Target}
          color="green"
        />
        <SummaryCard
          title="Most Cost Effective"
          value={summary.most_cost_effective}
          icon={BarChart3}
          color="blue"
        />
        <SummaryCard
          title="Fastest"
          value={summary.fastest}
          icon={RefreshCw}
          color="purple"
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-700">
        {(['overview', 'details', 'code'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium capitalize transition-colors ${
              activeTab === tab
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Score Comparison Bar Chart */}
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4">Score Comparison</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={scoreComparisonData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="model" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: 'none' }}
                />
                <Bar dataKey="score" fill="#3b82f6" name="Avg Score" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Radar Chart */}
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4">Qualitative Comparison</h3>
            {transformedRadarData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={transformedRadarData}>
                  <PolarGrid stroke="#334155" />
                  <PolarAngleAxis dataKey="metric" stroke="#94a3b8" />
                  <PolarRadiusAxis stroke="#94a3b8" />
                  {radarData?.map((model, index) => (
                    <Radar
                      key={model.model_name}
                      name={model.model_name}
                      dataKey={model.model_name}
                      stroke={modelColors[index % modelColors.length]}
                      fill={modelColors[index % modelColors.length]}
                      fillOpacity={0.3}
                    />
                  ))}
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-slate-400">
                Waiting for results...
              </div>
            )}
          </div>

          {/* Cost & Latency Comparison */}
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4">Cost Analysis</h3>
            <div className="space-y-4">
              {scoreComparisonData.map((item, index) => (
                <div key={item.model} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: modelColors[index % modelColors.length] }}
                    />
                    <span>{item.model}</span>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">${item.cost}</p>
                    <p className="text-sm text-slate-400">{item.latency}s latency</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Lines of Code Comparison */}
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4">Verbosity (Lines of Code)</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={scoreComparisonData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis type="number" stroke="#94a3b8" />
                <YAxis dataKey="model" type="category" stroke="#94a3b8" width={100} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: 'none' }}
                />
                <Bar dataKey="loc" fill="#10b981" name="Avg Lines" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {activeTab === 'details' && (
        <div className="bg-slate-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Model</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Test Case</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Score</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Adherence</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Security</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Cost</th>
                <th className="px-4 py-3 text-left text-sm font-medium">LoC</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {results.map((result) => (
                <tr key={result.id} className="hover:bg-slate-700/50">
                  <td className="px-4 py-3 font-medium">{result.model_name}</td>
                  <td className="px-4 py-3">{result.test_case_name}</td>
                  <td className="px-4 py-3">
                    <ScoreBadge score={result.overall_score} />
                  </td>
                  <td className="px-4 py-3">{result.adherence_score.toFixed(1)}</td>
                  <td className="px-4 py-3">{result.security_score.toFixed(1)}</td>
                  <td className="px-4 py-3">${result.total_cost.toFixed(4)}</td>
                  <td className="px-4 py-3">{result.lines_of_code}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => setSelectedResult(result)}
                      className="p-2 hover:bg-slate-600 rounded-lg transition-colors"
                      title="View Code"
                    >
                      <Code className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'code' && (
        <div className="space-y-4">
          <p className="text-slate-400">Select a result from the details tab to view the generated code</p>
          {selectedResult && (
            <CodeViewer result={selectedResult} onClose={() => setSelectedResult(null)} />
          )}
        </div>
      )}

      {/* Code Modal */}
      {selectedResult && activeTab !== 'code' && (
        <CodeViewer result={selectedResult} onClose={() => setSelectedResult(null)} />
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

function SummaryCard({ title, value, icon: Icon, color }: { title: string; value: string; icon: React.ElementType; color: string }) {
  const colorClasses = {
    green: 'bg-green-500/20 text-green-400',
    blue: 'bg-blue-500/20 text-blue-400',
    purple: 'bg-purple-500/20 text-purple-400',
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg ${colorClasses[color as keyof typeof colorClasses]}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <p className="text-sm text-slate-400">{title}</p>
          <p className="text-xl font-bold">{value}</p>
        </div>
      </div>
    </div>
  );
}

function ScoreBadge({ score }: { score: number }) {
  let colorClass = 'bg-red-500/20 text-red-400';
  if (score >= 80) colorClass = 'bg-green-500/20 text-green-400';
  else if (score >= 60) colorClass = 'bg-yellow-500/20 text-yellow-400';

  return (
    <span className={`px-2 py-1 rounded text-sm font-medium ${colorClass}`}>
      {score.toFixed(1)}
    </span>
  );
}

function CodeViewer({ result, onClose }: { result: BenchmarkResult; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-xl p-6 w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg font-semibold">{result.model_name}</h3>
            <p className="text-sm text-slate-400">{result.test_case_name}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
          >
            &times;
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
          <div className="bg-slate-700 rounded-lg p-3">
            <p className="text-slate-400">Score</p>
            <p className="text-xl font-bold">{result.overall_score.toFixed(1)}</p>
          </div>
          <div className="bg-slate-700 rounded-lg p-3">
            <p className="text-slate-400">Lines of Code</p>
            <p className="text-xl font-bold">{result.lines_of_code}</p>
          </div>
        </div>

        {result.issues_found.length > 0 && (
          <div className="mb-4">
            <p className="text-sm font-medium mb-2">Issues Found:</p>
            <ul className="text-sm text-red-400 space-y-1">
              {result.issues_found.map((issue, i) => (
                <li key={i}>- {issue}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex-1 overflow-auto bg-slate-900 rounded-lg p-4">
          <pre className="text-sm font-mono whitespace-pre-wrap">
            {result.generated_code || 'No code generated'}
          </pre>
        </div>
      </div>
    </div>
  );
}
