import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import GraphVisualization from './components/GraphVisualization';
import AgentMonitor from './components/AgentMonitor';
import Timeline from './components/Timeline';

const queryClient = new QueryClient();

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-dark-bg text-text-primary flex flex-col">
      <header className="bg-dark-panel p-4 border-b border-gray-800 flex justify-between items-center">
        <h1 className="text-xl font-bold text-neon-blue tracking-wider">MNEMOSYNE</h1>
        <nav className="flex gap-4">
          <Link to="/" className="hover:text-neon-blue transition-colors">Graph</Link>
          <Link to="/timeline" className="hover:text-neon-blue transition-colors">Timeline</Link>
          <Link to="/agents" className="hover:text-neon-blue transition-colors">Agents</Link>
        </nav>
      </header>
      <main className="flex-1 overflow-hidden relative">
        {children}
      </main>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<GraphVisualization />} />
            <Route path="/timeline" element={<Timeline />} />
            <Route path="/agents" element={<AgentMonitor />} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
