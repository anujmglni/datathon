"use client";

import { useState } from "react";
import { summarizeZiaOcr } from "@/lib/api";
import { ZiaOcrResponse } from "@/lib/types";
import { Camera, Sparkles, FileText, CheckCircle2 } from "lucide-react";

export default function ZiaOcrTab() {
  const [narrative, setNarrative] = useState(
    "FIR No. 104/2024 registered at Koramangala PS, Bengaluru City. On 14-03-2024 at around 21:30 hrs, complainant reported snatching of gold chain by two unidentified male accused riding a black motorcycle under Sec. 379 IPC r/w Sec. 356 IPC. Accused fled towards E-City Expressway."
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ZiaOcrResponse | null>(null);

  const handleAnalyze = async () => {
    if (!narrative.trim()) return;
    setLoading(true);
    try {
      const res = await summarizeZiaOcr(narrative);
      setResult(res);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Camera className="w-5 h-5 text-blue-600" />
            Zoho Catalyst Zia AI — OCR & FIR Document Digitization
          </h2>
          <p className="text-xs text-slate-500 mt-1 font-medium">
            Extract IPC sections, jurisdictions, and executive summaries from handwritten police complaint scans or FIR narrative statements.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Input Column */}
        <div className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-700 mb-1 block">Paste FIR Narrative / Complaint Statement</label>
            <textarea
              value={narrative}
              onChange={(e) => setNarrative(e.target.value)}
              rows={8}
              className="w-full bg-slate-50 border border-slate-200 text-slate-900 text-xs rounded-xl p-3 focus:outline-none focus:border-blue-600 font-mono leading-relaxed"
            />
          </div>

          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-xl text-xs transition shadow-xs disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            {loading ? "Processing with Zia AI Analytics…" : "⚡ Run Zia AI Analysis"}
          </button>
        </div>

        {/* Results Column */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
          <div className="text-xs font-bold uppercase text-slate-500 border-b border-slate-100 pb-3 flex items-center justify-between">
            <span>📝 Zia AI Text Analytics Output</span>
            <span className="text-[10px] text-blue-700 font-mono font-semibold">CONFIDENCE: {result?.zia_confidence_score ? `${result.zia_confidence_score * 100}%` : "—"}</span>
          </div>

          {result ? (
            <div className="space-y-4 text-xs">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                <div className="font-bold text-slate-900 mb-1 flex items-center gap-1.5 text-xs">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Executive Intelligence Summary
                </div>
                <p className="text-slate-700 leading-relaxed font-medium">{result.executive_summary}</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="font-bold text-slate-500 text-[10px] uppercase mb-1">IPC / Legal Provisions</div>
                  {result.extracted_entities?.ipc_sections?.length > 0 ? (
                    <div className="space-y-1">
                      {result.extracted_entities.ipc_sections.map((ipc, i) => (
                        <span key={i} className="inline-block px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-mono text-[11px] font-semibold border border-blue-200 mr-1">
                          {ipc}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-slate-400 font-medium">None detected</span>
                  )}
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="font-bold text-slate-500 text-[10px] uppercase mb-1">Identified Jurisdictions</div>
                  {result.extracted_entities?.jurisdictions?.length > 0 ? (
                    <div className="space-y-1">
                      {result.extracted_entities.jurisdictions.map((jur, i) => (
                        <span key={i} className="inline-block px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium text-[11px] border border-slate-200 mr-1">
                          📍 {jur}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-slate-400 font-medium">None detected</span>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-slate-400 text-xs py-12 flex flex-col items-center gap-2 font-medium">
              <FileText className="w-8 h-8 opacity-30 text-slate-500" />
              <span>Click "Run Zia AI Analysis" to extract entities & executive summary</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

