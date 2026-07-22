"use client";

import { useState, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import Header from "@/components/Header";
import Sidebar from "@/components/Sidebar";
import LiveTrace from "@/components/LiveTrace";
import GroundingSources from "@/components/GroundingSources";

const NetworkGraphTab = dynamic(() => import("@/components/NetworkGraphTab"), {
  ssr: false,
  loading: () => (
    <div className="py-20 text-center text-slate-500 font-medium flex items-center justify-center gap-2">
      <div className="w-4 h-4 rounded-full bg-blue-600 animate-ping" />
      Loading Criminal Network Engine…
    </div>
  ),
});

import ReportCompilerTab from "@/components/ReportCompilerTab";
import ZiaOcrTab from "@/components/ZiaOcrTab";

import { sendQuery, checkBackendHealth, generatePdfReport, exportDocxReport } from "@/lib/api";
import { ChatMessage } from "@/lib/types";
import { Send, Shield, Sparkles, Bot, User, FileText, Download, Check, FileDown } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>("chat");
  const [userRole, setUserRole] = useState<string>("Analyst");
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean>(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [downloadingFormat, setDownloadingFormat] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    checkBackendHealth().then(setIsBackendHealthy);
    const interval = setInterval(() => {
      checkBackendHealth().then(setIsBackendHealthy);
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (queryText?: string) => {
    const q = (queryText || inputQuery).trim();
    if (!q || loading) return;

    const userMsg: ChatMessage = {
      id: String(Date.now()),
      role: "user",
      content: q,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setLoading(true);

    try {
      const result = await sendQuery(q, "nextjs_ksp_session", userRole);
      const assistantMsg: ChatMessage = {
        id: String(Date.now() + 1),
        role: "assistant",
        content: result.answer || "No response generated.",
        result: result,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: String(Date.now() + 1),
          role: "assistant",
          content: `❌ Error querying backend: ${e.message}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = async (msgContent: string, format: "pdf" | "docx") => {
    const key = `${format}-${Date.now()}`;
    setDownloadingFormat(key);
    try {
      let res;
      if (format === "pdf") {
        res = await generatePdfReport("Karnataka Police Investigation Briefing", msgContent);
      } else {
        res = await exportDocxReport("Karnataka Police Investigation Briefing", msgContent);
      }

      if (res.download_url) {
        const link = document.createElement("a");
        link.href = `http://localhost:8080${res.download_url}`;
        link.download = res.filename || `ksp_report.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (err) {
      console.error("Export error:", err);
    } finally {
      setTimeout(() => setDownloadingFormat(null), 1500);
    }
  };

  const chatHistory = messages
    .filter((m) => m.role === "user")
    .map((m) => ({ id: m.id, query: m.content, timestamp: m.timestamp.toLocaleTimeString() }));

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 font-sans text-slate-900">
      {/* Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        userRole={userRole}
        setUserRole={setUserRole}
        isBackendHealthy={isBackendHealthy}
      />

      {/* Main Content Body */}
      <div className="flex-1 flex max-w-7xl w-full mx-auto p-4 gap-4 overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          chatHistory={chatHistory}
          onSelectQuery={(q) => {
            setActiveTab("chat");
            handleSend(q);
          }}
          onNewChat={() => setMessages([])}
        />

        {/* Tab Views */}
        <main className="flex-1 bg-white rounded-2xl border border-slate-200 shadow-xs p-6 overflow-y-auto flex flex-col justify-between">
          
          {/* TAB 1: CHAT INTELLIGENCE */}
          {activeTab === "chat" && (
            <div className="flex-1 flex flex-col justify-between space-y-4">
              
              {/* Chat Message List */}
              <div className="flex-1 space-y-4 overflow-y-auto pr-2">
                {messages.length === 0 ? (
                  <div className="text-center py-20 space-y-4 text-slate-500">
                    <div className="w-16 h-16 rounded-2xl bg-white border border-slate-200 flex items-center justify-center mx-auto shadow-xs p-2">
                      <img src="/ksp_logo.png" alt="KSP Logo" className="w-12 h-12 object-contain" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">Karnataka Police Crime Intelligence Platform</h3>
                      <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto font-medium">
                        Ask natural language questions about crimes, suspects, FIR case narratives, or criminal gang networks. Grounded strictly in official PostgreSQL database records.
                      </p>
                    </div>
                  </div>
                ) : (
                  messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex gap-3 text-xs leading-relaxed ${
                        msg.role === "user" ? "justify-end" : "justify-start"
                      }`}
                    >
                      {msg.role === "assistant" && (
                        <div className="w-8 h-8 rounded-xl bg-white border border-slate-200 flex items-center justify-center p-1 shrink-0 mt-1 shadow-xs">
                          <img src="/ksp_logo.png" alt="KSP Logo" className="w-6 h-6 object-contain" />
                        </div>
                      )}

                      <div
                        className={`max-w-2xl sm:max-w-3xl w-full break-words overflow-hidden break-all min-w-0 p-4.5 rounded-2xl ${
                          msg.role === "user"
                            ? "bg-blue-50/90 text-slate-900 border border-blue-200/90 rounded-br-none shadow-2xs font-medium"
                            : "bg-white text-slate-900 border border-slate-200/90 rounded-bl-none shadow-2xs"
                        }`}
                      >
                        <div className="prose prose-sm max-w-full text-slate-800 break-words-all leading-relaxed overflow-hidden">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                        </div>

                        {/* Direct PDF & DOCX Export Action Buttons */}
                        {msg.role === "assistant" && (
                          <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between gap-2 flex-wrap">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleDownloadReport(msg.content, "pdf")}
                                className="flex items-center gap-1.5 text-[11px] font-semibold text-blue-700 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 border border-blue-200 px-2.5 py-1 rounded-lg transition"
                              >
                                <FileText className="w-3.5 h-3.5" /> Download PDF (ReportLab)
                              </button>
                              <button
                                onClick={() => handleDownloadReport(msg.content, "docx")}
                                className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 border border-slate-300 px-2.5 py-1 rounded-lg transition"
                              >
                                <FileDown className="w-3.5 h-3.5" /> Download Word (DOCX)
                              </button>
                            </div>

                            {msg.result?.explainable_ai && (
                              <span className="text-[10px] text-slate-400 font-mono">
                                Latency: {msg.result.explainable_ai.execution_time_seconds.toFixed(3)}s
                              </span>
                            )}
                          </div>
                        )}

                        {/* Grounding Sources */}
                        {msg.result?.data && (
                          <GroundingSources
                            records={msg.result.data}
                            sqlExecuted={msg.result.explainable_ai?.sql_executed}
                          />
                        )}
                      </div>

                      {msg.role === "user" && (
                        <div className="w-8 h-8 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 shrink-0 mt-1 shadow-xs">
                          <User className="w-4 h-4" />
                        </div>
                      )}
                    </div>
                  ))
                )}


                {/* Animated NDAP-style Live Trace */}
                {loading && <LiveTrace query={inputQuery} />}

                <div ref={chatEndRef} />
              </div>

              {/* Input Form */}
              <div className="pt-2">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSend();
                  }}
                  className="bg-slate-50 p-2 rounded-2xl border border-slate-200 flex items-center gap-2 shadow-xs"
                >
                  <input
                    type="text"
                    value={inputQuery}
                    onChange={(e) => setInputQuery(e.target.value)}
                    placeholder="Ask about crimes, suspects, networks, or trends..."
                    className="flex-1 bg-transparent px-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none font-medium"
                  />
                  <button
                    type="submit"
                    disabled={loading || !inputQuery.trim()}
                    className="bg-blue-600 hover:bg-blue-700 text-white p-2.5 rounded-xl transition disabled:opacity-40 shadow-xs"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>

            </div>
          )}

          {/* TAB 2: CRIMINAL NETWORK GRAPH */}
          {activeTab === "graph" && <NetworkGraphTab />}

          {/* TAB 3: PDF REPORT COMPILER */}
          {activeTab === "pdf" && <ReportCompilerTab />}

          {/* TAB 4: ZIA AI OCR */}
          {activeTab === "ocr" && <ZiaOcrTab />}

        </main>
      </div>
    </div>
  );
}

