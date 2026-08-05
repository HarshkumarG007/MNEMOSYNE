import { useState, useEffect } from 'react';

type AgentEvent = {
  id: string;
  agent: string;
  action: string;
  status: 'running' | 'success' | 'error';
  confidence?: number;
};

export default function AgentMonitor() {
  const [events, setEvents] = useState<AgentEvent[]>([]);

  useEffect(() => {
    // Mock WebSocket stream
    const mockStream = setInterval(() => {
      const newEvent: AgentEvent = {
        id: Math.random().toString(),
        agent: ['IngestionAgent', 'ExtractionAgent', 'TemporalAgent', 'JudgeAgent'][Math.floor(Math.random() * 4)],
        action: ['Parsing file', 'Extracting NER', 'Computing timeline', 'Debating confidence'][Math.floor(Math.random() * 4)],
        status: ['running', 'success', 'success'][Math.floor(Math.random() * 3)] as any,
        confidence: Math.random() > 0.5 ? Math.floor(Math.random() * 100) : undefined
      };
      
      setEvents(prev => [newEvent, ...prev].slice(0, 10)); // Keep last 10
    }, 2000);

    return () => clearInterval(mockStream);
  }, []);

  return (
    <div className="p-8 max-w-4xl mx-auto h-full flex flex-col">
      <h2 className="text-2xl font-bold text-neon-blue mb-6">Live Agent Stream</h2>
      
      <div className="flex-1 bg-dark-panel rounded-lg border border-gray-800 p-4 overflow-y-auto space-y-4">
        {events.map(event => (
          <div key={event.id} className="flex items-center justify-between p-3 bg-dark-bg rounded border border-gray-700 shadow-sm animate-fade-in">
            <div className="flex items-center gap-4">
              <span className={`w-3 h-3 rounded-full ${
                event.status === 'running' ? 'bg-yellow-500 animate-pulse' : 
                event.status === 'success' ? 'bg-green-500' : 'bg-neon-red'
              }`} />
              <div>
                <p className="font-bold text-neon-blue">{event.agent}</p>
                <p className="text-sm text-gray-400">{event.action}</p>
              </div>
            </div>
            
            {event.confidence && (
              <div className="text-right">
                <p className="text-xs text-gray-500 mb-1">Confidence</p>
                <div className="w-24 bg-gray-800 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${event.confidence > 70 ? 'bg-green-500' : 'bg-neon-red'}`} 
                    style={{ width: `${event.confidence}%` }} 
                  />
                </div>
              </div>
            )}
          </div>
        ))}
        {events.length === 0 && (
          <div className="text-gray-500 text-center mt-10">Waiting for agent activity...</div>
        )}
      </div>
    </div>
  );
}
