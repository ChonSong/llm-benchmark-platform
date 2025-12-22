import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Play, FileCode, Settings, TrendingUp } from 'lucide-react';
import { benchmarksApi, modelsApi, testCasesApi } from '../services/api';

export default function Dashboard() {
  const { data: benchmarksData } = useQuery({
    queryKey: ['benchmarks'],
    queryFn: benchmarksApi.list,
  });

  const { data: models } = useQuery({
    queryKey: ['models'],
    queryFn: modelsApi.list,
  });

  const { data: testCases } = useQuery({
    queryKey: ['testCases'],
    queryFn: testCasesApi.list,
  });

  const recentBenchmarks = benchmarksData?.benchmarks?.slice(0, 5) || [];
  const completedBenchmarks = recentBenchmarks.filter(b => b.status === 'completed');

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">LLM Benchmark Platform</h1>
        <p className="text-slate-400">
          Compare coding capabilities of LLMs across adherence, refactoring, and extension tasks
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          icon={Play}
          label="Total Benchmarks"
          value={benchmarksData?.total || 0}
          color="blue"
        />
        <StatCard
          icon={FileCode}
          label="Test Cases"
          value={testCases?.length || 0}
          color="green"
        />
        <StatCard
          icon={Settings}
          label="Models Configured"
          value={models?.length || 0}
          color="purple"
        />
        <StatCard
          icon={TrendingUp}
          label="Completed Runs"
          value={completedBenchmarks.length}
          color="orange"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Start</h2>
          <div className="space-y-4">
            <QuickAction
              to="/benchmarks"
              icon={Play}
              title="Run New Benchmark"
              description="Start a new comparison test across multiple models"
            />
            <QuickAction
              to="/test-cases"
              icon={FileCode}
              title="Manage Test Cases"
              description="Create or edit test prompts and evaluation rules"
            />
            <QuickAction
              to="/models"
              icon={Settings}
              title="Configure Models"
              description="Set up API keys and model parameters"
            />
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Benchmarks</h2>
          {recentBenchmarks.length === 0 ? (
            <p className="text-slate-400">No benchmarks yet. Run your first benchmark to get started!</p>
          ) : (
            <div className="space-y-3">
              {recentBenchmarks.map((benchmark) => (
                <Link
                  key={benchmark.id}
                  to={`/benchmarks/${benchmark.id}`}
                  className="block p-4 bg-slate-700 rounded-lg hover:bg-slate-600 transition-colors"
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="font-medium">{benchmark.name}</h3>
                      <p className="text-sm text-slate-400">
                        {new Date(benchmark.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <StatusBadge status={benchmark.status} />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <h2 className="text-xl font-semibold mb-4">Evaluation Dimensions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <DimensionCard
            title="Task A: Strict Adherence"
            description="Tests how literally models follow rigid specifications. Evaluates the Python Rate Limiter task with 10 strict rules."
            metrics={['Class naming', 'Method signatures', 'No defensive code', 'Minimal implementation']}
          />
          <DimensionCard
            title="Task B: Legacy Refactoring"
            description="Tests ability to refactor messy TypeScript code with security issues into clean, layered architecture."
            metrics={['SQL injection fixes', 'Service/Controller/Repository split', 'Zod validation', 'Backward compatibility']}
          />
          <DimensionCard
            title="Task C: System Extension"
            description="Tests understanding of existing patterns and ability to extend a notification system with new handlers."
            metrics={['Pattern recognition', 'Architecture adherence', 'Template management', 'Error handling']}
          />
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }: { icon: React.ElementType; label: string; value: number; color: string }) {
  const colorClasses = {
    blue: 'bg-blue-500/20 text-blue-400',
    green: 'bg-green-500/20 text-green-400',
    purple: 'bg-purple-500/20 text-purple-400',
    orange: 'bg-orange-500/20 text-orange-400',
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg ${colorClasses[color as keyof typeof colorClasses]}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-sm text-slate-400">{label}</p>
        </div>
      </div>
    </div>
  );
}

function QuickAction({ to, icon: Icon, title, description }: { to: string; icon: React.ElementType; title: string; description: string }) {
  return (
    <Link
      to={to}
      className="flex items-center gap-4 p-4 bg-slate-700 rounded-lg hover:bg-slate-600 transition-colors"
    >
      <div className="p-2 bg-blue-500/20 rounded-lg">
        <Icon className="w-5 h-5 text-blue-400" />
      </div>
      <div>
        <h3 className="font-medium">{title}</h3>
        <p className="text-sm text-slate-400">{description}</p>
      </div>
    </Link>
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

function DimensionCard({ title, description, metrics }: { title: string; description: string; metrics: string[] }) {
  return (
    <div className="p-4 bg-slate-700 rounded-lg">
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-sm text-slate-400 mb-3">{description}</p>
      <div className="flex flex-wrap gap-2">
        {metrics.map((metric) => (
          <span key={metric} className="px-2 py-1 bg-slate-600 rounded text-xs">
            {metric}
          </span>
        ))}
      </div>
    </div>
  );
}
