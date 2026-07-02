'use client';
import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { api } from '../lib/api';
import { RiskHistory, RiskHistoryPoint } from '../lib/types';

interface Props {
  customerId: string;
  currentScore: number;
}

export default function RiskSparkline({ customerId, currentScore }: Props) {
  const [history, setHistory] = useState<RiskHistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!customerId) return;
    api.getRiskHistory(customerId)
      .then((data) => {
        const h = (data as any)?.history || [];
        setHistory(h);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [customerId]);

  if (loading) {
    return (
      <div className="h-16 flex items-center justify-center">
        <span className="text-soc-textSecondary text-xs font-mono animate-pulse">
          Loading history...
        </span>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="h-16 flex items-center justify-center">
        <span className="text-soc-textSecondary text-xs font-mono">No history available</span>
      </div>
    );
  }

  // Color the line based on trend — is risk going up or down?
  const first = history[0]?.risk_score ?? 0;
  const last = history[history.length - 1]?.risk_score ?? 0;
  const lineColor = last > first ? '#FF3B5C' : '#00E5A0';

  return (
    <div className="bg-soc-surface border border-soc-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-soc-textPrimary text-sm font-bold">Trust Score History</h4>
          <p className="text-soc-textSecondary text-xs mt-0.5">
            Last {history.length} events · {last > first ? '↑ Risk increasing' : '↓ Risk decreasing'}
          </p>
        </div>
        <div className="text-right">
          <div className={`font-mono font-bold text-xl
            ${currentScore < 31 ? 'text-soc-green' :
              currentScore < 66 ? 'text-soc-amber' : 'text-soc-red'}`}>
            {currentScore.toFixed(0)}
          </div>
          <div className="text-soc-textSecondary text-xs font-mono">current</div>
        </div>
      </div>

      {/* Sparkline — no axes, just the line */}
      <ResponsiveContainer width="100%" height={60}>
        <LineChart data={history}>
          <XAxis dataKey="timestamp" hide />
          <Line
            type="monotone"
            dataKey="risk_score"
            stroke={lineColor}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 3, fill: lineColor }}
          />
          <Tooltip
            contentStyle={{
              background: '#0F1629',
              border: '1px solid #1E2D4A',
              borderRadius: '6px',
              fontSize: '10px',
              fontFamily: 'JetBrains Mono, monospace',
              color: '#E8F0FE'
            }}
            formatter={(value: any) => [`${Number(value).toFixed(1)}/100`, 'Risk Score']}
            labelFormatter={(label: any) => {
              try {
                return new Date(label).toLocaleString("en-IN");
              } catch {
                return String(label);
              }
            }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Min/Max labels */}
      <div className="flex justify-between mt-1">
        <span className="text-soc-textSecondary text-[10px] font-mono">
          Min: {Math.min(...history.map(h => h.risk_score)).toFixed(0)}
        </span>
        <span className="text-soc-textSecondary text-[10px] font-mono">
          Max: {Math.max(...history.map(h => h.risk_score)).toFixed(0)}
        </span>
      </div>
    </div>
  );
}
