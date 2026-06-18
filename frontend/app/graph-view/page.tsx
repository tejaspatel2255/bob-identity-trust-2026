"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "../../lib/api";
import { GraphData } from "../../lib/types";
import GraphCanvas from "../../components/GraphCanvas";
import { 
  ArrowLeft, 
  Network, 
  Filter, 
  Database,
  HelpCircle,
  RefreshCw 
} from "lucide-react";

const ALL_NODE_TYPES = ["Customer", "Device", "Session", "Employee", "Account", "Beneficiary"];

export default function GlobalGraphView() {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [activeFilters, setActiveFilters] = useState<string[]>(ALL_NODE_TYPES);

  const loadGraphData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getFullGraph();
      setGraph(data);
    } catch (err: any) {
      console.error("Global graph fetch error:", err);
      setError(err.message || "Failed to load database network.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraphData();
  }, []);

  const handleFilterToggle = (type: string) => {
    setActiveFilters((prev) =>
      prev.includes(type)
        ? prev.filter((t) => t !== type)
        : [...prev, type]
    );
  };

  const selectAllFilters = () => {
    setActiveFilters(ALL_NODE_TYPES);
  };

  const clearAllFilters = () => {
    setActiveFilters([]);
  };

  return (
    <div className="p-8 pb-12 min-h-screen">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-soc-border pb-6 mb-8">
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="flex h-9 w-9 items-center justify-center rounded border border-soc-border bg-soc-surface text-soc-textSecondary hover:border-soc-cyan hover:text-soc-cyan transition-all"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-[10px] text-soc-textSecondary uppercase tracking-widest font-semibold">
                NEO4J RELATION MAPPING
              </span>
            </div>
            <h1 className="font-display text-2xl font-extrabold tracking-tight text-soc-textPrimary flex items-center gap-2">
              <Network className="h-6 w-6 text-soc-cyan" />
              Global Identity Trust Graph
            </h1>
          </div>
        </div>

        {/* Refresh button */}
        <button
          onClick={loadGraphData}
          disabled={loading}
          className="flex items-center justify-center gap-2 rounded border border-soc-border bg-soc-surface hover:border-soc-cyan text-soc-textPrimary hover:text-soc-cyan px-4 py-2.5 text-xs font-semibold uppercase tracking-wider transition-all disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          RELOAD GRAPH
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 rounded-lg border border-soc-border bg-soc-surface p-4 mb-6">
        <div className="flex items-center gap-2 text-soc-textSecondary text-xs font-semibold uppercase tracking-wider">
          <Filter className="h-3.5 w-3.5 text-soc-cyan" />
          Graph Node Visibility Filters
        </div>

        {/* Checkbox triggers */}
        <div className="flex flex-wrap gap-2 text-[10px]">
          {ALL_NODE_TYPES.map((type) => {
            const isChecked = activeFilters.includes(type);
            
            // Map node colors to checkbox borders
            const typeColorMap: Record<string, string> = {
              Customer: "border-[#00D4FF] text-[#00D4FF] bg-[#00D4FF]/5",
              Device: "border-[#7B61FF] text-[#7B61FF] bg-[#7B61FF]/5",
              Session: "border-[#FFFFFF] text-[#FFFFFF] bg-[#FFFFFF]/5",
              Employee: "border-[#FFB800] text-[#FFB800] bg-[#FFB800]/5",
              Account: "border-[#00E5A0] text-[#00E5A0] bg-[#00E5A0]/5",
              Beneficiary: "border-[#FF3B5C] text-[#FF3B5C] bg-[#FF3B5C]/5",
            };

            return (
              <button
                key={type}
                onClick={() => handleFilterToggle(type)}
                className={`rounded border px-2.5 py-1.5 font-bold uppercase tracking-wider transition-all ${
                  isChecked
                    ? typeColorMap[type] || "border-soc-cyan bg-soc-cyan/15 text-soc-cyan"
                    : "border-soc-border bg-soc-bg/20 text-soc-textSecondary hover:text-soc-textPrimary"
                }`}
              >
                {type}
              </button>
            );
          })}
        </div>

        {/* Global Select Buttons */}
        <div className="flex gap-2 text-[9px] font-bold uppercase tracking-wider">
          <button
            onClick={selectAllFilters}
            className="rounded border border-soc-border hover:border-soc-textSecondary bg-soc-bg px-2.5 py-1 text-soc-textPrimary transition-all"
          >
            Show All
          </button>
          <button
            onClick={clearAllFilters}
            className="rounded border border-soc-border hover:border-soc-textSecondary bg-soc-bg px-2.5 py-1 text-soc-textPrimary transition-all"
          >
            Clear All
          </button>
        </div>
      </div>

      {/* Main Graph Grid Content */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Side: 2D Canvas (col-span-8) */}
        <div className="lg:col-span-8">
          {loading ? (
            <div className="flex h-[550px] w-full items-center justify-center rounded-lg border border-soc-border bg-soc-surface/40 text-soc-cyan">
              <div className="flex flex-col items-center gap-3">
                <span className="h-8 w-8 animate-spin rounded-full border-2 border-soc-cyan border-t-transparent"></span>
                <span className="font-mono text-xs uppercase tracking-widest animate-pulse">Running graph query...</span>
              </div>
            </div>
          ) : error ? (
            <div className="flex h-[550px] w-full items-center justify-center rounded-lg border border-soc-border bg-soc-surface/40 text-soc-red p-6 text-center">
              <div>
                <Database className="h-10 w-10 mx-auto mb-4 text-soc-red" />
                <h3 className="font-display text-lg font-bold text-soc-textPrimary mb-2">Graph Database Error</h3>
                <p className="text-xs text-soc-textSecondary max-w-md mb-6">{error}</p>
                <button
                  onClick={loadGraphData}
                  className="rounded border border-soc-cyan bg-soc-cyan/15 px-4 py-2 text-xs font-bold uppercase tracking-wider text-soc-cyan hover:bg-soc-cyan hover:text-soc-bg transition-all"
                >
                  Retry Database Connect
                </button>
              </div>
            </div>
          ) : graph ? (
            <GraphCanvas
              nodes={graph.nodes}
              edges={graph.edges}
              onNodeSelect={(node) => setSelectedNode(node)}
              height={550}
              highlightNeighbors={true}
              filterTypes={activeFilters}
            />
          ) : null}
        </div>

        {/* Right Side: Side Panel Inspector (col-span-4) */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          
          {/* Instructions Overlay */}
          <div className="rounded-lg border border-soc-border bg-soc-surface p-5 text-xs text-soc-textSecondary leading-relaxed">
            <h3 className="font-display text-xs font-bold uppercase tracking-wider text-soc-cyan mb-2.5 flex items-center gap-1.5">
              <HelpCircle className="h-4 w-4" />
              Graph Navigation Instructions
            </h3>
            <ul className="list-disc pl-4 space-y-1.5 font-medium">
              <li>Use the scroll wheel to **zoom** in or out of the canvas.</li>
              <li>**Click and drag** the canvas background to pan across the network layout.</li>
              <li>**Drag individual nodes** to alter force calculations and pin layouts.</li>
              <li>**Click a node** to highlight its direct 2-hop neighborhood and inspect database attributes.</li>
              <li>Click the canvas background to **reset neighborhood filters**.</li>
            </ul>
          </div>

          {/* Property Inspector */}
          {selectedNode ? (
            <div className="rounded-lg border border-soc-border bg-soc-surface p-5">
              <div className="flex items-center justify-between border-b border-soc-border/60 pb-3 mb-3">
                <h3 className="font-display text-xs font-bold uppercase tracking-wider text-soc-cyan">
                  Neo4j Node Inspector
                </h3>
                <span className="font-mono text-[10px] text-soc-textSecondary uppercase font-bold">
                  [{selectedNode.type}]
                </span>
              </div>
              
              <div className="flex flex-col gap-3 max-h-72 overflow-y-auto pr-2">
                {/* Node ID */}
                <div className="border-b border-soc-border/20 pb-2 text-xs">
                  <span className="text-soc-textSecondary block font-bold mb-0.5 uppercase text-[9px] tracking-wider">Node Registry ID</span>
                  <span className="font-mono text-soc-textPrimary font-bold">{selectedNode.id}</span>
                </div>

                {/* Properties list */}
                {Object.entries(selectedNode.properties).map(([key, val]: any) => {
                  // Skip id if already shown
                  if (key === "id") return null;

                  return (
                    <div key={key} className="border-b border-soc-border/20 pb-2 text-xs">
                      <span className="text-soc-textSecondary block font-semibold mb-0.5">{key}</span>
                      <span className="font-mono text-soc-textPrimary break-all">
                        {typeof val === "boolean" ? (val ? "TRUE" : "FALSE") : val.toString()}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-dashed border-soc-border bg-soc-surface/40 p-12 text-center text-xs text-soc-textSecondary uppercase font-mono tracking-wider">
              Select any graph node to inspect Neo4j node attributes.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
