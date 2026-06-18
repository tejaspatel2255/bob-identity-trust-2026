"use client";

import React from "react";
import {
  Radar,
  RadarChart as ReChartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer
} from "recharts";
import { RiskEvent } from "../lib/types";

interface RadarChartProps {
  event: RiskEvent;
}

export default function RadarChart({ event }: RadarChartProps) {
  // Helper to map event features to a standard 0-100 radar axis
  const getRadarData = (ev: RiskEvent) => {
    // Look at GNN SHAP features and baseline indicators
    const shaps = ev.shap_attributions || [];
    
    const getContribution = (featureSub: string) => {
      const found = shaps.find((s) => s.feature.toLowerCase().includes(featureSub.toLowerCase()));
      return found ? found.contribution : 0;
    };

    // Calculate axis values based on contributions (scaled 10 to 100)
    const simSwap = getContribution("sim_swap") > 0 ? 100 : 10;
    const deviceTrust = getContribution("new_device") > 0 ? 90 : 20; // High contribution = High risk
    const geovelocity = getContribution("geovelocity") > 0 ? 95 : 15;
    const beneficiary = getContribution("beneficiary") > 0 ? 80 : 10;
    const accessHours = getContribution("outside_hours") > 0 ? 85 : 12;
    const drift = getContribution("drift") > 0 || getContribution("behavioral") > 0 ? 70 : 25;

    return [
      { subject: "SIM Swap Risk", value: simSwap },
      { subject: "Device Trust", value: deviceTrust },
      { subject: "Geovelocity", value: geovelocity },
      { subject: "Beneficiary Trust", value: beneficiary },
      { subject: "Access Hours", value: accessHours },
      { subject: "Behavioral Drift", value: drift },
    ];
  };

  const data = getRadarData(event);

  return (
    <div className="h-64 w-full flex items-center justify-center">
      <ResponsiveContainer width="100%" height="100%">
        <ReChartsRadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#1E2D4A" />
          <PolarAngleAxis
            dataKey="subject"
            stroke="#6B84A8"
            fontSize={10}
            tickLine={false}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            stroke="#1E2D4A"
            tick={false}
            axisLine={false}
          />
          <Radar
            name="Trust Signals"
            dataKey="value"
            stroke="#00D4FF"
            fill="#00D4FF"
            fillOpacity={0.15}
          />
        </ReChartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
}
