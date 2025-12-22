import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { BarChart3, Settings, FileCode, Play, Home } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Benchmarks from './pages/Benchmarks';
import BenchmarkResults from './pages/BenchmarkResults';
import TestCases from './pages/TestCases';
import Models from './pages/Models';

function App() {
  const location = useLocation();
  
  const navItems = [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/benchmarks', icon: Play, label: 'Benchmarks' },
    { path: '/test-cases', icon: FileCode, label: 'Test Cases' },
    { path: '/models', icon: Settings, label: 'Models' },
  ];

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <nav className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-8 h-8 text-blue-500" />
              <span className="text-xl font-bold">LLM Benchmark</span>
            </div>
            <div className="flex gap-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-600 text-white'
                        : 'text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/benchmarks" element={<Benchmarks />} />
          <Route path="/benchmarks/:id" element={<BenchmarkResults />} />
          <Route path="/test-cases" element={<TestCases />} />
          <Route path="/models" element={<Models />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
