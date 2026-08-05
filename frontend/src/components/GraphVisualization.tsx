import { useEffect, useState } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';

const mockElements = [
  { data: { id: 'n1', label: 'John Doe', type: 'Person' } },
  { data: { id: 'n2', label: 'malware.exe', type: 'File' } },
  { data: { id: 'n3', label: 'Accessed', type: 'Event' } },
  { data: { source: 'n1', target: 'n3', label: 'triggered' } },
  { data: { source: 'n3', target: 'n2', label: 'target' } }
];

const stylesheet: any = [
  {
    selector: 'node',
    style: {
      'background-color': '#666',
      'label': 'data(label)',
      'color': '#fff',
      'font-size': '12px',
      'text-outline-color': '#111',
      'text-outline-width': '2px',
    }
  },
  {
    selector: 'node[type="Person"]',
    style: { 'background-color': '#00f3ff' }
  },
  {
    selector: 'node[type="Event"]',
    style: { 'background-color': '#ff003c' }
  },
  {
    selector: 'node[type="File"]',
    style: { 'background-color': '#888888' }
  },
  {
    selector: 'edge',
    style: {
      'width': 2,
      'line-color': '#444',
      'target-arrow-color': '#444',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'label': 'data(label)',
      'font-size': '10px',
      'color': '#aaa',
      'text-rotation': 'autorotate'
    }
  }
];

export default function GraphVisualization() {
  const [elements, setElements] = useState<any[]>([]);

  useEffect(() => {
    // Simulate fetching from /api/v1/graph
    setTimeout(() => {
      setElements(mockElements);
    }, 500);
  }, []);

  return (
    <div className="w-full h-full bg-dark-bg relative">
      {elements.length === 0 ? (
        <div className="absolute inset-0 flex items-center justify-center text-neon-blue animate-pulse">
          Loading Graph...
        </div>
      ) : (
        <CytoscapeComponent 
          elements={elements} 
          style={{ width: '100%', height: '100%' }}
          stylesheet={stylesheet}
          layout={{ name: 'cose' }} 
        />
      )}
    </div>
  );
}
