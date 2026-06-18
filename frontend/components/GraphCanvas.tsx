"use client";

import React, { useEffect, useState, useRef } from "react";
import dynamic from "next/dynamic";
import { NodeModel, EdgeModel } from "../lib/types";

// Import react-force-graph-2d dynamically with SSR disabled and explicit module default resolution
const ForceGraph2D = dynamic(
  () => import("react-force-graph-2d").then((mod) => mod.default || mod),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full w-full items-center justify-center bg-soc-bg text-soc-cyan">
        <div className="flex flex-col items-center gap-3">
          <span className="h-8 w-8 animate-spin rounded-full border-2 border-soc-cyan border-t-transparent"></span>
          <span className="font-mono text-xs uppercase tracking-widest animate-pulse">Initializing Trust Canvas...</span>
        </div>
      </div>
    ),
  }
);

interface GraphCanvasProps {
  nodes: NodeModel[];
  edges: EdgeModel[];
  onNodeSelect?: (node: any) => void;
  height?: number;
  highlightNeighbors?: boolean;
  filterTypes?: string[]; // Types of nodes to show
}

export default function GraphCanvas({
  nodes,
  edges,
  onNodeSelect,
  height = 500,
  highlightNeighbors = false,
  filterTypes = [],
}: GraphCanvasProps) {
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isMounted, setIsMounted] = useState(false);
  const [width, setWidth] = useState<number>(600);
  const [graphData, setGraphData] = useState<{ nodes: any[]; links: any[] }>({ nodes: [], links: [] });
  const [highlightNodes, setHighlightNodes] = useState<Set<string>>(new Set());
  const [highlightLinks, setHighlightLinks] = useState<Set<any>>(new Set());
  const [hoverNode, setHoverNode] = useState<any>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted || !containerRef.current) return;

    const initialWidth = containerRef.current.clientWidth;
    setWidth(initialWidth > 200 ? initialWidth : 600);

    const handleResize = () => {
      if (containerRef.current) {
        const w = containerRef.current.clientWidth;
        setWidth(w > 200 ? w : 600);
      }
    };

    window.addEventListener("resize", handleResize);
    
    // Check after layout settles
    const timer = setTimeout(handleResize, 100);

    return () => {
      window.removeEventListener("resize", handleResize);
      clearTimeout(timer);
    };
  }, [isMounted]);

  useEffect(() => {
    // 1. Filter nodes by type if filterTypes is provided
    let filteredNodes = nodes;
    if (filterTypes && filterTypes.length > 0) {
      filteredNodes = nodes.filter((n) => filterTypes.includes(n.type));
    }

    const nodeIds = new Set(filteredNodes.map((n) => n.id));

    // 2. Filter edges to only connect nodes that are visible
    const filteredEdges = edges.filter(
      (e) => nodeIds.has(e.source) && nodeIds.has(e.target)
    );

    // 3. Map to format required by react-force-graph
    const mappedNodes = filteredNodes.map((n) => ({
      id: n.id,
      type: n.type,
      name: n.properties.name || n.properties.fingerprint || n.id,
      properties: n.properties,
    }));

    const mappedLinks = filteredEdges.map((e) => ({
      id: `${e.source}-${e.target}-${e.type}`,
      source: e.source,
      target: e.target,
      type: e.type,
      properties: e.properties,
    }));

    setGraphData({ nodes: mappedNodes, links: mappedLinks });
  }, [nodes, edges, filterTypes]);

  // Color mapping based on design brief
  const getNodeColor = (type: string) => {
    switch (type) {
      case "Customer":
        return "#00D4FF"; // cyan
      case "Device":
        return "#7B61FF"; // purple
      case "Session":
        return "#FFFFFF"; // white
      case "Employee":
        return "#FFB800"; // orange / amber
      case "Account":
        return "#00E5A0"; // green
      case "Beneficiary":
        return "#FF3B5C"; // red
      default:
        return "#6B84A8"; // secondary grey
    }
  };

  // Node size relative weight
  const getNodeVal = (type: string) => {
    switch (type) {
      case "Customer":
        return 7;
      case "Employee":
        return 6;
      case "Account":
        return 5;
      case "Session":
        return 4.5;
      case "Device":
        return 4.5;
      case "Beneficiary":
        return 5;
      default:
        return 4;
    }
  };

  // Handle neighborhood highlight calculations on node click/hover
  const handleNodeClick = (node: any) => {
    if (onNodeSelect) {
      onNodeSelect(node);
    }

    if (highlightNeighbors) {
      const neighbors = new Set<string>();
      const neighborLinks = new Set<any>();

      neighbors.add(node.id);

      // Find 1-hop neighbors
      graphData.links.forEach((link) => {
        const sourceId = typeof link.source === "object" ? link.source.id : link.source;
        const targetId = typeof link.target === "object" ? link.target.id : link.target;
        
        if (sourceId === node.id) {
          neighbors.add(targetId);
          neighborLinks.add(link);
        } else if (targetId === node.id) {
          neighbors.add(sourceId);
          neighborLinks.add(link);
        }
      });

      // Find 2-hop neighbors
      graphData.links.forEach((link) => {
        const sourceId = typeof link.source === "object" ? link.source.id : link.source;
        const targetId = typeof link.target === "object" ? link.target.id : link.target;

        if (neighbors.has(sourceId) && !neighbors.has(targetId)) {
          // Check if link is connected to a 1-hop neighbor
          neighborLinks.add(link);
        } else if (neighbors.has(targetId) && !neighbors.has(sourceId)) {
          neighborLinks.add(link);
        }
      });

      // Include all neighbor IDs in the set
      graphData.links.forEach((link) => {
        const sourceId = typeof link.source === "object" ? link.source.id : link.source;
        const targetId = typeof link.target === "object" ? link.target.id : link.target;
        if (neighborLinks.has(link)) {
          neighbors.add(sourceId);
          neighbors.add(targetId);
        }
      });

      setHighlightNodes(neighbors);
      setHighlightLinks(neighborLinks);
    }
  };

  const handleCanvasClick = () => {
    if (highlightNeighbors) {
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
    }
  };

  return (
    <div ref={containerRef} className="relative w-full rounded-lg border border-soc-border bg-soc-surface/40 overflow-hidden">
      {/* Legend overlays */}
      <div className="absolute left-4 top-4 z-10 flex flex-wrap gap-x-4 gap-y-2 rounded border border-soc-border bg-soc-surface/80 p-2.5 backdrop-blur-sm">
        <div className="flex items-center gap-1.5 text-[10px]">
          <span className="h-2 w-2 rounded-full bg-[#00D4FF]" />
          <span className="text-soc-textSecondary uppercase tracking-wider font-semibold">Customer</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px]">
          <span className="h-2 w-2 rounded-full bg-[#7B61FF]" />
          <span className="text-soc-textSecondary uppercase tracking-wider font-semibold">Device</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px]">
          <span className="h-2 w-2 rounded-full bg-[#FFFFFF]" />
          <span className="text-soc-textSecondary uppercase tracking-wider font-semibold">Session</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px]">
          <span className="h-2 w-2 rounded-full bg-[#FFB800]" />
          <span className="text-soc-textSecondary uppercase tracking-wider font-semibold">Staff</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px]">
          <span className="h-2 w-2 rounded-full bg-[#00E5A0]" />
          <span className="text-soc-textSecondary uppercase tracking-wider font-semibold">Account</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px]">
          <span className="h-2 w-2 rounded-full bg-[#FF3B5C]" />
          <span className="text-soc-textSecondary uppercase tracking-wider font-semibold">Beneficiary</span>
        </div>
      </div>

      {isMounted ? (
        <ForceGraph2D
          ref={fgRef}
          graphData={graphData}
          width={width}
          height={height}
          backgroundColor="#0A0E1A"
          nodeColor={(node: any) => {
            if (highlightNodes.size > 0 && !highlightNodes.has(node.id)) {
              return "rgba(30, 45, 74, 0.2)"; // Dimmed color
            }
            return getNodeColor(node.type);
          }}
          nodeVal={(node: any) => getNodeVal(node.type)}
          nodeLabel={(node: any) => `<span style="font-family: monospace; font-size: 11px;">[${node.type}] ${node.name}</span>`}
          linkLabel={(link: any) => `<span style="font-family: monospace; font-size: 10px;">${link.type}</span>`}
          linkColor={(link: any) => {
            if (highlightLinks.size > 0 && !highlightLinks.has(link)) {
              return "rgba(30, 45, 74, 0.05)";
            }
            return "rgba(30, 45, 74, 0.4)";
          }}
          linkWidth={(link: any) => (highlightLinks.has(link) ? 3 : 1)}
          linkDirectionalParticles={(link: any) => (highlightLinks.size === 0 || highlightLinks.has(link) ? 2 : 0)}
          linkDirectionalParticleSpeed={0.006}
          linkDirectionalParticleWidth={2}
          linkDirectionalParticleColor={(link: any) => {
            const targetNode = link.target;
            const targetType = typeof targetNode === "object" ? targetNode.type : "";
            return getNodeColor(targetType);
          }}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          onNodeClick={handleNodeClick}
          onBackgroundClick={handleCanvasClick}
          cooldownTicks={120}
          d3VelocityDecay={0.3}
        />
      ) : (
        <div className="flex h-full w-full items-center justify-center bg-soc-bg text-soc-cyan" style={{ height }}>
          <div className="flex flex-col items-center gap-3">
            <span className="h-8 w-8 animate-spin rounded-full border-2 border-soc-cyan border-t-transparent"></span>
            <span className="font-mono text-xs uppercase tracking-widest animate-pulse">Initializing Trust Canvas...</span>
          </div>
        </div>
      )}
    </div>
  );
}
