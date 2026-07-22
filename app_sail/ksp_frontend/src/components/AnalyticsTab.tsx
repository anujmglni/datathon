"use client";

import { useState, useEffect, useCallback } from "react";
import { fetchAnalyticsSummary, fetchNetworkOptions } from "@/lib/api";
import { AnalyticsResponsePayload } from "@/lib/types";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter
} from "recharts";
import {
  SlidersHorizontal,
  Download,
  Info,
  Calendar,
  TrendingUp,
  MapPin,
  ShieldCheck,
  Building2,
  DollarSign,
  Users,
  FileText,
  CheckCircle2
} from "lucide-react";

// Colorblind-Safe Palette
const CHART_COLORS = [
  "#2563eb", // Blue
  "#7c3aed", // Purple
  "#059669", // Emerald
  "#d97706", // Amber
  "#dc2626", // Red
  "#0891b2", // Cyan
  "#4f46e5", // Indigo
  "#be185d", // Pink
];

// Sequential Color Scale for Heatmap cells
function getHeatmapColor(value: number, max: number): string {
  if (!max || value === 0) return "#f1f5f9";
  const ratio = Math.min(value / max, 1);
  if (ratio < 0.2) return "#dbeafe";
  if (ratio < 0.4) return "#93c5fd";
  if (ratio < 0.6) return "#3b82f6";
  if (ratio < 0.8) return "#1d4ed8";
  return "#1e3a8a";
}

export default function AnalyticsTab() {
  // Global Filters State
  const [district, setDistrict] = useState<string>("all");
  const [crimeType, setCrimeType] = useState<string>("all");
  const [dateRange, setDateRange] = useState<string>("365");
  const [selectedYear, setSelectedYear] = useState<string>("all");

  // Options State
  const [districtsList, setDistrictsList] = useState<string[]>([]);
  const [crimeTypesList, setCrimeTypesList] = useState<string[]>([]);

  // Analytics Data & Loading State
  const [loading, setLoading] = useState<boolean>(true);
  const [payload, setPayload] = useState<AnalyticsResponsePayload | null>(null);

  // Map Hovered Node State
  const [hoveredNode, setHoveredNode] = useState<any | null>(null);

  // Bar Chart Toggle Mode ("count" vs "gravity")
  const [barMode, setBarMode] = useState<"count" | "gravity">("count");

  // Fetch Filter Options
  useEffect(() => {
    async function loadOptions() {
      const opts = await fetchNetworkOptions();
      setDistrictsList(opts.districts || []);
      setCrimeTypesList(opts.crime_types || []);
    }
    loadOptions();
  }, []);

  // Fetch Analytics Payload
  const loadAnalytics = useCallback(async () => {
    setLoading(true);
    const data = await fetchAnalyticsSummary(district, crimeType, dateRange, selectedYear);
    setPayload(data);
    setLoading(false);
  }, [district, crimeType, dateRange, selectedYear]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  // Download Chart SVG/Canvas Image directly as PNG
  const downloadChartImage = (cardId: string, chartTitle: string) => {
    const cardElem = document.getElementById(cardId);
    if (!cardElem) return;

    const svgElem = cardElem.querySelector("svg");
    if (svgElem) {
      try {
        const svgData = new XMLSerializer().serializeToString(svgElem);
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        const img = new Image();
        const svgBlob = new Blob([svgData], { type: "image/svg+xml;charset=utf-8" });
        const url = URL.createObjectURL(svgBlob);

        img.onload = () => {
          canvas.width = Math.max(img.width || 600, 600);
          canvas.height = Math.max(img.height || 350, 350);
          if (ctx) {
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          }
          const pngUrl = canvas.toDataURL("image/png");
          const a = document.createElement("a");
          a.href = pngUrl;
          a.download = `ksp_${chartTitle.toLowerCase().replace(/[^a-z0-9]/g, "_")}.png`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        };
        img.src = url;
        return;
      } catch (e) {
        console.error("SVG export failed fallback:", e);
      }
    }

    // Fallback: Simple text/HTML snapshot download
    const printWin = window.open("", "_blank");
    if (!printWin) return;
    printWin.document.write(`
      <html>
        <head><title>${chartTitle} Export</title></head>
        <body style="font-family:sans-serif; padding:30px;">
          <h2>Karnataka State Police — ${chartTitle}</h2>
          <p>Generated: ${new Date().toLocaleString()}</p>
          <div style="border:1px solid #ccc; padding:20px; border-radius:12px;">
            ${cardElem.innerHTML}
          </div>
          <script>window.onload = function() { window.print(); window.close(); }</script>
        </body>
      </html>
    `);
    printWin.document.close();
  };

  // Full Dashboard PDF Export
  const handleExportFullDashboard = () => {
    if (!payload) return;
    const printWin = window.open("", "_blank");
    if (!printWin) return;

    printWin.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Executive Crime Pattern & Sociological Analytics Report</title>
          <style>
            body { font-family: 'Helvetica Neue', Arial, sans-serif; padding: 30px; color: #0f172a; line-height: 1.4; }
            .header { border-bottom: 3px solid #1e3a8a; padding-bottom: 15px; margin-bottom: 20px; }
            .header h1 { margin: 0; font-size: 22px; color: #1e3a8a; }
            .header p { margin: 4px 0 0 0; font-size: 12px; color: #475569; }
            .filter-bar { background: #f1f5f9; padding: 10px 15px; border-radius: 8px; font-size: 12px; font-weight: bold; margin-bottom: 20px; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
            .card { border: 1px solid #cbd5e1; border-radius: 10px; padding: 15px; background: #ffffff; page-break-inside: avoid; }
            .card-title { font-size: 14px; font-weight: bold; color: #1e293b; margin-bottom: 8px; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px; }
            .summary-box { background: #eff6ff; border-left: 3px solid #2563eb; padding: 8px 10px; font-size: 11px; color: #1e40af; margin-top: 10px; border-radius: 0 6px 6px 0; }
            .footer { margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 10px; font-size: 10px; color: #94a3b8; text-align: center; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>Karnataka State Police — Crime Intelligence Analytics Dashboard</h1>
            <p>Executive Report | Generated: ${new Date().toLocaleString()}</p>
          </div>

          <div class="filter-bar">
            Active Parameters — Jurisdiction: ${district.toUpperCase()} | Crime Type: ${crimeType.toUpperCase()} | Year: ${selectedYear.toUpperCase()} | Range: Last ${dateRange} Days
          </div>

          <div class="grid">
            <div class="card">
              <div class="card-title">1. Heatmap — Crime Density (District × Month)</div>
              <div class="summary-box">${payload.heatmap_district_month?.description}</div>
            </div>

            <div class="card">
              <div class="card-title">2. Heatmap — Crime Type × Time of Day</div>
              <div class="summary-box">${payload.heatmap_crime_timeofday?.description}</div>
            </div>

            <div class="card">
              <div class="card-title">3. Line Chart — Crime Trend Over Time</div>
              <div class="summary-box">${payload.line_crime_trends?.description}</div>
            </div>

            <div class="card">
              <div class="card-title">4. Bar Chart — Top Offenses by Volume & Gravity</div>
              <div class="summary-box">${payload.bar_top_offenses?.description}</div>
            </div>

            <div class="card">
              <div class="card-title">5. Interactive Karnataka Map & Case Nodes</div>
              <div class="summary-box">${payload.choropleth_district_map?.description}</div>
            </div>

            <div class="card">
              <div class="card-title">6. Donut Chart — Case Status Breakdown</div>
              <div class="summary-box">${payload.donut_case_status?.description}</div>
            </div>

            <div class="card">
              <div class="card-title">7. Financial Crime Summary (Lost vs Recovered)</div>
              <div class="summary-box">${payload.financial_crime_summary?.description}</div>
            </div>

            <div class="card">
              <div class="card-title">8. Sociological Correlation Scatter Plot</div>
              <div class="summary-box">${payload.sociological_correlation?.description}</div>
            </div>
          </div>

          <div class="footer">
            Karnataka State Police — SCRB Intelligence Division | Confidential Law Enforcement Report
          </div>
          <script>
            window.onload = function() { window.print(); window.close(); }
          </script>
        </body>
      </html>
    `);
    printWin.document.close();
  };

  // Heatmap 1 Grid data
  const h1Data = payload?.heatmap_district_month?.data || [];
  const h1Months = Array.from(new Set(h1Data.map((d: any) => d.month_str))).sort().slice(-8);
  const h1Districts = Array.from(new Set(h1Data.map((d: any) => d.district))).slice(0, 8);
  const h1MaxVal = Math.max(...h1Data.map((d: any) => d.case_count), 1);

  // Heatmap 2 Grid data
  const h2Data = payload?.heatmap_crime_timeofday?.data || [];
  const h2Times = ["Morning (06:00-12:00)", "Afternoon (12:00-18:00)", "Evening (18:00-24:00)", "Night (00:00-06:00)"];
  const h2Crimes = Array.from(new Set(h2Data.map((d: any) => d.crime_type))).slice(0, 6);
  const h2MaxVal = Math.max(...h2Data.map((d: any) => d.case_count), 1);

  // Map case nodes
  const mapNodes = payload?.choropleth_district_map?.data || [];

  return (
    <div className="space-y-6 pb-12 animate-fadeIn">
      
      {/* GLOBAL CONTROLS & YEAR TOGGLE HEADER */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          
          <div className="flex items-center gap-1.5 font-bold text-xs text-slate-900 pr-2 border-r border-slate-200">
            <SlidersHorizontal className="w-4 h-4 text-blue-600" />
            <span>Global Filters</span>
          </div>

          {/* District Filter */}
          <div className="flex items-center gap-1.5 text-xs">
            <label className="font-semibold text-slate-700">District:</label>
            <select
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-900 font-medium text-xs focus:outline-none focus:border-blue-600 cursor-pointer"
            >
              <option value="all">All Districts</option>
              {districtsList.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          {/* Crime Category Filter */}
          <div className="flex items-center gap-1.5 text-xs">
            <label className="font-semibold text-slate-700">Category:</label>
            <select
              value={crimeType}
              onChange={(e) => setCrimeType(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-900 font-medium text-xs focus:outline-none focus:border-blue-600 cursor-pointer"
            >
              <option value="all">All Categories</option>
              {crimeTypesList.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Year-Wise Selector Toggle */}
          <div className="flex items-center gap-1.5 text-xs">
            <label className="font-semibold text-slate-700">Year:</label>
            <div className="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs font-semibold">
              {["all", "2026", "2025", "2024", "2023", "2022"].map((yr) => (
                <button
                  key={yr}
                  onClick={() => setSelectedYear(yr)}
                  className={`px-2 py-0.5 rounded-md transition ${selectedYear === yr ? "bg-blue-600 text-white shadow-2xs font-bold" : "text-slate-600 hover:text-slate-900"}`}
                >
                  {yr === "all" ? "All Years" : yr}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Export Full Dashboard Button */}
        <button
          onClick={handleExportFullDashboard}
          disabled={loading || !payload}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-4 py-2 rounded-xl shadow-xs transition cursor-pointer disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
          Export Dashboard PDF
        </button>
      </div>

      {/* LOADING SPINNER */}
      {loading && (
        <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 rounded-full border-4 border-blue-600 border-t-transparent animate-spin" />
          <p className="text-xs font-semibold text-slate-600">Aggregating Karnataka Crime Datasets & Case Nodes…</p>
        </div>
      )}

      {!loading && payload && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* CHART 1: HEATMAP - DISTRICT x MONTH */}
          <div id="chart-card-1" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-blue-600" />
                  <h3 className="font-bold text-sm text-slate-900">1. Crime Density (District × Month)</h3>
                </div>
                <button
                  onClick={() => downloadChartImage("chart-card-1", "District_Month_Heatmap")}
                  className="p-1.5 hover:bg-blue-50 text-blue-600 rounded-lg transition"
                  title="Download Chart Image (PNG)"
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>

              {/* Heatmap Grid */}
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-[11px] border-collapse">
                  <thead>
                    <tr>
                      <th className="p-1 text-left text-slate-500 font-semibold border-b">District</th>
                      {h1Months.map((m) => (
                        <th key={m} className="p-1 text-center text-slate-500 font-semibold border-b">
                          {m}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {h1Districts.map((dist) => (
                      <tr key={dist}>
                        <td className="p-1.5 font-medium text-slate-800 border-b truncate max-w-[110px]">{dist}</td>
                        {h1Months.map((m) => {
                          const item = h1Data.find((d: any) => d.district === dist && d.month_str === m);
                          const val = item ? item.case_count : 0;
                          return (
                            <td
                              key={m}
                              className="p-1.5 text-center font-bold text-slate-900 rounded transition"
                              style={{ backgroundColor: getHeatmapColor(val, h1MaxVal), color: val > h1MaxVal * 0.5 ? "#ffffff" : "#0f172a" }}
                              title={`${dist} - ${m}: ${val} cases`}
                            >
                              {val}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Plain Language Summary Box (No "Explainable AI" label) */}
            <div className="bg-blue-50/70 border-l-4 border-blue-600 rounded-r-xl p-3 text-xs text-blue-950 space-y-1">
              <p className="leading-relaxed font-medium">{payload.heatmap_district_month?.description}</p>
              <p className="text-[10px] text-blue-700 italic pt-1 border-t border-blue-100/60">
                How to read: {payload.heatmap_district_month?.how_to_read}
              </p>
            </div>
          </div>

          {/* CHART 2: HEATMAP - CRIME TYPE x TIME OF DAY */}
          <div id="chart-card-2" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-purple-600" />
                  <h3 className="font-bold text-sm text-slate-900">2. Crime Type × Time of Day</h3>
                </div>
                <button
                  onClick={() => downloadChartImage("chart-card-2", "Crime_TimeOfDay_Heatmap")}
                  className="p-1.5 hover:bg-purple-50 text-purple-600 rounded-lg transition"
                  title="Download Chart Image (PNG)"
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>

              {/* Heatmap Grid */}
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-[11px] border-collapse">
                  <thead>
                    <tr>
                      <th className="p-1 text-left text-slate-500 font-semibold border-b">Crime Type</th>
                      {h2Times.map((t) => (
                        <th key={t} className="p-1 text-center text-slate-500 font-semibold border-b">
                          {t.split(" ")[0]}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {h2Crimes.map((crime) => (
                      <tr key={crime}>
                        <td className="p-1.5 font-medium text-slate-800 border-b truncate max-w-[120px]">{crime}</td>
                        {h2Times.map((t) => {
                          const item = h2Data.find((d: any) => d.crime_type === crime && d.time_of_day === t);
                          const val = item ? item.case_count : 0;
                          return (
                            <td
                              key={t}
                              className="p-1.5 text-center font-bold text-slate-900 rounded transition"
                              style={{ backgroundColor: getHeatmapColor(val, h2MaxVal), color: val > h2MaxVal * 0.5 ? "#ffffff" : "#0f172a" }}
                              title={`${crime} - ${t}: ${val} cases`}
                            >
                              {val}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Plain Language Summary Box (No "Explainable AI" label) */}
            <div className="bg-purple-50/70 border-l-4 border-purple-600 rounded-r-xl p-3 text-xs text-purple-950 space-y-1">
              <p className="leading-relaxed font-medium">{payload.heatmap_crime_timeofday?.description}</p>
              <p className="text-[10px] text-purple-700 italic pt-1 border-t border-purple-100/60">
                How to read: {payload.heatmap_crime_timeofday?.how_to_read}
              </p>
            </div>
          </div>

          {/* CHART 3: LINE CHART - CRIME TREND OVER TIME (Animated + Year Toggle) */}
          <div id="chart-card-3" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-600" />
                  <h3 className="font-bold text-sm text-slate-900">3. Monthly Crime Trend Progression</h3>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => downloadChartImage("chart-card-3", "Crime_Trend_LineChart")}
                    className="p-1.5 hover:bg-emerald-50 text-emerald-600 rounded-lg transition"
                    title="Download Chart Image (PNG)"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="h-60 mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={payload.line_crime_trends?.data || []}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="month_str" tick={{ fontSize: 10, fill: "#64748b" }} />
                    <YAxis tick={{ fontSize: 10, fill: "#64748b" }} />
                    <Tooltip contentStyle={{ borderRadius: "8px", fontSize: "12px" }} />
                    <Line
                      type="monotone"
                      dataKey="total_cases"
                      stroke="#059669"
                      strokeWidth={2.5}
                      dot={{ r: 3.5, fill: "#059669" }}
                      activeDot={{ r: 6 }}
                      name="Total Registered Cases"
                      isAnimationActive={true}
                      animationDuration={1200}
                      animationEasing="ease-in-out"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Plain Language Summary Box */}
            <div className="bg-emerald-50/70 border-l-4 border-emerald-600 rounded-r-xl p-3 text-xs text-emerald-950 space-y-1">
              <p className="leading-relaxed font-medium">{payload.line_crime_trends?.description}</p>
            </div>
          </div>

          {/* CHART 4: BAR CHART - TOP DISTRICTS (Animated + Mode Toggle) */}
          <div id="chart-card-4" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-amber-600" />
                  <h3 className="font-bold text-sm text-slate-900">4. Top Districts by Volume & Gravity</h3>
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex items-center bg-slate-100 p-0.5 rounded-lg text-[10px] font-bold">
                    <button
                      onClick={() => setBarMode("count")}
                      className={`px-2 py-0.5 rounded-md transition ${barMode === "count" ? "bg-white text-slate-900 shadow-2xs" : "text-slate-500"}`}
                    >
                      By Count
                    </button>
                    <button
                      onClick={() => setBarMode("gravity")}
                      className={`px-2 py-0.5 rounded-md transition ${barMode === "gravity" ? "bg-white text-slate-900 shadow-2xs" : "text-slate-500"}`}
                    >
                      Gravity Score
                    </button>
                  </div>

                  <button
                    onClick={() => downloadChartImage("chart-card-4", "Top_Offenses_BarChart")}
                    className="p-1.5 hover:bg-amber-50 text-amber-600 rounded-lg transition"
                    title="Download Chart Image (PNG)"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="h-60 mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={payload.bar_top_offenses?.data || []}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="label" tick={{ fontSize: 9, fill: "#64748b" }} interval={0} angle={-15} textAnchor="end" />
                    <YAxis tick={{ fontSize: 10, fill: "#64748b" }} />
                    <Tooltip contentStyle={{ borderRadius: "8px", fontSize: "12px" }} />
                    {barMode === "count" ? (
                      <Bar
                        dataKey="case_count"
                        fill="#d97706"
                        radius={[4, 4, 0, 0]}
                        name="Raw Case Count"
                        isAnimationActive={true}
                        animationDuration={1200}
                        animationEasing="ease-in-out"
                      />
                    ) : (
                      <Bar
                        dataKey="gravity_score"
                        fill="#dc2626"
                        radius={[4, 4, 0, 0]}
                        name="Gravity Weighted Score"
                        isAnimationActive={true}
                        animationDuration={1200}
                        animationEasing="ease-in-out"
                      />
                    )}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Plain Language Summary Box */}
            <div className="bg-amber-50/70 border-l-4 border-amber-600 rounded-r-xl p-3 text-xs text-amber-950 space-y-1">
              <p className="leading-relaxed font-medium">{payload.bar_top_offenses?.description}</p>
            </div>
          </div>

          {/* CHART 5: INTERACTIVE KARNATAKA GEOGRAPHICAL MAP WITH CASE NODES & HOVER CARDS */}
          <div id="chart-card-5" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col justify-between space-y-4 relative overflow-visible">
            <div>
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-rose-600" />
                  <h3 className="font-bold text-sm text-slate-900">5. Interactive Karnataka Map & Case Nodes</h3>
                </div>
                <button
                  onClick={() => downloadChartImage("chart-card-5", "Karnataka_Case_Map")}
                  className="p-1.5 hover:bg-rose-50 text-rose-600 rounded-lg transition"
                  title="Download Map Canvas Image (PNG)"
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>

              {/* Interactive Map Surface Canvas */}
              <div className="mt-4 relative bg-slate-900 rounded-xl p-4 h-72 border border-slate-800 overflow-hidden flex items-center justify-center">
                
                {/* Background Map Grid Pattern */}
                <div className="absolute inset-0 bg-[radial-gradient(#3b82f6_1px,transparent_1px)] [background-size:16px_16px] opacity-20" />
                
                {/* Karnataka Territory Outline Overlay */}
                <div className="absolute inset-4 border border-blue-500/30 rounded-lg flex items-start p-2 pointer-events-none">
                  <span className="text-[10px] font-mono text-blue-400 font-bold uppercase tracking-wider">
                    Karnataka State Police Jurisdiction Map
                  </span>
                </div>

                {/* Case Nodes Pinned across Karnataka Lat/Lng Coordinates */}
                {mapNodes.map((node: any) => (
                  <div
                    key={node.district_name}
                    style={{ left: `${node.x}%`, top: `${node.y}%` }}
                    className="absolute -translate-x-1/2 -translate-y-1/2 z-20 group cursor-pointer"
                    onMouseEnter={() => setHoveredNode(node)}
                    onMouseLeave={() => setHoveredNode(null)}
                  >
                    {/* Pulsing Case Node Button */}
                    <div className="relative flex items-center justify-center">
                      <span className="animate-ping absolute inline-flex h-6 w-6 rounded-full bg-rose-400 opacity-75" />
                      <div className="relative inline-flex rounded-full h-5 w-5 bg-rose-600 border-2 border-white shadow-md text-[9px] font-bold text-white items-center justify-center">
                        {node.case_count}
                      </div>
                    </div>

                    {/* Node District Label */}
                    <span className="mt-1 block text-[9px] font-bold text-white bg-slate-900/90 px-1.5 py-0.5 rounded shadow whitespace-nowrap text-center">
                      {node.district_name}
                    </span>
                  </div>
                ))}

                {/* HOVER EXPANDED CASE DETAILS CARD */}
                {hoveredNode && (
                  <div className="absolute bottom-3 left-3 right-3 z-30 bg-white/95 backdrop-blur border-2 border-blue-600 rounded-xl p-3 shadow-xl animate-fadeIn space-y-1.5">
                    <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
                      <div className="flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5 text-rose-600" />
                        <h4 className="font-bold text-xs text-slate-900">{hoveredNode.district_name} Jurisdiction</h4>
                      </div>
                      <span className="bg-rose-100 text-rose-700 text-[10px] font-bold px-2 py-0.5 rounded-full">
                        {hoveredNode.case_count} Cases Registered
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[11px]">
                      <div>
                        <span className="text-slate-500 font-medium">Primary Station:</span>
                        <p className="font-bold text-slate-800 truncate">{hoveredNode.primary_station}</p>
                      </div>
                      <div>
                        <span className="text-slate-500 font-medium">Top Crime Category:</span>
                        <p className="font-bold text-blue-700 truncate">{hoveredNode.top_crime_type}</p>
                      </div>
                    </div>

                    <div className="pt-1 border-t border-slate-100 text-[10px] text-slate-600">
                      <span className="font-bold text-slate-700">Sample FIR Narrative: </span>
                      <span className="italic">"{hoveredNode.sample_facts}"</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Plain Language Summary Box */}
            <div className="bg-rose-50/70 border-l-4 border-rose-600 rounded-r-xl p-3 text-xs text-rose-950 space-y-1">
              <p className="leading-relaxed font-medium">{payload.choropleth_district_map?.description}</p>
              <p className="text-[10px] text-rose-700 italic pt-1 border-t border-rose-100/60">
                How to read: {payload.choropleth_district_map?.how_to_read}
              </p>
            </div>
          </div>

          {/* CHART 6: DONUT CHART - CASE STATUS (Animated) */}
          <div id="chart-card-6" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-indigo-600" />
                  <h3 className="font-bold text-sm text-slate-900">6. Case Disposition Status Breakdown</h3>
                </div>
                <button
                  onClick={() => downloadChartImage("chart-card-6", "Case_Status_DonutChart")}
                  className="p-1.5 hover:bg-indigo-50 text-indigo-600 rounded-lg transition"
                  title="Download Chart Image (PNG)"
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>

              <div className="h-60 mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={payload.donut_case_status?.data || []}
                      dataKey="case_count"
                      nameKey="status_name"
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={4}
                      isAnimationActive={true}
                      animationDuration={1200}
                      animationEasing="ease-in-out"
                    >
                      {(payload.donut_case_status?.data || []).map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: "8px", fontSize: "12px" }} />
                    <Legend wrapperStyle={{ fontSize: "11px" }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Plain Language Summary Box */}
            <div className="bg-indigo-50/70 border-l-4 border-indigo-600 rounded-r-xl p-3 text-xs text-indigo-950 space-y-1">
              <p className="leading-relaxed font-medium">{payload.donut_case_status?.description}</p>
            </div>
          </div>

          {/* CHART 7: FINANCIAL CRIME SUMMARY (Animated) */}
          <div id="chart-card-7" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-emerald-600" />
                  <h3 className="font-bold text-sm text-slate-900">7. Financial Crime (Lost vs Recovered INR)</h3>
                </div>
                <button
                  onClick={() => downloadChartImage("chart-card-7", "Financial_Crime_Summary")}
                  className="p-1.5 hover:bg-emerald-50 text-emerald-600 rounded-lg transition"
                  title="Download Chart Image (PNG)"
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>

              <div className="h-60 mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={payload.financial_crime_summary?.data || []}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="fraud_type" tick={{ fontSize: 9, fill: "#64748b" }} interval={0} angle={-15} textAnchor="end" />
                    <YAxis tick={{ fontSize: 10, fill: "#64748b" }} />
                    <Tooltip contentStyle={{ borderRadius: "8px", fontSize: "12px" }} formatter={(value: any) => `₹${Number(value).toLocaleString()}`} />
                    <Legend wrapperStyle={{ fontSize: "11px" }} />
                    <Bar
                      dataKey="total_lost_inr"
                      fill="#dc2626"
                      radius={[4, 4, 0, 0]}
                      name="Total Lost (INR)"
                      isAnimationActive={true}
                      animationDuration={1200}
                    />
                    <Bar
                      dataKey="total_recovered_inr"
                      fill="#059669"
                      radius={[4, 4, 0, 0]}
                      name="Total Recovered (INR)"
                      isAnimationActive={true}
                      animationDuration={1200}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Plain Language Summary Box */}
            <div className="bg-emerald-50/70 border-l-4 border-emerald-600 rounded-r-xl p-3 text-xs text-emerald-950 space-y-1">
              <p className="leading-relaxed font-medium">{payload.financial_crime_summary?.description}</p>
            </div>
          </div>

          {/* CHART 8: SOCIOLOGICAL CORRELATION SCATTER PLOT (Animated) */}
          <div id="chart-card-8" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-blue-600" />
                  <h3 className="font-bold text-sm text-slate-900">8. Sociological Correlation (Urbanization vs Crime)</h3>
                </div>
                <button
                  onClick={() => downloadChartImage("chart-card-8", "Sociological_ScatterPlot")}
                  className="p-1.5 hover:bg-blue-50 text-blue-600 rounded-lg transition"
                  title="Download Chart Image (PNG)"
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>

              <div className="h-60 mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis type="number" dataKey="urbanization_pct" name="Urbanization %" unit="%" tick={{ fontSize: 10 }} />
                    <YAxis type="number" dataKey="case_count" name="Case Count" tick={{ fontSize: 10 }} />
                    <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={{ borderRadius: "8px", fontSize: "12px" }} />
                    <Scatter
                      name="District Crime Density"
                      data={payload.sociological_correlation?.data || []}
                      fill="#2563eb"
                      isAnimationActive={true}
                      animationDuration={1200}
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Plain Language Summary Box */}
            <div className="bg-blue-50/70 border-l-4 border-blue-600 rounded-r-xl p-3 text-xs text-blue-950 space-y-1">
              <p className="leading-relaxed font-medium">{payload.sociological_correlation?.description}</p>
              <p className="text-[10px] text-blue-700 italic pt-1 border-t border-blue-100/60">
                How to read: {payload.sociological_correlation?.how_to_read}
              </p>
            </div>
          </div>

        </div>
      )}

    </div>
  );
}
