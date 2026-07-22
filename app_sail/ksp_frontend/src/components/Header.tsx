"use client";

import { Shield, Activity, UserCheck } from "lucide-react";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  userRole: string;
  setUserRole: (role: string) => void;
  isBackendHealthy: boolean;
}

export default function Header({
  activeTab,
  setActiveTab,
  userRole,
  setUserRole,
  isBackendHealthy,
}: HeaderProps) {
  const tabs = [
    { id: "chat", label: "💬 Chat Intelligence" },
    { id: "graph", label: "🕸️ Criminal Network Graph" },
    { id: "analytics", label: "📊 Crime & Trend Analytics" },
    { id: "pdf", label: "📄 PDF Reports" },
  ];


  return (
    <header className="sticky top-0 z-50 bg-white border-b border-slate-200 px-6 py-3 shadow-xs">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        
        {/* Brand KSP Logo & Title */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="p-1 bg-white rounded-xl shadow-xs border border-slate-200 flex items-center justify-center">
            <img src="/ksp_logo.png" alt="Karnataka State Police Logo" className="w-9 h-9 object-contain" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-slate-900 flex items-center gap-2">
              Karnataka State Police
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-mono font-medium">
                Crime Intelligence Platform
              </span>
            </h1>
            <p className="text-xs text-slate-500 font-medium">Conversational Crime AI & Network Analytics</p>
          </div>
        </div>


        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 shrink-0">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                activeTab === tab.id
                  ? "bg-blue-600 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Health Status & RBAC Switcher */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
            <Activity className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-600 font-medium">Status:</span>
            {isBackendHealthy ? (
              <span className="flex items-center gap-1.5 text-emerald-700 font-semibold">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                ONLINE
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-rose-600 font-semibold">
                <span className="w-2 h-2 rounded-full bg-rose-500" />
                OFFLINE
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
            <UserCheck className="w-3.5 h-3.5 text-blue-600" />
            <span className="text-slate-600 font-medium">Role:</span>
            <select
              value={userRole}
              onChange={(e) => setUserRole(e.target.value)}
              className="bg-transparent text-slate-900 font-semibold focus:outline-none cursor-pointer"
            >
              <option value="Analyst" className="bg-white text-slate-900">Analyst</option>
              <option value="Inspector" className="bg-white text-slate-900">Inspector</option>
              <option value="SP" className="bg-white text-slate-900">SP</option>
              <option value="DGP" className="bg-white text-slate-900">DGP</option>
            </select>
          </div>
        </div>

      </div>
    </header>
  );
}

