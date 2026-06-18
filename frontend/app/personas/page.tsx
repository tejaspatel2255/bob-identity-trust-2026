"use client";

import React, { useState } from "react";
import Link from "next/link";
import { scoreRisk } from "../../lib/api";
import { Persona, RiskScoreResponse } from "../../lib/types";
import PersonaCard from "../../components/PersonaCard";
import RiskScoreRing from "../../components/RiskScoreRing";
import TypewriterText from "../../components/TypewriterText";
import { 
  ArrowLeft, 
  Play, 
  Terminal, 
  ShieldCheck, 
  Cpu, 
  ArrowRight,
  ShieldAlert
} from "lucide-react";

const DEMO_PERSONAS: Persona[] = [
  {
    id: "persona-priya",
    name: "Priya Sharma",
    trustLevel: "safe",
    description: "Regular customer session. Authenticated on known mobile device. Operating during normal hours. Familiar IP geolocation.",
    entityType: "CUSTOMER_SESSION",
    entityId: "CUST_PRIYA_SHARMA",
    eventData: {
      sim_swap_flag: false,
      is_new_device: false,
      geovelocity_jump_km: 12,
      is_first_time_beneficiary: false,
      outside_working_hours: false,
      behavioral_baseline_drift: 0.04,
      typing_cadence_wpm: 82,
      swipe_speed_px_per_sec: 420
    }
  },
  {
    id: "persona-attacker",
    name: "Unknown Attacker",
    trustLevel: "danger",
    description: "SIM swap detected 90 minutes ago. Device identifier is new. Geovelocity jump of 1,200km in under 1 hour. Target transfer: ₹75,000 to first-time beneficiary.",
    entityType: "CUSTOMER_SESSION",
    entityId: "CUST_UNKNOWN_ATTACKER",
    eventData: {
      sim_swap_flag: true,
      is_new_device: true,
      geovelocity_jump_km: 1200,
      is_first_time_beneficiary: true,
      outside_working_hours: true,
      behavioral_baseline_drift: 0.78,
      typing_cadence_wpm: 140,
      swipe_speed_px_per_sec: 180
    }
  },
  {
    id: "persona-ramesh",
    name: "Ramesh Patel",
    trustLevel: "purple",
    description: "Branch officer logging in at 11:42 PM (outside shift hours). Accessed 3 HIGH-balance VIP customer accounts within 10 minutes. Account recovery requests followed.",
    entityType: "EMPLOYEE_ACCESS",
    entityId: "EMP_RAMESH_PATEL",
    eventData: {
      outside_hours: true,
      bulk_account_access: true,
      high_balance_accessed_count: 4,
      recovery_requests_followed: true,
      is_new_device: false,
      behavioral_baseline_drift: 0.65
    }
  }
];

export default function Personas() {
  const [selectedPersona, setSelectedPersona] = useState<Persona | null>(null);
  const [result, setResult] = useState<RiskScoreResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSimulation = async (persona: Persona) => {
    try {
      setIsLoading(true);
      setError(null);
      setResult(null);
      setSelectedPersona(persona);

      const response = await scoreRisk({
        entity_type: persona.entityType,
        entity_id: persona.entityId,
        event_data: persona.eventData
      });

      setResult(response);
    } catch (err: any) {
      console.error("Simulation run error:", err);
      setError(err.message || "Failed to complete risk simulation.");
    } finally {
      setIsLoading(false);
    }
  };

  const getActionStyles = (action: string) => {
    switch (action) {
      case "HARD_BLOCK":
        return "bg-soc-red/10 border-soc-red/30 text-soc-red";
      case "STEP_UP_AUTH":
        return "bg-soc-amber/10 border-soc-amber/30 text-soc-amber";
      default:
        return "bg-soc-green/10 border-soc-green/30 text-soc-green";
    }
  };

  return (
    <div className="p-8 pb-16 min-h-screen">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8 border-b border-soc-border pb-6">
        <Link
          href="/dashboard"
          className="flex h-9 w-9 items-center justify-center rounded border border-soc-border bg-soc-surface text-soc-textSecondary hover:border-soc-cyan hover:text-soc-cyan transition-all"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <span className="font-mono text-[10px] text-soc-textSecondary uppercase tracking-widest font-semibold">
            CYBER SECURITY SANDBOX
          </span>
          <h1 className="font-display text-2xl font-extrabold tracking-tight text-soc-textPrimary">
            Threat Persona Simulation Console
          </h1>
        </div>
      </div>

      {/* Main Grid description */}
      <div className="mb-8 max-w-3xl">
        <p className="text-xs text-soc-textSecondary leading-relaxed">
          Select one of the default user profiles below to run a real-time ingestion scenario. 
          The transaction metrics will be evaluated by the GNN scorer model, policy friction rules will trigger adaptive barriers, and an LLM chain will generate an explainable audit rationale.
        </p>
      </div>

      {/* Persona Cards Horizontal Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {DEMO_PERSONAS.map((persona) => (
          <PersonaCard
            key={persona.id}
            persona={persona}
            onRun={() => runSimulation(persona)}
            isLoading={isLoading && selectedPersona?.id === persona.id}
            isActive={selectedPersona?.id === persona.id}
          />
        ))}
      </div>

      {/* Results Terminal Block */}
      {selectedPersona && (
        <div className="rounded-lg border border-soc-border bg-soc-surface p-6 shadow-2xl relative overflow-hidden">
          {/* Header Title */}
          <div className="flex items-center justify-between border-b border-soc-border pb-4 mb-6">
            <h3 className="font-display text-sm font-bold uppercase tracking-wider text-soc-cyan flex items-center gap-2">
              <Terminal className="h-4 w-4" />
              Live Evaluation Stream: {selectedPersona.name}
            </h3>
            <span className="font-mono text-[9px] text-soc-textSecondary uppercase">
              Target ID: {selectedPersona.entityId}
            </span>
          </div>

          {/* Loader or Error or Results */}
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <span className="h-8 w-8 animate-spin rounded-full border-2 border-soc-cyan border-t-transparent"></span>
              <span className="font-mono text-xs uppercase tracking-widest text-soc-cyan animate-pulse">
                Evaluating fraud vectors via OpenRouter AI Fallbacks...
              </span>
            </div>
          ) : error ? (
            <div className="flex items-center gap-3 rounded border border-soc-red/20 bg-soc-red/5 p-4 text-soc-red">
              <ShieldAlert className="h-5 w-5 flex-shrink-0" />
              <div className="text-xs font-semibold">{error}</div>
            </div>
          ) : result ? (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              
              {/* Left Column: Risk circle & Action badge (30%) */}
              <div className="lg:col-span-3 flex flex-col items-center justify-center p-4 border border-soc-border/40 rounded-lg bg-soc-bg/40 text-center">
                <RiskScoreRing score={result.risk_score} size={110} strokeWidth={8} />
                
                <div className="mt-4 mb-2">
                  <span className="text-[10px] text-soc-textSecondary font-bold uppercase block mb-1">Risk Score</span>
                  <span className="font-mono text-2xl font-bold text-soc-textPrimary">{result.risk_score.toFixed(1)}%</span>
                </div>

                <div className="w-full border-t border-soc-border/40 my-3" />

                <span className={`inline-block w-full rounded border px-3 py-1.5 font-bold text-xs uppercase tracking-widest ${
                  getActionStyles(result.action.action)
                }`}>
                  {result.action.action.replace(/_/g, " ")}
                </span>
              </div>

              {/* Right Column: AI Explanation & Provider Stats (90%) */}
              <div className="lg:col-span-9 flex flex-col gap-6">
                {/* Typewriter Explanation */}
                <div className="rounded border-l-4 border-soc-cyan bg-soc-bg p-5">
                  <h4 className="font-display text-[10px] font-bold uppercase tracking-wider text-soc-cyan mb-2">
                    AI Explainability Insight
                  </h4>
                  <TypewriterText text={result.explanation} speed={12} />
                </div>

                {/* Additional Metadata */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-semibold">
                  <div className="rounded border border-soc-border p-3">
                    <span className="text-soc-textSecondary block uppercase text-[9px] mb-1 font-bold">Model Explanation API</span>
                    <span className="text-soc-cyan uppercase flex items-center gap-1">
                      <Cpu className="h-3.5 w-3.5 text-soc-cyan" />
                      {result.provider_used} {result.fallback_used ? " (Fallback)" : ""}
                    </span>
                  </div>

                  <div className="rounded border border-soc-border p-3">
                    <span className="text-soc-textSecondary block uppercase text-[9px] mb-1 font-bold">Model Version ID</span>
                    <span className="font-mono text-soc-textPrimary text-[10px] break-all">{result.model_id}</span>
                  </div>

                  <div className="rounded border border-soc-border p-3">
                    <span className="text-soc-textSecondary block uppercase text-[9px] mb-1 font-bold">Friction Block Rationale</span>
                    <span className="text-soc-textPrimary uppercase">{result.action.message || "Silent pass approved"}</span>
                  </div>
                </div>

                {/* Link to Case File */}
                <div className="flex justify-end mt-4">
                  <Link
                    href={`/cases/${result.entity_id}`}
                    className="flex items-center gap-2 rounded border border-soc-cyan bg-soc-cyan/15 hover:bg-soc-cyan hover:text-soc-bg px-4 py-2 text-xs font-bold uppercase tracking-wider text-soc-cyan transition-all"
                  >
                    View Forensic Case File
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            </div>
          ) : null}

          {/* Decorative accent lights */}
          <div className="absolute right-0 bottom-0 top-0 w-[4px] bg-soc-cyan" />
        </div>
      )}
    </div>
  );
}
