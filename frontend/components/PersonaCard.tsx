"use client";

import React from "react";
import { User, ShieldAlert, AlertTriangle } from "lucide-react";
import { Persona } from "../lib/types";

interface PersonaCardProps {
  persona: Persona;
  onRun: () => void;
  isLoading: boolean;
  isActive: boolean;
}

export default function PersonaCard({ persona, onRun, isLoading, isActive }: PersonaCardProps) {
  // Border colors based on persona trust level
  const borderStyles = {
    safe: "border-soc-green/20 hover:border-soc-green bg-soc-green/5",
    warning: "border-soc-amber/20 hover:border-soc-amber bg-soc-amber/5",
    danger: "border-soc-red/20 hover:border-soc-red bg-soc-red/5 hover:shadow-[0_0_15px_rgba(255,59,92,0.1)]",
    purple: "border-soc-purple/20 hover:border-soc-purple bg-soc-purple/5",
  };

  const ringStyles = {
    safe: "border-soc-green text-soc-green",
    warning: "border-soc-amber text-soc-amber",
    danger: "border-soc-red text-soc-red animate-pulse",
    purple: "border-soc-purple text-soc-purple",
  };

  const getAvatarIcon = () => {
    switch (persona.trustLevel) {
      case "safe":
        return <User className="h-6 w-6" />;
      case "danger":
        return <ShieldAlert className="h-6 w-6 animate-pulse" />;
      case "purple":
        return <User className="h-6 w-6" />;
      default:
        return <AlertTriangle className="h-6 w-6" />;
    }
  };

  return (
    <div
      className={`flex flex-col justify-between rounded-lg border p-6 transition-all duration-300 ${
        isActive
          ? "border-soc-cyan bg-soc-surface shadow-[0_0_15px_rgba(0,212,255,0.1)] scale-[1.02]"
          : `bg-soc-surface ${borderStyles[persona.trustLevel as keyof typeof borderStyles]}`
      }`}
    >
      <div>
        {/* Avatar Ring */}
        <div className="flex items-center gap-4 mb-4">
          <div
            className={`flex h-12 w-12 items-center justify-center rounded-full border-2 bg-soc-bg ${
              ringStyles[persona.trustLevel as keyof typeof ringStyles]
            } ${persona.trustLevel === "danger" ? "relative" : ""}`}
          >
            {getAvatarIcon()}
            {persona.trustLevel === "danger" && (
              <span className="absolute -right-0.5 -top-0.5 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-soc-red opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-soc-red"></span>
              </span>
            )}
          </div>
          
          <div>
            <h3 className="font-display text-base font-bold text-soc-textPrimary">
              {persona.name}
            </h3>
            <span className="font-mono text-[9px] uppercase tracking-wider text-soc-textSecondary">
              {persona.entityId}
            </span>
          </div>
        </div>

        {/* Profile Description */}
        <p className="text-xs text-soc-textSecondary leading-relaxed mb-6 min-h-[40px]">
          {persona.description}
        </p>
      </div>

      {/* Action Button */}
      <button
        onClick={onRun}
        disabled={isLoading}
        className={`w-full rounded py-2 text-xs font-semibold tracking-wider uppercase transition-all duration-200 border ${
          isLoading
            ? "border-soc-border bg-soc-surface text-soc-textSecondary cursor-not-allowed"
            : isActive
            ? "border-soc-cyan bg-soc-cyan text-soc-bg hover:bg-soc-cyan/95"
            : "border-soc-border bg-soc-bg text-soc-textPrimary hover:border-soc-cyan hover:bg-soc-cyan/10"
        }`}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-soc-textSecondary border-t-transparent"></span>
            Processing Simulation...
          </span>
        ) : (
          `Run Simulation`
        )}
      </button>
    </div>
  );
}
