'use client';
import { useState, useCallback } from 'react';
import { ATTACK_STEPS, AttackStep } from '../lib/attackSimulation';
import { api } from '../lib/api';
import { RiskEvent } from '../lib/types';
import RiskScoreRing from './RiskScoreRing';

type StepStatus = 'idle' | 'running' | 'done' | 'blocked';

interface StepResult {
  score: number;
  action: string;
  explanation: string;
  provider: string;
}

export default function AttackTimeline() {
  const [stepStatuses, setStepStatuses] = useState<Record<number, StepStatus>>(
    Object.fromEntries(ATTACK_STEPS.map(s => [s.id, 'idle']))
  );
  const [stepResults, setStepResults] = useState<Record<number, StepResult>>({});
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [simulationComplete, setSimulationComplete] = useState(false);

  const resetSimulation = () => {
    setStepStatuses(Object.fromEntries(ATTACK_STEPS.map(s => [s.id, 'idle'])));
    setStepResults({});
    setCurrentStep(0);
    setSimulationComplete(false);
    setIsRunning(false);
  };

  const runSimulation = useCallback(async () => {
    if (isRunning) return;
    resetSimulation();
    setIsRunning(true);

    for (const step of ATTACK_STEPS) {
      setCurrentStep(step.id);
      setStepStatuses(prev => ({ ...prev, [step.id]: 'running' }));

      try {
        const result = await api.scoreEvent(step.payload) as RiskEvent;
        const score = result.risk_score;
        const action = typeof result.action === 'object' ? (result.action as any).action : result.action;
        const explanation = result.explanation ?? '';
        const provider = result.provider_used ?? '';

        setStepResults(prev => ({
          ...prev,
          [step.id]: { score, action, explanation, provider }
        }));

        const status: StepStatus = action === 'HARD_BLOCK' ? 'blocked' : 'done';
        setStepStatuses(prev => ({ ...prev, [step.id]: status }));

        // If hard blocked, mark remaining steps as idle and stop
        if (action === 'HARD_BLOCK') {
          const remaining = ATTACK_STEPS.filter(s => s.id > step.id);
          setStepStatuses(prev => ({
            ...prev,
            ...Object.fromEntries(remaining.map(s => [s.id, 'idle']))
          }));
          break;
        }
      } catch (err) {
        console.error(`Step ${step.id} failed:`, err);
        setStepStatuses(prev => ({ ...prev, [step.id]: 'idle' }));
        break;
      }

      // 1.5 second delay between steps — the dramatic pause
      await new Promise(resolve => setTimeout(resolve, 1500));
    }

    setSimulationComplete(true);
    setIsRunning(false);
  }, [isRunning]);

  const getStepColor = (status: StepStatus) => {
    switch (status) {
      case 'running': return 'border-soc-cyan bg-soc-cyan/10 shadow-[0_0_12px_#00D4FF44]';
      case 'done':    return 'border-soc-green bg-soc-green/10';
      case 'blocked': return 'border-soc-red bg-soc-red/10 shadow-[0_0_12px_#FF3B5C44]';
      default:        return 'border-soc-border bg-soc-surface';
    }
  };

  const getStatusLabel = (status: StepStatus) => {
    switch (status) {
      case 'running': return <span className="text-soc-cyan text-xs font-mono animate-pulse">● PROCESSING...</span>;
      case 'done':    return <span className="text-soc-green text-xs font-mono">✓ PASSED</span>;
      case 'blocked': return <span className="text-soc-red text-xs font-mono animate-pulse">⛔ HARD BLOCK</span>;
      default:        return <span className="text-soc-textSecondary text-xs font-mono">○ WAITING</span>;
    }
  };

  return (
    <div className="w-full bg-soc-surface border border-soc-border rounded-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-soc-textPrimary font-bold text-lg">
            ⚡ Live Attack Simulation
          </h3>
          <p className="text-soc-textSecondary text-sm mt-0.5">
            Watch a SIM-swap fraud unfold step by step in real time
          </p>
        </div>
        <div className="flex gap-3">
          {simulationComplete && (
            <button
              onClick={resetSimulation}
              className="px-4 py-2 rounded-lg border border-soc-border text-soc-textSecondary
                         text-sm font-mono hover:border-soc-cyan hover:text-soc-cyan
                         transition-colors duration-200"
            >
              Reset
            </button>
          )}
          <button
            onClick={runSimulation}
            disabled={isRunning}
            className={`px-6 py-2 rounded-lg text-sm font-mono font-bold transition-all duration-200
              ${isRunning
                ? 'bg-soc-border text-soc-textSecondary cursor-not-allowed'
                : 'bg-soc-red text-white hover:bg-soc-red/80 shadow-[0_0_20px_#FF3B5C44]'
              }`}
          >
            {isRunning ? `Running Step ${currentStep}/5...` : '▶ Run Attack Simulation'}
          </button>
        </div>
      </div>

      {/* Connector line + Steps */}
      <div className="relative">
        {/* Vertical connector line */}
        <div className="absolute left-[27px] top-8 bottom-8 w-px bg-soc-border" />

        <div className="space-y-3">
          {ATTACK_STEPS.map((step, idx) => {
            const status = stepStatuses[step.id];
            const result = stepResults[step.id];

            return (
              <div key={step.id}
                   className={`relative flex gap-4 rounded-xl border p-4 transition-all duration-500
                               ${getStepColor(status)}`}>
                {/* Step circle */}
                <div className={`relative z-10 flex-shrink-0 w-14 h-14 rounded-full border-2 flex items-center
                                 justify-center text-2xl transition-all duration-300
                                 ${status === 'running' ? 'border-soc-cyan animate-pulse' :
                                   status === 'done' ? 'border-soc-green' :
                                   status === 'blocked' ? 'border-soc-red' :
                                   'border-soc-border'}`}>
                  {step.icon}
                </div>

                {/* Step content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-soc-textPrimary font-bold text-sm">
                        Step {step.id}: {step.label}
                      </span>
                      <p className="text-soc-textSecondary text-xs mt-0.5">{step.description}</p>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0 ml-4">
                      {getStatusLabel(status)}
                      {result && (
                        <div className="flex items-center gap-2">
                          <span className={`font-mono font-bold text-lg
                            ${result.score < 31 ? 'text-soc-green' :
                              result.score < 66 ? 'text-soc-amber' :
                              'text-soc-red'}`}>
                            {result.score.toFixed(0)}
                          </span>
                          <span className="text-soc-textSecondary font-mono text-xs">/100</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Explanation (appears after result) */}
                  {result?.explanation && (
                    <div className={`mt-2 text-xs p-2 rounded-lg border-l-2 font-mono
                      ${result.action === 'HARD_BLOCK'
                        ? 'border-soc-red bg-soc-red/5 text-soc-red'
                        : 'border-soc-cyan bg-soc-cyan/5 text-soc-textSecondary'}`}>
                      {result.explanation}
                    </div>
                  )}

                  {/* Provider badge */}
                  {result?.provider && (
                    <div className="mt-1 text-[10px] font-mono text-soc-textSecondary">
                      Explained by: {result.provider} ⚡
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Final verdict */}
      {simulationComplete && (
        <div className="mt-6 p-4 rounded-xl border border-soc-red bg-soc-red/10
                        text-center shadow-[0_0_30px_#FF3B5C22]">
          <div className="text-soc-red font-bold text-lg">⛔ TRANSACTION BLOCKED</div>
          <div className="text-soc-textPrimary text-sm mt-1">
            Setu detected a multi-signal SIM-swap fraud attack.
            Case auto-routed to Fraud Investigation Desk.
          </div>
          <div className="text-soc-textSecondary font-mono text-xs mt-1">
            Final Risk Score: {(Object.values(stepResults)[Object.values(stepResults).length - 1]?.score ?? 91).toFixed(0)}/100
          </div>
        </div>
      )}
    </div>
  );
}
