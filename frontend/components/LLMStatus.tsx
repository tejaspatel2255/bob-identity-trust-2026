"use client";

import React from "react";

interface LLMStatusProps {
  activeProvider?: string; // "llama-3.3-70b" | "gemini-flash" | "gpt-4o-mini" | "template"
}

export default function LLMStatus({ activeProvider }: LLMStatusProps) {
  const chain = [
    { key: "llama-3.3-70b", name: "Llama 3.3 (OpenRouter)", tier: "Free Tier" },
    { key: "gemini-flash", name: "Gemini Flash (OpenRouter)", tier: "Free Tier" },
    { key: "gpt-4o-mini", name: "GPT-4o-Mini (OpenRouter)", tier: "Paid Tier" },
    { key: "template", name: "Deterministic Template", tier: "Local Offline" },
  ];

  return (
    <div className="rounded-lg border border-soc-border bg-soc-surface p-4">
      <h3 className="font-display text-sm font-semibold tracking-wider text-soc-textPrimary uppercase mb-4">
        AI Explanation Routing
      </h3>
      <div className="flex flex-col gap-3">
        {chain.map((model, idx) => {
          const isSelected = activeProvider === model.key;
          
          return (
            <div
              key={model.key}
              className={`flex items-center justify-between rounded border p-2.5 transition-all ${
                isSelected
                  ? "border-soc-cyan bg-soc-cyan/5 shadow-[0_0_8px_rgba(0,212,255,0.1)]"
                  : "border-soc-border bg-soc-bg/50"
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs text-soc-textSecondary">
                  #{idx + 1}
                </span>
                <div>
                  <div className="text-xs font-semibold text-soc-textPrimary">
                    {model.name}
                  </div>
                  <div className="font-mono text-[10px] text-soc-textSecondary">
                    {model.tier}
                  </div>
                </div>
              </div>

              {/* Status Dot */}
              <div className="flex items-center gap-2">
                <span className="font-mono text-[10px] text-soc-textSecondary">
                  {isSelected ? "ACTIVE" : "READY"}
                </span>
                <span className="relative flex h-2.5 w-2.5">
                  {isSelected && (
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-soc-cyan opacity-75"></span>
                  )}
                  <span
                    className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                      isSelected
                        ? "bg-soc-cyan"
                        : model.key === "template"
                        ? "bg-soc-green"
                        : "bg-soc-textSecondary/40"
                    }`}
                  ></span>
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
