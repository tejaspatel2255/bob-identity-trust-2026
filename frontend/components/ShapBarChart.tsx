"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Cell,
  Tooltip,
  CartesianGrid
} from "recharts";
import { ShapAttribution } from "../lib/types";

interface ShapBarChartProps {
  attributions: ShapAttribution[];
}

export default function ShapBarChart({ attributions }: ShapBarChartProps) {
  // Sort and format the data
  const data = attributions.map((attr) => ({
    name: attr.feature.replace(/_/g, " "),
    contribution: attr.contribution,
    rawName: attr.feature,
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const dataPoint = payload[0].payload;
      const val = dataPoint.contribution;
      return (
        <div className="rounded border border-soc-border bg-soc-surface p-2 shadow-xl">
          <p className="text-xs font-semibold text-soc-textPrimary">{dataPoint.name}</p>
          <p className="font-mono text-[11px] text-soc-textSecondary mt-0.5">
            Contribution: <span className={val > 0 ? "text-soc-red" : "text-soc-green"}>
              {val > 0 ? "+" : ""}{val.toFixed(2)}
            </span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1E2D4A" horizontal={true} vertical={false} />
          
          <XAxis
            type="number"
            stroke="#6B84A8"
            fontSize={10}
            fontFamily="monospace"
            tickLine={false}
            axisLine={false}
          />
          
          <YAxis
            dataKey="name"
            type="category"
            stroke="#6B84A8"
            fontSize={10}
            fontFamily="sans-serif"
            tickLine={false}
            axisLine={false}
            width={100}
          />
          
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(30, 45, 74, 0.2)" }} />
          
          <Bar dataKey="contribution" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => {
              // Red for positive risk contribution, Green for baseline/safe contributors
              const fill = entry.contribution > 0.1 ? "#FF3B5C" : "#00E5A0";
              return <Cell key={`cell-${index}`} fill={fill} />;
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
