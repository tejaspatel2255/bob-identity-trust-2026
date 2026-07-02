'use client';
import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { ScanResult } from '../lib/types';

export default function CorrelationPanel() {
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastScanned, setLastScanned] = useState<string | null>(null);

  const runScan = async () => {
    setLoading(true);
    try {
      const result = await api.scanAllCorrelations() as ScanResult;
      setScanResult(result);
      setLastScanned(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Correlation scan failed:', err);
    } finally {
      setLoading(false);
    }
  };

  // Auto-scan on mount
  useEffect(() => { runScan(); }, []);

  return (
    <div className="bg-soc-surface border border-soc-border rounded-xl p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-soc-textPrimary font-bold text-sm flex items-center gap-2">
            <span className="text-soc-cyan">⬡</span>
            Cross-Entity Correlation
          </h3>
          <p className="text-soc-textSecondary text-xs mt-0.5">
            Insider-assisted account takeover detection
          </p>
        </div>
        <button
          onClick={runScan}
          disabled={loading}
          className="text-xs font-mono px-3 py-1.5 rounded-lg border border-soc-cyan
                     text-soc-cyan hover:bg-soc-cyan/10 transition-colors duration-200
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Scanning...' : '↺ Rescan'}
        </button>
      </div>

      {/* Stats */}
      {scanResult && (
        <div className="mb-3 p-3 rounded-lg bg-soc-bg border border-soc-border">
          <div className="flex items-center justify-between">
            <span className="text-soc-textSecondary text-xs font-mono">Correlated Accounts</span>
            <span className={`font-mono font-bold text-lg
              ${scanResult.total_correlated_accounts > 0
                ? 'text-soc-red' : 'text-soc-green'}`}>
              {scanResult.total_correlated_accounts}
            </span>
          </div>
          {lastScanned && (
            <div className="text-soc-textSecondary text-[10px] font-mono mt-1">
              Last scanned: {lastScanned}
            </div>
          )}
        </div>
      )}

      {/* Alert list */}
      {scanResult && scanResult.total_correlated_accounts > 0 && (
        <div className="space-y-2 max-h-40 overflow-y-auto">
          {scanResult.alerts.map((alert, idx) => (
            <div key={idx}
                 className="p-3 rounded-lg border border-soc-red/40 bg-soc-red/5">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-soc-red text-xs font-bold font-mono">
                    ⚠ INSIDER-ASSISTED TAKEOVER
                  </div>
                  <div className="text-soc-textPrimary text-xs mt-1">
                    Account: <span className="font-mono text-soc-cyan">
                      {String(alert.account_id)}
                    </span>
                    <span className="ml-2 text-soc-textSecondary">
                      ({String(alert.balance_tier)} tier)
                    </span>
                  </div>
                  <div className="text-soc-textSecondary text-xs mt-0.5">
                    {String(alert.employee_name)} ({String(alert.employee_role)})
                    → recovery by {String(alert.customer_name)}
                  </div>
                </div>
                <div className="flex-shrink-0 text-right">
                  <div className="text-soc-amber font-mono text-xs font-bold">
                    {String(alert.minutes_apart)}m apart
                  </div>
                  <div className="text-soc-textSecondary text-[10px] font-mono mt-0.5">
                    CONFIDENCE: HIGH
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Clean state */}
      {scanResult && scanResult.total_correlated_accounts === 0 && (
        <div className="text-center py-4">
          <div className="text-soc-green text-sm font-mono">✓ No correlations detected</div>
          <div className="text-soc-textSecondary text-xs mt-1">
            All employee access patterns appear normal
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && !scanResult && (
        <div className="text-center py-4 text-soc-textSecondary text-sm font-mono animate-pulse">
          Scanning graph for correlations...
        </div>
      )}
    </div>
  );
}
