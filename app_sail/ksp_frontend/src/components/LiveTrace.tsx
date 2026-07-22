"use client";

import { useState, useEffect } from "react";
import { ShieldCheck, Brain, Database, Hash, Sparkles, CheckCircle2 } from "lucide-react";

const PIPELINE_STEPS = [
  { icon: ShieldCheck, label: "RBAC & Governance Check", detail: "Validating user role & masking restricted demographic columns…" },
  { icon: Brain, label: "Groq Zero-Shot NLU", detail: "Extracting intent, district, year, crime type & IPC sections via Llama 3.3 70B…" },
  { icon: Database, label: "PostgreSQL Targeted Filter", detail: "Compiling dynamic SQL (district ILIKE + crimeregistereddate LIKE)…" },
  { icon: Hash, label: "BM25Okapi Re-Ranking", detail: "Scoring & ranking candidate FIR BriefFacts narratives…" },
  { icon: Sparkles, label: "Groq Executive Synthesis", detail: "Generating grounded 2-paragraph crime intelligence briefing…" },
];

export default function LiveTrace({ query }: { query: string }) {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    setActiveStep(0);
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev < PIPELINE_STEPS.length - 1 ? prev + 1 : prev));
    }, 450);
    return () => clearInterval(interval);
  }, [query]);

  const progressPct = Math.round(((activeStep + 1) / PIPELINE_STEPS.length) * 100);

  return (
    <div className="glass-panel rounded-2xl border border-blue-500/20 p-5 shadow-2xl space-y-4 max-w-3xl mx-auto my-4 animate-fadeIn">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-ping" />
          <span className="text-xs font-bold uppercase tracking-wider text-blue-400">
            Intelligence Pipeline Execution
          </span>
        </div>
        <span className="text-xs font-mono font-bold text-slate-300 bg-blue-500/10 px-2.5 py-1 rounded-full border border-blue-500/20">
          {progressPct}%
        </span>
      </div>

      {/* Progress Line */}
      <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
        <div
          className="bg-gradient-to-r from-blue-500 to-emerald-400 h-full transition-all duration-300 ease-out"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Step items */}
      <div className="space-y-2 pt-1">
        {PIPELINE_STEPS.map((step, idx) => {
          const Icon = step.icon;
          const isDone = idx < activeStep;
          const isCurrent = idx === activeStep;

          return (
            <div
              key={step.label}
              className={`flex items-start gap-3 p-2.5 rounded-xl transition-all ${
                isCurrent
                  ? "bg-blue-950/40 border border-blue-500/30 text-slate-100"
                  : isDone
                  ? "text-slate-400 opacity-80"
                  : "text-slate-600 opacity-40"
              }`}
            >
              <div className="mt-0.5">
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Icon className={`w-4 h-4 ${isCurrent ? "text-blue-400 animate-pulse" : "text-slate-500"}`} />
                )}
              </div>
              <div className="flex-1 text-xs">
                <div className="font-semibold">{step.label}</div>
                {isCurrent && <div className="text-[11px] text-blue-300/80 mt-0.5">{step.detail}</div>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
