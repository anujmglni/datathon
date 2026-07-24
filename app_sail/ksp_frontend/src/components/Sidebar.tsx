"use client";

import { useState, useEffect } from "react";
import { Plus, MessageSquare, Sparkles, Shield, Trash2, PanelLeftClose, PanelLeft } from "lucide-react";

interface SidebarProps {
  chatHistory: { id: string; query: string; timestamp: string }[];
  onSelectQuery: (query: string, id?: string) => void;
  onNewChat: () => void;
}

export default function Sidebar({ chatHistory, onSelectQuery, onNewChat }: SidebarProps) {
  const [collapsed, setCollapsed] = useState<boolean>(false);

  useEffect(() => {
    const saved = localStorage.getItem("ksp_sidebar_collapsed");
    if (saved === "true") setCollapsed(true);
  }, []);

  const toggleCollapse = () => {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem("ksp_sidebar_collapsed", String(next));
      return next;
    });
  };

  const suggestions = [
    "Show total theft cases in Bengaluru in 2022",
    "Find criminal network of accused ID 11",
    "Search case narratives for rash driving incident",
    "Investment fraud transactions and money trails",
    "Crime trends in Mysuru district",
    "Murder and homicide cases across Karnataka",
  ];

  // Cap displayed history to at most the last 6 entries (most recent first)
  const visibleHistory = chatHistory.slice(-6).reverse();

  return (
    <aside
      className={`bg-white border-r border-slate-200 flex flex-col justify-between hidden md:flex shrink-0 shadow-xs transition-all duration-300 ease-in-out ${
        collapsed ? "w-16 p-2.5" : "w-64 p-4"
      }`}
    >
      <div className="space-y-4">
        {/* KSP Badge Header with Logo Collapse Toggle */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <button
            onClick={toggleCollapse}
            className="flex items-center gap-2.5 text-left rounded-xl p-1 hover:bg-slate-100 transition cursor-pointer group"
            title={collapsed ? "Expand Sidebar (Persisted)" : "Collapse Sidebar (Persisted)"}
          >
            <div className="w-8 h-8 rounded-lg bg-white border border-slate-200 p-0.5 flex items-center justify-center shrink-0 shadow-xs group-hover:border-blue-400 transition">
              <img src="/ksp_logo.png" alt="KSP Crest Logo" className="w-7 h-7 object-contain" />
            </div>
            {!collapsed && (
              <div className="overflow-hidden">
                <h2 className="font-bold text-xs text-slate-900 truncate">Karnataka Police</h2>
                <p className="text-[10px] text-slate-500 font-medium truncate">Crime Intelligence Unit</p>
              </div>
            )}
          </button>

          {!collapsed && (
            <button
              onClick={toggleCollapse}
              className="p-1 hover:bg-slate-100 text-slate-400 hover:text-slate-700 rounded-lg transition"
              title="Collapse Sidebar"
            >
              <PanelLeftClose className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* New Chat Button */}
        <button
          onClick={onNewChat}
          title="Start New Investigation Chat"
          className={`w-full flex items-center justify-center gap-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-xs py-2.5 rounded-xl transition cursor-pointer ${
            collapsed ? "px-0" : "px-3"
          }`}
        >
          <Plus className="w-4 h-4 shrink-0" />
          {!collapsed && <span>New Chat</span>}
        </button>

        {/* Chat History Section (Capped to 6 entries) */}
        <div className="space-y-2">
          {!collapsed && (
            <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-500 px-1">
              <span className="flex items-center gap-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-blue-600" /> Recent Queries
              </span>
              <span className="text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-600 font-mono">
                {visibleHistory.length}
              </span>
            </div>
          )}

          <div className="space-y-1 max-h-48 overflow-y-auto pr-0.5">
            {visibleHistory.length === 0 ? (
              !collapsed && <p className="text-[11px] text-slate-400 italic px-2 py-1">No active turns yet.</p>
            ) : (
              visibleHistory.map((item) => (
                <button
                  key={item.id}
                  onClick={() => onSelectQuery(item.query, item.id)}
                  title={item.query}
                  className={`w-full text-left text-xs text-slate-700 hover:text-blue-700 bg-slate-50 hover:bg-blue-50/70 border border-slate-200/80 p-2 rounded-lg transition truncate font-medium flex items-center gap-2 cursor-pointer ${
                    collapsed ? "justify-center" : ""
                  }`}
                >
                  <MessageSquare className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  {!collapsed && <span className="truncate">{item.query}</span>}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Quick Query Suggestions */}
        {!collapsed && (
          <div className="space-y-2 pt-2 border-t border-slate-100">
            <div className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500 px-1">
              <Sparkles className="w-3.5 h-3.5 text-amber-500" /> Quick Prompts
            </div>

            <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
              {suggestions.map((query) => (
                <button
                  key={query}
                  onClick={() => onSelectQuery(query)}
                  className="w-full text-left text-xs text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200/60 p-2 rounded-lg transition line-clamp-1 font-medium cursor-pointer"
                >
                  {query}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="space-y-2 pt-3 border-t border-slate-100">
        <button
          onClick={onNewChat}
          title="Reset Session Memory"
          className={`w-full flex items-center justify-center gap-2 text-xs font-medium text-rose-600 hover:text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 py-2 rounded-lg transition cursor-pointer ${
            collapsed ? "px-0" : "px-3"
          }`}
        >
          <Trash2 className="w-3.5 h-3.5 shrink-0" />
          {!collapsed && <span>Reset Session Memory</span>}
        </button>

        {!collapsed && (
          <div className="text-[10px] text-slate-400 text-center font-medium">
            Karnataka State Police • Official Platform
          </div>
        )}
      </div>
    </aside>
  );
}

