"use client";

import { Plus, MessageSquare, Sparkles, Shield, Trash2 } from "lucide-react";

interface SidebarProps {
  chatHistory: { id: string; query: string; timestamp: string }[];
  onSelectQuery: (query: string) => void;
  onNewChat: () => void;
}

export default function Sidebar({ chatHistory, onSelectQuery, onNewChat }: SidebarProps) {
  const suggestions = [
    "Show total theft cases in Bengaluru in 2022",
    "Find criminal network of accused ID 11",
    "Search case narratives for rash driving incident",
    "Investment fraud transactions and money trails",
    "Crime trends in Mysuru district",
    "Murder and homicide cases across Karnataka",
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 p-4 flex flex-col justify-between hidden md:flex shrink-0 shadow-xs">
      <div className="space-y-4">
        {/* KSP Badge Header */}
        <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
          <div className="w-8 h-8 rounded-lg bg-white border border-slate-200 p-0.5 flex items-center justify-center shrink-0 shadow-xs">
            <img src="/ksp_logo.png" alt="KSP Crest Logo" className="w-7 h-7 object-contain" />
          </div>
          <div>
            <h2 className="font-bold text-xs text-slate-900">Karnataka Police</h2>
            <p className="text-[10px] text-slate-500 font-medium">Crime Intelligence Unit</p>
          </div>
        </div>


        {/* ChatGPT style + New Chat button */}
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 shadow-xs py-2.5 px-3 rounded-xl transition"
        >
          <Plus className="w-4 h-4" /> New Chat
        </button>

        {/* Chat History Section */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-500 px-1">
            <span className="flex items-center gap-1.5">
              <MessageSquare className="w-3.5 h-3.5 text-blue-600" /> Recent Queries
            </span>
            <span className="text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-600 font-mono">
              {chatHistory.length}
            </span>
          </div>

          <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
            {chatHistory.length === 0 ? (
              <p className="text-[11px] text-slate-400 italic px-2 py-1">No active turns yet.</p>
            ) : (
              chatHistory.slice().reverse().map((item) => (
                <button
                  key={item.id}
                  onClick={() => onSelectQuery(item.query)}
                  className="w-full text-left text-xs text-slate-700 hover:text-blue-700 bg-slate-50 hover:bg-blue-50/70 border border-slate-200/80 p-2 rounded-lg transition truncate font-medium flex items-center gap-2"
                >
                  <MessageSquare className="w-3 h-3 text-slate-400 shrink-0" />
                  <span className="truncate">{item.query}</span>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Quick Query Suggestions */}
        <div className="space-y-2 pt-2 border-t border-slate-100">
          <div className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500 px-1">
            <Sparkles className="w-3.5 h-3.5 text-amber-500" /> Quick Prompts
          </div>

          <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
            {suggestions.map((query) => (
              <button
                key={query}
                onClick={() => onSelectQuery(query)}
                className="w-full text-left text-xs text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200/60 p-2 rounded-lg transition line-clamp-1 font-medium"
              >
                {query}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="space-y-2 pt-3 border-t border-slate-100">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 text-xs font-medium text-rose-600 hover:text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 py-2 rounded-lg transition"
        >
          <Trash2 className="w-3.5 h-3.5" /> Reset Session Memory
        </button>

        <div className="text-[10px] text-slate-400 text-center font-medium">
          Karnataka State Police • Official Platform
        </div>
      </div>
    </aside>
  );
}

