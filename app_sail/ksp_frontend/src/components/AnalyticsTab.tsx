"use client";

import { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import { fetchAnalyticsSummary, fetchNetworkOptions, generatePdfReport } from "@/lib/api";
import { AnalyticsResponsePayload } from "@/lib/types";
import { toPng } from "html-to-image";
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
  Image as ImageIcon
} from "lucide-react";

// Dynamically import NDAP Leaflet Map component on client side (ssr: false)
const KarnatakaLeafletMap = dynamic(() => import("@/components/KarnatakaLeafletMap"), {
  ssr: false,
  loading: () => (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-12 text-center text-slate-400 text-xs font-semibold flex items-center justify-center gap-2 col-span-full h-[460px]">
      <div className="w-4 h-4 rounded-full bg-blue-500 animate-ping" />
      Initializing NDAP Karnataka GIS Leaflet Engine…
    </div>
  ),
});

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

  // Download Chart Card visually as high-res PNG image
  const downloadChartImage = async (cardId: string, chartTitle: string) => {
    const cardElem = document.getElementById(cardId);
    if (!cardElem) return;

    try {
      const dataUrl = await toPng(cardElem, {
        cacheBust: true,
        backgroundColor: "#ffffff",
        quality: 0.95,
        pixelRatio: 2
      });
      const link = document.createElement("a");
      link.download = `ksp_${chartTitle.toLowerCase().replace(/[^a-z0-9]/g, "_")}.png`;
      link.href = dataUrl;
      link.click();
    } catch (err) {
      console.error("Failed to download chart image:", err);
    }
  };

  const [exportingPdf, setExportingPdf] = useState<boolean>(false);

  const captureCardPng = async (elemId: string): Promise<string> => {
    const elem = document.getElementById(elemId);
    if (!elem) return "";
    try {
      return await toPng(elem, {
        cacheBust: true,
        backgroundColor: "#ffffff",
        quality: 0.85,
        pixelRatio: 1.2,
        filter: (node) => {
          if (node instanceof HTMLElement) {
            if (node.tagName === "BUTTON" || node.getAttribute("role") === "button") return false;
            if (node.classList.contains("leaflet-control-container")) return false;
          }
          return true;
        }
      });
    } catch (e) {
      console.error(`Failed to capture ${elemId}:`, e);
      return "";
    }
  };

  // Dedicated Metric PDF Export for Individual Chart Cards
  const handleExportChartPdf = async (
    cardId: string,
    chartTitle: string,
    whatItDepicts: string,
    casesCompared: string,
    aiFindings: string
  ) => {
    try {
      const imgDataUrl = await captureCardPng(cardId);
      const markdown = [
        `# KARNATAKA STATE POLICE — ${chartTitle.toUpperCase()} REPORT`,
        `**Jurisdiction:** ${district.toUpperCase()} | **Category:** ${crimeType} | **Year:** ${selectedYear === "all" ? "All Years (2019-2025)" : selectedYear} | **Period:** Last ${dateRange} Days`,
        "---",
        "",
        `## VISUAL ANALYTICS CHART`,
        imgDataUrl ? `![${chartTitle}](${imgDataUrl})` : "",
        "",
        "## DETAILED METHODOLOGY & COMPARATIVE EXPLANATION",
        `- **What this Metric Depicts:** ${whatItDepicts}`,
        `- **Dataset & Cases Compared:** ${casesCompared}`,
        `- **Key AI Criminological Findings:** ${aiFindings}`,
        "",
        "---",
        "",
        "## STRATEGIC LAW ENFORCEMENT DIRECTIVE",
        `- **Operational Recommendation:** Deploy targeted station patrols under Sec 102 CrPC & CCTNS monitoring based on statistical variance shown in this metric.`,
        "",
        "---",
        "",
        "**ISSUING AUTHORITY:**",
        "Office of the Director General of Police, State Crime Records Bureau (SCRB), Bengaluru, Karnataka"
      ].join("\n");

      const res = await generatePdfReport(`KSP ${chartTitle} - ${district}`, markdown);
      if (res && res.download_url) {
        const link = document.createElement("a");
        link.href = res.download_url;
        link.target = "_blank";
        link.download = res.filename || `ksp_${chartTitle.toLowerCase().replace(/[^a-z0-9]/g, "_")}_report.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (err) {
      console.error(`Chart PDF export failed for ${cardId}:`, err);
    }
  };

  // Full Executive Analytics Dashboard PDF Report Export with Visual Charts (Excluding Map)
  const handleExportFullDashboard = async () => {
    if (!payload) return;
    setExportingPdf(true);
    try {
      const c1Png = await captureCardPng("chart-card-1");
      const c2Png = await captureCardPng("chart-card-2");
      const c3Png = await captureCardPng("chart-card-3");
      const c4Png = await captureCardPng("chart-card-4");
      const c6Png = await captureCardPng("chart-card-6");
      const c7Png = await captureCardPng("chart-card-7");
      const c8Png = await captureCardPng("chart-card-8");

      const markdown = [
        "# KARNATAKA STATE POLICE — EXECUTIVE CRIME ANALYTICS REPORT",
        `**Jurisdiction:** ${district.toUpperCase()} | **Category:** ${crimeType} | **Year:** ${selectedYear === "all" ? "All Years (2019-2025)" : selectedYear} | **Period:** Last ${dateRange} Days`,
        "---",
        "",
        "## DISTRICT × MONTH CRIME DENSITY HEATMAP",
        c1Png ? `![District x Month Heatmap](${c1Png})` : "",
        `- **What it Depicts:** Sequential heat intensity matrix mapping reported case density across 38 Karnataka districts over monthly intervals.`,
        `- **Cases Compared:** Comparing all registered FIRs matching jurisdiction '${district.toUpperCase()}' and category '${crimeType}' for year '${selectedYear === "all" ? "All Years" : selectedYear}'.`,
        `- **Key AI Findings:** ${payload.heatmap_district_month?.description || 'Density matrix active.'}`,
        "",
        "---",
        "",
        "## CRIME TYPE × TIME OF DAY TEMPORAL CLUSTERING",
        c2Png ? `![Crime Type x Time Window](${c2Png})` : "",
        `- **What it Depicts:** Temporal distribution of offense occurrence across 6-hour operational patrol windows (Morning, Afternoon, Evening, Night).`,
        `- **Cases Compared:** Analyzing incident timestamps across major crime heads within '${district.toUpperCase()}' jurisdiction for category '${crimeType}'.`,
        `- **Key AI Findings:** ${payload.heatmap_crime_timeofday?.description || 'Temporal distribution tracked.'}`,
        "",
        "---",
        "",
        "## MONTHLY CRIME TREND OVER TIME",
        c3Png ? `![Monthly Crime Trend Line Chart](${c3Png})` : "",
        `- **What it Depicts:** Longitudinal line chart tracking case registration progression and seasonality trends across monthly buckets.`,
        `- **Cases Compared:** Comparing monthly FIR volume trends across the selected timeline (${dateRange} days) for '${crimeType}' offenses.`,
        `- **Key AI Findings:** ${payload.line_crime_trends?.description || 'Progression timeline active.'}`,
        "",
        "---",
        "",
        "## TOP DISTRICTS BY VOLUME & STATUTORY SEVERITY GRAVITY",
        c4Png ? `![Top Districts Bar Chart](${c4Png})` : "",
        `- **What it Depicts:** Comparative ranking contrasting raw FIR case counts against statutory severity weighted by GravityOffence score.`,
        `- **Cases Compared:** Ranking top Karnataka districts by raw volume vs penal gravity weight under '${crimeType}' filters in ${selectedYear === "all" ? "All Years" : selectedYear}.`,
        `- **Key AI Findings:** ${payload.bar_top_offenses?.description || 'Gravity ranking indexed.'}`,
        "",
        "---",
        "",
        "## CASE DISPOSITION STATUS BREAKDOWN",
        c6Png ? `![Case Status Donut Chart](${c6Png})` : "",
        `- **What it Depicts:** Proportional donut distribution of cases across CCTNS investigation stages (Under Investigation, Charge Sheeted, Pending Trial, Closed).`,
        `- **Cases Compared:** Evaluating legal resolution breakdown for cases matching '${crimeType}' in '${district.toUpperCase()}' for year ${selectedYear === "all" ? "2019-2025" : selectedYear}.`,
        `- **Key AI Findings:** ${payload.donut_case_status?.description || 'Status disposition tracked.'}`,
        "",
        "---",
        "",
        "## FINANCIAL CRIME LOSS VS RECOVERY AUDIT",
        c7Png ? `![Financial Crime Bar Chart](${c7Png})` : "",
        `- **What it Depicts:** Dual-bar financial audit comparing total INR funds stolen versus funds frozen/recovered across cyber and economic fraud categories.`,
        `- **Cases Compared:** Auditing financial transaction records and Sec 102 CrPC lien orders across bank accounts matching '${crimeType}' offenses.`,
        `- **Key AI Findings:** ${payload.financial_crime_summary?.description || 'Recovery rate tracked.'}`,
        "",
        "---",
        "",
        "## SOCIOLOGICAL CORRELATION SCATTER PLOT",
        c8Png ? `![Sociological Correlation](${c8Png})` : "",
        `- **What it Depicts:** Bivariate scatter plot correlating district case volume against socio-demographic metrics (Literacy Rate & Urbanization %).`,
        `- **Cases Compared:** Cross-analyzing census socio-economic indicators against reported commercial and property offenses under active parameters.`,
        `- **Key AI Findings:** ${payload.sociological_correlation?.description || 'Demographic correlation active.'}`,
        "",
        "---",
        "",
        "**ISSUING AUTHORITY:**",
        "Office of the Director General of Police, State Crime Records Bureau (SCRB), Bengaluru, Karnataka"
      ].join("\n");

      const res = await generatePdfReport(`KSP Executive Analytics Briefing - ${district}`, markdown);
      if (res && res.download_url) {
        const link = document.createElement("a");
        link.href = res.download_url;
        link.target = "_blank";
        link.download = res.filename || `ksp_analytics_dashboard_${district}_${Date.now()}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (e) {
      console.error("Dashboard PDF export failed:", e);
    } finally {
      setExportingPdf(false);
    }
  };

  function roundVal(val: any, decimals: number = 1): number {
    const num = Number(val) || 0;
    return Number(num.toFixed(decimals));
  }

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

  // Map case nodes and inter-district links
  const mapNodes = payload?.choropleth_district_map?.data || [];
  const mapLinks = payload?.choropleth_district_map?.links || [];

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
              {["all", "2025", "2024", "2023", "2022", "2021", "2020", "2019"].map((yr) => (
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
          disabled={loading || !payload || exportingPdf}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-4 py-2 rounded-xl shadow-xs transition cursor-pointer disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
          {exportingPdf ? "Generating Visual PDF Report…" : "Export Dashboard PDF"}
        </button>
      </div>

      {/* LOADING SPINNER */}
      {loading && (
        <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 rounded-full border-4 border-blue-600 border-t-transparent animate-spin" />
          <p className="text-xs font-semibold text-slate-600">Aggregating Karnataka Datasets & Leaflet GIS Map Layers…</p>
        </div>
      )}

      {!loading && payload && (
        <div className="space-y-6">
          
          {/* SECTION 1: TOP 4 CHARTS (HEATMAPS, LINE TREND, BAR RANKING) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* CHART 1: HEATMAP - DISTRICT x MONTH */}
            <div id="chart-card-1" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-blue-600" />
                    <h3 className="font-bold text-sm text-slate-900">1. Crime Density (District × Month)</h3>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => downloadChartImage("chart-card-1", "District_Month_Heatmap")}
                      className="p-1.5 hover:bg-slate-100 text-slate-600 rounded-lg transition"
                      title="Download Chart Image (PNG)"
                    >
                      <ImageIcon className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleExportChartPdf(
                        "chart-card-1",
                        "District x Month Crime Density Heatmap",
                        "Sequential heat intensity matrix mapping reported case density across 38 Karnataka districts over monthly intervals.",
                        `Comparing all registered FIRs matching jurisdiction '${district.toUpperCase()}' and category '${crimeType.toUpperCase()}' for year '${selectedYear.toUpperCase()}'.`,
                        payload.heatmap_district_month?.description || "Density matrix active."
                      )}
                      className="flex items-center gap-1 bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-bold px-2.5 py-1 rounded-lg border border-blue-200 transition cursor-pointer"
                      title="Export Focused Metric PDF Report"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      Export PDF
                    </button>
                  </div>
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

              {/* Plain Language Summary Box */}
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
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => downloadChartImage("chart-card-2", "Crime_TimeOfDay_Heatmap")}
                      className="p-1.5 hover:bg-slate-100 text-slate-600 rounded-lg transition"
                      title="Download Chart Image (PNG)"
                    >
                      <ImageIcon className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleExportChartPdf(
                        "chart-card-2",
                        "Crime Type x Time of Day Temporal Clustering",
                        "Temporal distribution of offense occurrence across 6-hour operational patrol windows (Morning, Afternoon, Evening, Night).",
                        `Analyzing incident timestamps across major crime heads within '${district.toUpperCase()}' jurisdiction.`,
                        payload.heatmap_crime_timeofday?.description || "Temporal distribution tracked."
                      )}
                      className="flex items-center gap-1 bg-purple-50 text-purple-700 hover:bg-purple-100 text-xs font-bold px-2.5 py-1 rounded-lg border border-purple-200 transition cursor-pointer"
                      title="Export Focused Metric PDF Report"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      Export PDF
                    </button>
                  </div>
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

              {/* Plain Language Summary Box */}
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

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => downloadChartImage("chart-card-3", "Crime_Trend_LineChart")}
                      className="p-1.5 hover:bg-slate-100 text-slate-600 rounded-lg transition"
                      title="Download Chart Image (PNG)"
                    >
                      <ImageIcon className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleExportChartPdf(
                        "chart-card-3",
                        "Monthly Crime Trend Progression",
                        "Longitudinal line chart tracking case registration progression and seasonality trends across monthly buckets.",
                        `Comparing monthly FIR volume trends across the selected timeline (${dateRange} days).`,
                        payload.line_crime_trends?.description || "Progression timeline active."
                      )}
                      className="flex items-center gap-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 text-xs font-bold px-2.5 py-1 rounded-lg border border-emerald-200 transition cursor-pointer"
                      title="Export Focused Metric PDF Report"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      Export PDF
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
                      className="p-1.5 hover:bg-slate-100 text-slate-600 rounded-lg transition"
                      title="Download Chart Image (PNG)"
                    >
                      <ImageIcon className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleExportChartPdf(
                        "chart-card-4",
                        "Top Districts by Volume & Statutory Gravity",
                        "Comparative ranking contrasting raw FIR case counts against statutory severity weighted by GravityOffence score.",
                        `Ranking top 10 Karnataka districts by raw volume vs penal gravity weight under active filters.`,
                        payload.bar_top_offenses?.description || "Gravity ranking indexed."
                      )}
                      className="flex items-center gap-1 bg-amber-50 text-amber-700 hover:bg-amber-100 text-xs font-bold px-2.5 py-1 rounded-lg border border-amber-200 transition cursor-pointer"
                      title="Export Focused Metric PDF Report"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      Export PDF
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

          </div>

          {/* SECTION 2: CENTER OF THE ANALYTICS TAB PAGE — NDAP KARNATAKA LEAFLET GIS MAP STACK (IN THE MIDDLE) */}
          <KarnatakaLeafletMap
            nodes={mapNodes}
            individualCases={payload.choropleth_district_map?.individual_cases || []}
            links={mapLinks}
            localLinks={payload.choropleth_district_map?.local_case_links || []}
            description={payload.choropleth_district_map?.description}
            howToRead={payload.choropleth_district_map?.how_to_read}
          />


          {/* SECTION 3: BOTTOM 3 CHARTS (DONUT, FINANCIAL SUMMARY, SOCIOLOGICAL SCATTER) */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* CHART 6: DONUT CHART - CASE STATUS */}
            <div id="chart-card-6" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-indigo-600" />
                    <h3 className="font-bold text-xs text-slate-900">5. Case Disposition Status</h3>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => downloadChartImage("chart-card-6", "Case_Status_DonutChart")}
                      className="p-1.5 hover:bg-slate-100 text-slate-600 rounded-lg transition"
                      title="Download Chart Image (PNG)"
                    >
                      <ImageIcon className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleExportChartPdf(
                        "chart-card-6",
                        "Case Disposition Status Breakdown",
                        "Proportional donut distribution of cases across CCTNS investigation stages (Under Investigation, Charge Sheeted, Pending Trial, Closed).",
                        `Evaluating legal resolution breakdown for cases matching '${crimeType.toUpperCase()}' in '${district.toUpperCase()}'.`,
                        payload.donut_case_status?.description || "Status disposition tracked."
                      )}
                      className="flex items-center gap-1 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 text-xs font-bold px-2.5 py-1 rounded-lg border border-indigo-200 transition cursor-pointer"
                      title="Export Focused Metric PDF Report"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      Export PDF
                    </button>
                  </div>
                </div>

                <div className="h-56 mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={payload.donut_case_status?.data || []}
                        dataKey="case_count"
                        nameKey="status_name"
                        cx="50%"
                        cy="50%"
                        innerRadius={45}
                        outerRadius={75}
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
                      <Legend wrapperStyle={{ fontSize: "10px" }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Plain Language Summary Box */}
              <div className="bg-indigo-50/70 border-l-4 border-indigo-600 rounded-r-xl p-2.5 text-xs text-indigo-950">
                <p className="leading-relaxed font-medium">{payload.donut_case_status?.description}</p>
              </div>
            </div>

            {/* CHART 7: FINANCIAL CRIME SUMMARY */}
            <div id="chart-card-7" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-emerald-600" />
                    <h3 className="font-bold text-xs text-slate-900">6. Financial Crime Lost vs Recovered</h3>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => downloadChartImage("chart-card-7", "Financial_Crime_Summary")}
                      className="p-1.5 hover:bg-slate-100 text-slate-600 rounded-lg transition"
                      title="Download Chart Image (PNG)"
                    >
                      <ImageIcon className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleExportChartPdf(
                        "chart-card-7",
                        "Financial Crime Loss vs Recovery Audit",
                        "Dual-bar financial audit comparing total INR funds stolen versus funds frozen/recovered across cyber and economic fraud categories.",
                        `Auditing financial transaction records and Sec 102 CrPC lien orders across bank accounts matching active filters.`,
                        payload.financial_crime_summary?.description || "Recovery rate tracked."
                      )}
                      className="flex items-center gap-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 text-xs font-bold px-2.5 py-1 rounded-lg border border-emerald-200 transition cursor-pointer"
                      title="Export Focused Metric PDF Report"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      Export PDF
                    </button>
                  </div>
                </div>

                <div className="h-56 mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={payload.financial_crime_summary?.data || []}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="fraud_type" tick={{ fontSize: 9, fill: "#64748b" }} interval={0} angle={-15} textAnchor="end" />
                      <YAxis tick={{ fontSize: 9, fill: "#64748b" }} />
                      <Tooltip contentStyle={{ borderRadius: "8px", fontSize: "12px" }} formatter={(value: any) => `₹${Number(value).toLocaleString()}`} />
                      <Legend wrapperStyle={{ fontSize: "10px" }} />
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
              <div className="bg-emerald-50/70 border-l-4 border-emerald-600 rounded-r-xl p-2.5 text-xs text-emerald-950">
                <p className="leading-relaxed font-medium">{payload.financial_crime_summary?.description}</p>
              </div>
            </div>

            {/* CHART 8: SOCIOLOGICAL CORRELATION SCATTER PLOT */}
            <div id="chart-card-8" className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-blue-600" />
                    <h3 className="font-bold text-xs text-slate-900">7. Sociological Correlation</h3>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => downloadChartImage("chart-card-8", "Sociological_ScatterPlot")}
                      className="p-1.5 hover:bg-slate-100 text-slate-600 rounded-lg transition"
                      title="Download Chart Image (PNG)"
                    >
                      <ImageIcon className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleExportChartPdf(
                        "chart-card-8",
                        "Sociological Correlation Scatter Plot",
                        "Bivariate scatter plot correlating district case volume against socio-demographic metrics (Literacy Rate & Urbanization %).",
                        `Cross-analyzing census socio-economic indicators against reported commercial and property offenses under active filters.`,
                        payload.sociological_correlation?.description || "Demographic correlation active."
                      )}
                      className="flex items-center gap-1 bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-bold px-2.5 py-1 rounded-lg border border-blue-200 transition cursor-pointer"
                      title="Export Focused Metric PDF Report"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      Export PDF
                    </button>
                  </div>
                </div>

                <div className="h-56 mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis type="number" dataKey="urbanization_pct" name="Urbanization %" unit="%" tick={{ fontSize: 9 }} />
                      <YAxis type="number" dataKey="case_count" name="Case Count" tick={{ fontSize: 9 }} />
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
              <div className="bg-blue-50/70 border-l-4 border-blue-600 rounded-r-xl p-2.5 text-xs text-blue-950 space-y-1">
                <p className="leading-relaxed font-medium">{payload.sociological_correlation?.description}</p>
                <p className="text-[10px] text-blue-700 italic pt-0.5 border-t border-blue-100/60">
                  How to read: {payload.sociological_correlation?.how_to_read}
                </p>
              </div>
            </div>

          </div>

        </div>
      )}

    </div>
  );
}
