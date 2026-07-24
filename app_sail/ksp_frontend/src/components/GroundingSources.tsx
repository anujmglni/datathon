"use client";

import { useState } from "react";
import { Table, Code2, ChevronDown, ChevronUp } from "lucide-react";
import { DatabaseRecord } from "@/lib/types";

interface GroundingSourcesProps {
  records: DatabaseRecord[];
  sqlExecuted?: string;
}

export default function GroundingSources({ records, sqlExecuted }: GroundingSourcesProps) {
  const [showTable, setShowTable] = useState(false);
  const [showSql, setShowSql] = useState(false);

  if (!records || records.length === 0) return null;

  return (
    <div className="space-y-2 mt-4 pt-3 border-t border-slate-800 text-xs">
      {/* Expander buttons */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setShowTable(!showTable)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition"
        >
          <Table className="w-3.5 h-3.5 text-blue-400" />
          <span>Grounding Sources ({records.length} database records)</span>
          {showTable ? <ChevronUp className="w-3.5 h-3.5 ml-1" /> : <ChevronDown className="w-3.5 h-3.5 ml-1" />}
        </button>

        {sqlExecuted && (
          <button
            onClick={() => setShowSql(!showSql)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition"
          >
            <Code2 className="w-3.5 h-3.5 text-amber-400" />
            <span>Executed SQL Provenance</span>
            {showSql ? <ChevronUp className="w-3.5 h-3.5 ml-1" /> : <ChevronDown className="w-3.5 h-3.5 ml-1" />}
          </button>
        )}
      </div>

      {/* SQL View */}
      {showSql && sqlExecuted && (
        <div className="glass-card p-3 rounded-xl border border-amber-500/20 bg-slate-950 font-mono text-[11px] text-amber-300 overflow-x-auto">
          <div className="text-[10px] uppercase font-bold text-amber-400/70 mb-1">Targeted PostgreSQL Query</div>
          <code>{sqlExecuted}</code>
        </div>
      )}

      {/* Table View */}
      {showTable && (
        <div className="glass-card rounded-xl border border-slate-800 overflow-x-auto">
          <table className="w-full text-left text-slate-300">
            <thead className="bg-slate-900/90 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="p-2.5">Case No</th>
                <th className="p-2.5">Date</th>
                <th className="p-2.5">District</th>
                <th className="p-2.5">Crime Group</th>
                <th className="p-2.5">Brief Facts</th>
                <th className="p-2.5">BM25</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {records.map((r, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40">
                  <td className="p-2.5 font-mono text-blue-300">{String(r.CrimeNo || r.caseno || idx + 1)}</td>
                  <td className="p-2.5 whitespace-nowrap">{String(r.CrimeRegisteredDate || r.crimeregistereddate || "N/A")}</td>
                  <td className="p-2.5 whitespace-nowrap font-medium">{String(r.DistrictName || r.districtname || "N/A")}</td>
                  <td className="p-2.5 whitespace-nowrap text-slate-400">{String(r.CrimeGroupName || r.crimegroupname || "N/A")}</td>
                  <td className="p-2.5 max-w-md truncate text-slate-300">{String(r.BriefFacts || r.brieffacts || "")}</td>
                  <td className="p-2.5 font-mono text-emerald-400">{r._bm25_score ? String(r._bm25_score) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
