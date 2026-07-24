"use client";

import { useState } from "react";
import { generatePdfReport, exportDocxReport } from "@/lib/api";
import { FileText, Download, CheckCircle2, AlertCircle, FileDown } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function ReportCompilerTab() {
  const [title, setTitle] = useState("Bengaluru City Crime Analysis Briefing — 2024");
  const [content, setContent] = useState(`# Executive Crime Overview
District: Bengaluru City
Period: January 2024 — December 2024
Total Cases Analyzed: 1,247

## Key Investigation Findings
- Property theft cases concentrated in Koramangala, Whitefield, and Electronic City.
- 23% increase in cybercrime cases compared to 2023.
- Repeat offender rate: 12.4% (highest in Majestic sub-jurisdiction).

## Operational Recommendations
1. Increase night patrolling in Koramangala (8 PM — 2 AM).
2. Deploy cyber cell rapid-response unit for UPI fraud complaints.
3. Expand CCTV coverage in identified hotspot zones.

## Gang & Network Intelligence
- 4 organized groups identified through co-accused analysis.
- Primary hub suspect: Person #4821 (degree centrality: 0.847).
`);

  const [loading, setLoading] = useState(false);
  const [reportResult, setReportResult] = useState<{ success?: boolean; filename?: string; download_url?: string; size_bytes?: number; error?: string } | null>(null);

  const handleGeneratePdf = async () => {
    setLoading(true);
    setReportResult(null);
    try {
      const res = await generatePdfReport(title, content);
      setReportResult(res);
      if (res.download_url) {
        const link = document.createElement("a");
        link.href = `http://localhost:8080${res.download_url}`;
        link.download = res.filename || "ksp_report.pdf";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (e: any) {
      setReportResult({ error: e.message });
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDocx = async () => {
    setLoading(true);
    setReportResult(null);
    try {
      const res = await exportDocxReport(title, content);
      setReportResult(res);
      if (res.download_url) {
        const link = document.createElement("a");
        link.href = `http://localhost:8080${res.download_url}`;
        link.download = res.filename || "ksp_report.docx";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (e: any) {
      setReportResult({ error: e.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto pr-1 min-h-0 space-y-6 animate-fadeIn">
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            Official Report Compiler (PDF & Word DOCX)
          </h2>
          <p className="text-xs text-slate-500 mt-1 font-medium">
            Compile professional PDF briefings with ReportLab or editable Word documents with python-docx.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Editor Side */}
        <div className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-700 mb-1 block">Report Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 text-slate-900 text-xs rounded-xl p-3 focus:outline-none focus:border-blue-600 font-semibold"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 mb-1 block">Report Content (Markdown)</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={14}
              className="w-full bg-slate-50 border border-slate-200 text-slate-900 text-xs font-mono rounded-xl p-3 focus:outline-none focus:border-blue-600 leading-relaxed"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={handleGeneratePdf}
              disabled={loading}
              className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 px-4 rounded-xl text-xs transition shadow-xs disabled:opacity-50"
            >
              <FileText className="w-4 h-4" />
              {loading ? "Compiling PDF…" : "Download PDF"}
            </button>
            <button
              onClick={handleGenerateDocx}
              disabled={loading}
              className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-900 text-white font-bold py-2.5 px-4 rounded-xl text-xs transition shadow-xs disabled:opacity-50"
            >
              <FileDown className="w-4 h-4" />
              {loading ? "Compiling DOCX…" : "Download DOCX"}
            </button>
          </div>

          {reportResult && (
            <div className={`p-3.5 rounded-xl text-xs flex items-center gap-3 border ${reportResult.error ? "bg-rose-50 border-rose-200 text-rose-800" : "bg-emerald-50 border-emerald-200 text-emerald-800"}`}>
              {reportResult.error ? <AlertCircle className="w-5 h-5 text-rose-600" /> : <CheckCircle2 className="w-5 h-5 text-emerald-600" />}
              <div className="font-medium">
                {reportResult.error ? (
                  <div>Failed to generate report: {reportResult.error}</div>
                ) : (
                  <div>
                    <span className="font-bold">Generated Report:</span> {reportResult.filename} ({reportResult.size_bytes} bytes)
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Live Preview Side */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col">
          <div className="text-xs font-bold uppercase text-slate-500 border-b border-slate-100 pb-3 mb-4 flex items-center justify-between">
            <span>Live Executive Preview</span>
            <span className="text-[10px] text-blue-700 font-mono font-semibold">REPORTLAB & DOCX</span>
          </div>

          <div className="prose prose-sm max-w-none text-slate-800 flex-1 overflow-y-auto pr-2 break-words-all">
            <h1 className="text-xl font-bold text-blue-700 border-b border-slate-200 pb-2">{title}</h1>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}

