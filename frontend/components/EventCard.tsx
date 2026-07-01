"use client";

import React from "react";
import RiskScoreRing from "./RiskScoreRing";
import { RiskEvent } from "../lib/types";

interface EventCardProps {
  event: RiskEvent;
  isSelected: boolean;
  onClick: () => void;
}

export default function EventCard({ event, isSelected, onClick }: EventCardProps) {
  const actionStr = typeof event.action === 'object' ? (event.action as any).action : event.action;
  const isHardBlock = actionStr === "HARD_BLOCK" || event.risk_score >= 66;
  const isStepUp = actionStr === "STEP_UP_AUTH" || (event.risk_score >= 31 && event.risk_score <= 65);

  // Map action action string
  const actionLabel = actionStr ? actionStr.replace(/_/g, " ") : "SILENT PASS";

  // Action badge styles
  let badgeClass = "bg-soc-green/10 text-soc-green border-soc-green/30";
  if (isHardBlock) {
    badgeClass = "bg-soc-red/10 text-soc-red border-soc-red/30";
  } else if (isStepUp) {
    badgeClass = "bg-soc-amber/10 text-soc-amber border-soc-amber/30";
  }

  // Format relative timestamp
  const getRelativeTime = (isoString: string) => {
    try {
      const diffMs = new Date().getTime() - new Date(isoString).getTime();
      const diffSec = Math.max(0, Math.floor(diffMs / 1000));
      if (diffSec < 60) return `${diffSec}s ago`;
      const diffMin = Math.floor(diffSec / 60);
      if (diffMin < 60) return `${diffMin}m ago`;
      const diffHour = Math.floor(diffMin / 60);
      return `${diffHour}h ago`;
    } catch {
      return "now";
    }
  };

  return (
    <div
      onClick={onClick}
      className={`relative cursor-pointer rounded-lg border p-4 transition-all duration-300 hover:scale-[1.01] ${
        isSelected
          ? "border-soc-cyan bg-soc-cyan/5 shadow-[0_0_12px_rgba(0,212,255,0.1)]"
          : "border-soc-border bg-soc-surface hover:border-soc-textSecondary/30"
      } ${isHardBlock ? "animate-pulse-fast border-soc-red/20 shadow-[0_0_10px_rgba(255,59,92,0.05)]" : ""}`}
    >
      <div className="flex items-start justify-between gap-3">
        {/* Left Side: Score & Primary Info */}
        <div className="flex items-center gap-3">
          <RiskScoreRing score={event.risk_score} size={48} strokeWidth={4} />
          
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span
                className={`rounded px-1.5 py-0.5 text-[9px] font-bold tracking-wider uppercase border ${
                  event.entity_type === "EMPLOYEE_ACCESS"
                    ? "bg-soc-purple/10 text-soc-purple border-soc-purple/30"
                    : "bg-soc-cyan/10 text-soc-cyan border-soc-cyan/30"
                }`}
              >
                {event.entity_type === "EMPLOYEE_ACCESS" ? "Staff Access" : "Customer Session"}
              </span>
              <span className="font-mono text-[10px] text-soc-textSecondary">
                {getRelativeTime(event.timestamp)}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <div className="font-mono text-sm font-semibold text-soc-textPrimary tracking-tight">
                {event.entity_id}
              </div>
              {event.confidence && (
                <div
                  title={event.confidence.reasoning}
                  className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full border text-[9px] font-mono cursor-help"
                  style={{
                    borderColor: event.confidence.confidence_label === 'HIGH' ? '#00D4FF'
                               : event.confidence.confidence_label === 'MEDIUM' ? '#FFB800'
                               : '#FF3B5C',
                    color: event.confidence.confidence_label === 'HIGH' ? '#00D4FF'
                         : event.confidence.confidence_label === 'MEDIUM' ? '#FFB800'
                         : '#FF3B5C'
                  }}
                >
                  CONF: {event.confidence.confidence_label} {event.confidence.confidence_pct}%
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Side: Action pill */}
        <span className={`rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider ${badgeClass}`}>
          {actionLabel}
        </span>
      </div>

      {/* Explanation Text */}
      <div className="mt-3">
        <p className="text-xs text-soc-textSecondary line-clamp-2 hover:line-clamp-none transition-all duration-300 leading-normal">
          {event.explanation}
        </p>
      </div>

      {/* Tiny Status Indicator line */}
      <div
        className={`absolute bottom-0 left-0 right-0 h-[2px] rounded-b-lg ${
          isHardBlock ? "bg-soc-red" : isStepUp ? "bg-soc-amber" : "bg-soc-green"
        }`}
      />
    </div>
  );
}
