import { useMemo } from 'react';
import { scaleTime } from '@visx/scale';
import { AxisBottom } from '@visx/axis';

const mockEvents = [
  { date: new Date('2023-01-01T10:00:00'), title: 'File created' },
  { date: new Date('2023-01-05T14:30:00'), title: 'File accessed' },
  { date: new Date('2023-01-10T09:15:00'), title: 'Data exfiltrated' },
];

export default function Timeline() {
  const width = 800;
  const height = 200;
  const margin = { top: 40, right: 40, bottom: 40, left: 40 };

  const xMax = width - margin.left - margin.right;
  const yMax = height - margin.top - margin.bottom;

  const xScale = useMemo(() => {
    return scaleTime({
      range: [0, xMax],
      domain: [
        new Date('2022-12-01'),
        new Date('2023-02-01')
      ]
    });
  }, [xMax]);

  return (
    <div className="w-full h-full flex flex-col items-center justify-center bg-dark-bg p-8">
      <h2 className="text-xl text-neon-blue mb-4">Event Timeline</h2>
      <svg width={width} height={height} className="bg-dark-panel rounded-lg shadow-lg">
        <g transform={`translate(${margin.left},${margin.top})`}>
          {/* Axis */}
          <AxisBottom
            top={yMax}
            scale={xScale}
            stroke="#444"
            tickStroke="#444"
            tickLabelProps={() => ({
              fill: '#aaa',
              fontSize: 10,
              textAnchor: 'middle',
            })}
          />
          
          {/* Events */}
          {mockEvents.map((d, i) => {
            const cx = xScale(d.date);
            return (
              <g key={`event-${i}`} transform={`translate(${cx}, ${yMax / 2})`}>
                <circle r={6} fill="#ff003c" />
                <text 
                  y={-15} 
                  fill="#e0e0e0" 
                  fontSize={12} 
                  textAnchor="middle"
                >
                  {d.title}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}
