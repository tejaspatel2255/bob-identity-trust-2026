"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { getHealth, getRiskEvents } from "../../lib/api";
import { RiskEvent, HealthResponse } from "../../lib/types";
import EventCard from "../../components/EventCard";
import RadarChart from "../../components/RadarChart";
import ShapBarChart from "../../components/ShapBarChart";
import LLMStatus from "../../components/LLMStatus";
import { 
  ShieldAlert, 
  Activity, 
  Database, 
  Cpu, 
  Clock, 
  ChevronRight,
  RefreshCw
} from "lucide-react";

export default function Dashboard() {
  const [events, setEvents] = useState<RiskEvent[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<RiskEvent | null>(null);
  const [toast, setToast] = useState<{ message: string; type: "error" | "info" } | null>(null);
  const [isPolling, setIsPolling] = useState(true);

  // Fetch data
  const fetchData = async () => {
    try {
      const fetchedEvents = await getRiskEvents();
      setEvents(fetchedEvents);

      // Default selection to first event if not set or if current selection is not in list
      if (fetchedEvents.length > 0) {
        setSelectedEvent((prev) => {
          if (!prev) return fetchedEvents[0];
          const exists = fetchedEvents.find((e) => e.id === prev.id);
          return exists || fetchedEvents[0];
        });
      }

      const fetchedHealth = await getHealth();
      setHealth(fetchedHealth);
    } catch (err: any) {
      console.error("Dashboard data fetch error:", err);
      showToast(err.message || "Failed to sync with SOC backend", "error");
    }
  };

  const showToast = (message: string, type: "error" | "info" = "info") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Poll data every 3 seconds
  useEffect(() => {
    fetchData(); // Initial load
    const interval = setInterval(() => {
      if (isPolling) fetchData();
    }, 3000);

    return () => clearInterval(interval);
  }, [isPolling]);

  // Calculations for stats
  const totalEventsToday = events.length;
  const activeFlagsCount = events.filter((e) => e.risk_score >= 66 || e.action === "HARD_BLOCK").length;
  const averageRiskScore = events.length > 0 
    ? events.reduce((sum, e) => sum + e.risk_score, 0) / events.length 
    : 0;

  // Active provider highlight
  const currentProvider = selectedEvent?.provider_used || "template";

  return (
    <div className="p-8 pb-12 min-h-screen">
      {/* Top Header Row */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-soc-border pb-6 mb-8">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="h-2 w-2 rounded-full bg-soc-cyan animate-pulse" />
            <span className="font-mono text-xs text-soc-cyan uppercase tracking-widest font-semibold">
              System Operations Active
            </span>
          </div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight text-soc-textPrimary">
            Setu Fraud Signals & Identity SOC
          </h1>
        </div>

        {/* Sync Indicator Control */}
        <button
          onClick={() => {
            setIsPolling(!isPolling);
            showToast(isPolling ? "Polling suspended" : "Real-time sync resumed", "info");
          }}
          className={`flex items-center gap-2 rounded border px-3 py-1.5 text-xs font-semibold uppercase tracking-wider transition-all ${
            isPolling
              ? "border-soc-cyan/30 bg-soc-cyan/5 text-soc-cyan"
              : "border-soc-border bg-soc-surface text-soc-textSecondary hover:text-soc-textPrimary"
          }`}
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isPolling ? "animate-spin" : ""}`} />
          {isPolling ? "SYNCING LIVE" : "PAUSED"}
        </button>
      </div>

      {/* Top Stats Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Metric 1: Total Events */}
        <div className="rounded-lg border border-soc-border bg-soc-surface p-5 flex flex-col justify-between">
          <span className="text-xs uppercase tracking-wider text-soc-textSecondary font-semibold">
            Total Ingestion Log
          </span>
          <div className="flex items-baseline justify-between mt-3">
            <span className="font-mono text-3xl font-bold text-soc-cyan">
              {totalEventsToday}
            </span>
            <Activity className="h-5 w-5 text-soc-cyan/40" />
          </div>
        </div>

        {/* Metric 2: Active Flags */}
        <div className="rounded-lg border border-soc-border bg-soc-surface p-5 flex flex-col justify-between relative overflow-hidden">
          <span className="text-xs uppercase tracking-wider text-soc-textSecondary font-semibold">
            Critical Alerts
          </span>
          <div className="flex items-baseline justify-between mt-3">
            <span className="font-mono text-3xl font-bold text-soc-red">
              {activeFlagsCount}
            </span>
            <ShieldAlert className={`h-5 w-5 ${activeFlagsCount > 0 ? "text-soc-red animate-bounce" : "text-soc-red/40"}`} />
          </div>
          {activeFlagsCount > 0 && (
            <span className="absolute left-0 top-0 bottom-0 w-[4px] bg-soc-red" />
          )}
        </div>

        {/* Metric 3: Avg Risk Score */}
        <div className="rounded-lg border border-soc-border bg-soc-surface p-5 flex flex-col justify-between">
          <span className="text-xs uppercase tracking-wider text-soc-textSecondary font-semibold">
            Average Risk Level
          </span>
          <div className="flex items-baseline justify-between mt-3">
            <span
              className={`font-mono text-3xl font-bold ${
                averageRiskScore >= 66
                  ? "text-soc-red"
                  : averageRiskScore >= 31
                  ? "text-soc-amber"
                  : "text-soc-green"
              }`}
            >
              {averageRiskScore.toFixed(1)}%
            </span>
            <Cpu className="h-5 w-5 text-soc-textSecondary/40" />
          </div>
        </div>

        {/* Metric 4: LLM Status */}
        <div className="rounded-lg border border-soc-border bg-soc-surface p-5 flex flex-col justify-between">
          <span className="text-xs uppercase tracking-wider text-soc-textSecondary font-semibold">
            Active Explainability
          </span>
          <div className="flex items-center justify-between mt-4">
            <span className="font-mono text-xs font-semibold text-soc-textPrimary uppercase">
              {currentProvider === "template" ? "Local Template" : currentProvider}
            </span>
            <div className="flex items-center gap-1.5">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-soc-cyan opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-soc-cyan"></span>
              </span>
              <span className="text-[10px] text-soc-cyan font-bold tracking-widest">ONLINE</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Column 1: Live Event Feed (40%) */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-soc-border pb-3">
            <h2 className="font-display text-lg font-bold text-soc-textPrimary uppercase tracking-wider">
              Live Threat Stream
            </h2>
            <Link
              href="/live-feed"
              className="flex items-center gap-1 text-xs font-semibold text-soc-cyan hover:underline"
            >
              VIEW ALL EVENTS
              <ChevronRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="flex flex-col gap-4 overflow-y-auto max-h-[580px] pr-2">
            {events.length === 0 ? (
              <div className="rounded-lg border border-dashed border-soc-border bg-soc-surface/40 p-8 text-center text-soc-textSecondary text-xs">
                No active threats monitored. Trigger a cyber simulator event in the Control Panel to populate.
              </div>
            ) : (
              events.map((ev) => (
                <EventCard
                  key={ev.id}
                  event={ev}
                  isSelected={selectedEvent?.id === ev.id}
                  onClick={() => setSelectedEvent(ev)}
                />
              ))
            )}
          </div>
        </div>

        {/* Column 2: Trust Signal Radar & SHAP (35%) */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="border-b border-soc-border pb-3">
            <h2 className="font-display text-lg font-bold text-soc-textPrimary uppercase tracking-wider">
              Signal Vector Breakdown
            </h2>
          </div>

          {selectedEvent ? (
            <div className="flex flex-col gap-6">
              {/* Radar Chart */}
              <div className="rounded-lg border border-soc-border bg-soc-surface p-4">
                <h3 className="font-display text-xs font-bold uppercase tracking-wider text-soc-textSecondary mb-2">
                  Multi-Factor GNN Signatures
                </h3>
                <RadarChart event={selectedEvent} />
              </div>

              {/* SHAP Chart */}
              <div className="rounded-lg border border-soc-border bg-soc-surface p-4">
                <h3 className="font-display text-xs font-bold uppercase tracking-wider text-soc-textSecondary mb-2">
                  Neural Weight Attributions (SHAP)
                </h3>
                <ShapBarChart attributions={selectedEvent.shap_attributions} />
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-soc-border bg-soc-surface/40 p-12 text-center text-soc-textSecondary text-xs">
              Select an incident event from the thread stream to view deep neural vectors.
            </div>
          )}
        </div>

        {/* Column 3: LLM & Database Status Panel (25%) */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          {/* LLM Status DOTS */}
          <LLMStatus activeProvider={currentProvider} />

          {/* Neo4j Health Panel */}
          <div className="rounded-lg border border-soc-border bg-soc-surface p-4">
            <h3 className="font-display text-sm font-semibold tracking-wider text-soc-textPrimary uppercase mb-4">
              Graph database metrics
            </h3>

            <div className="flex flex-col gap-3">
              {/* Database Connection */}
              <div className="flex items-center justify-between border-b border-soc-border/50 pb-2 text-xs">
                <span className="text-soc-textSecondary font-medium">Driver Connection</span>
                <span className="flex items-center gap-1.5 font-semibold">
                  <Database className={`h-3.5 w-3.5 ${health?.neo4j_connected ? "text-soc-green" : "text-soc-red animate-pulse"}`} />
                  <span className={health?.neo4j_connected ? "text-soc-green" : "text-soc-red"}>
                    {health?.neo4j_connected ? "CONNECTED" : "DISCONNECTED"}
                  </span>
                </span>
              </div>

              {/* Total Nodes */}
              <div className="flex items-center justify-between border-b border-soc-border/50 pb-2 text-xs">
                <span className="text-soc-textSecondary font-medium">Total Graph Nodes</span>
                <span className="font-mono text-soc-textPrimary font-semibold">
                  {health?.total_nodes ?? "---"}
                </span>
              </div>

              {/* Total Edges */}
              <div className="flex items-center justify-between border-b border-soc-border/50 pb-2 text-xs">
                <span className="text-soc-textSecondary font-medium">Total Graph Edges</span>
                <span className="font-mono text-soc-textPrimary font-semibold">
                  {health?.total_edges ?? "---"}
                </span>
              </div>

              {/* Flagged 24h */}
              <div className="flex items-center justify-between text-xs">
                <span className="text-soc-textSecondary font-medium">Flagged (Last 24h)</span>
                <span className="font-mono text-soc-red font-semibold">
                  {health?.flagged_last_24h ?? "---"}
                </span>
              </div>
            </div>

            {/* Model Info block */}
            <div className="rounded border border-soc-border bg-soc-bg p-3 mt-4 text-[10px]">
              <div className="flex justify-between mb-1 text-soc-textSecondary uppercase font-bold tracking-wider">
                <span>Core Graph Model</span>
                <span>Active</span>
              </div>
              <div className="text-soc-textPrimary font-mono font-bold mb-2">
                {health?.model_version || "Setu-GNN-v1.0.0"}
              </div>
              <div className="flex items-center gap-1 text-soc-textSecondary font-medium">
                <Clock className="h-3 w-3" />
                <span>Last trained: 12h ago (retraining hourly)</span>
              </div>
            </div>
            
            {/* View Full Graph shortcut */}
            <Link
              href="/graph-view"
              className="mt-4 block w-full text-center rounded border border-soc-cyan bg-soc-cyan/10 hover:bg-soc-cyan hover:text-soc-bg py-2 text-xs font-bold tracking-wider uppercase text-soc-cyan transition-all"
            >
              EXPLORE GLOBAL TRUST GRAPH
            </Link>
          </div>
          
          {/* View Details Case Link */}
          {selectedEvent && (
            <Link
              href={`/cases/${selectedEvent.id}`}
              className="flex items-center justify-center gap-1.5 rounded border border-soc-border bg-soc-surface hover:border-soc-cyan text-soc-textPrimary hover:text-soc-cyan py-2.5 text-xs font-bold tracking-wider uppercase transition-all"
            >
              ANALYZE CASE FILE {selectedEvent.entity_id}
              <ChevronRight className="h-4 w-4" />
            </Link>
          )}
        </div>
      </div>

      {/* Styled Error/Info Toast */}
      {toast && (
        <div className={`fixed bottom-6 right-6 z-50 rounded border p-4 shadow-2xl transition-all duration-300 max-w-sm ${
          toast.type === "error"
            ? "border-soc-red bg-soc-surface text-soc-red glow-red"
            : "border-soc-cyan bg-soc-surface text-soc-cyan glow-cyan"
        }`}>
          <div className="flex gap-3 items-start">
            <ShieldAlert className="h-5 w-5 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-display text-xs font-bold uppercase tracking-wider">
                {toast.type === "error" ? "SOC Operations Alert" : "System Notification"}
              </h4>
              <p className="text-xs text-soc-textPrimary mt-1 font-medium">
                {toast.message}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
