"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { fetchNetworkPayload, fetchNetworkOptions, fetchEntityProfile, generatePdfReport } from "@/lib/api";



import { GraphNode, GraphEdge, NetworkResponsePayload } from "@/lib/types";
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  SlidersHorizontal,
  Info,
  ExternalLink,
  ShieldAlert,
  Calendar,
  Layers,
  MapPin,
  FileText,
  CreditCard,
  User,
  Users,
  Search,
  Mic,
  MicOff,
  Download,
  Share2
} from "lucide-react";


function generatePersonalizedRecommendations(profileData: any): string[] {
  if (!profileData) return [];

  const recs: string[] = [];
  const cases: any[] = profileData.cases || [];
  
  const districts = Array.from(new Set(cases.map((c: any) => c.DistrictName || c.districtname).filter(Boolean)));
  const stations = Array.from(new Set(cases.map((c: any) => c.StationName || c.stationname).filter(Boolean)));
  const crimeGroups = Array.from(new Set(cases.map((c: any) => c.CrimeGroupName || c.crimegroupname).filter(Boolean)));
  const ios = Array.from(new Set(cases.map((c: any) => c.IOName || c.ioname).filter(Boolean)));

  const mainDist = (districts[0] as string) || profileData.attributes?.District || profileData.district || "Jurisdictional District";
  const mainStation = (stations[0] as string) || profileData.attributes?.Station || profileData.station || "Local Police Station";
  const mainIO = (ios[0] as string) || "Assigned Investigating Officer";
  const label = profileData.label || "Subject Entity";
  const entityType = profileData.entity_type || "accused";

  // 1. Recidivism & Threat Level Protocol
  if (profileData.risk_level?.includes("CRITICAL") || cases.length >= 3) {
    recs.push(
      `**History-Sheet & Security Bond (Sec 110 CrPC):** Open History Sheet (HS-B Register) under KPM Sec 1205 across ${districts.length ? districts.join(", ") : mainDist} jurisdiction. File habitual offender security bond proceedings before the Special Executive Magistrate.`
    );
  } else if (profileData.risk_level?.includes("HIGH")) {
    recs.push(
      `**Surveillance & Night Beat Patrol (KPM Sec 1201):** Deploy targeted night beat patrols in ${mainStation} jurisdiction to monitor habitual movements of ${label}.`
    );
  } else {
    recs.push(
      `**CCTNS Real-Time Alert & Tracking:** Flag ${label} in CCTNS database for automated alert triggers across all station checkposts in ${mainDist}.`
    );
  }

  // 2. Crime-Category Specific Operational Protocols
  const crimeText = (crimeGroups.join(" ") + " " + cases.map((c: any) => c.BriefFacts || c.brieffacts || "").join(" ")).toLowerCase();

  if (crimeText.includes("property") || crimeText.includes("theft") || crimeText.includes("burglary")) {
    recs.push(
      `**Stolen Property Receiver Inspection (Sec 411 IPC):** Direct ${mainIO} at ${mainStation} to conduct surprise search operations at local pawn shops and second-hand receivers in ${mainDist}. Requisition Fingerprint Bureau (FPB Madiwala) matching.`
    );
  }

  if (crimeText.includes("fraud") || crimeText.includes("financial") || crimeText.includes("cheating") || entityType === "financial") {
    recs.push(
      `**Bank Account Freeze & Lien Order (Sec 102 CrPC):** Issue immediate Sec 102 CrPC notices to destination bank branches to freeze funds linked to ${label}. File escalation on National Cyber Crime Reporting Portal (1930 NCRP).`
    );
    recs.push(
      `**Nodal Officer CDR & IP Log Requisition (Sec 91 CrPC):** Issue notices under Sec 91 CrPC to Telecom Nodal Officers for Call Detail Records (CDR) and IP login location logs.`
    );
  }

  if (crimeText.includes("document") || crimeText.includes("forgery")) {
    recs.push(
      `**Forensic Examination & Sub-Registrar Notice (Sec 91 CrPC):** Send questioned documents to State Forensic Science Laboratory (SFSL) Madiwala for ink/handwriting analysis. Issue Sec 91 CrPC notices to Sub-Registrar office in ${mainDist} to freeze encumbrance titles.`
    );
  }

  if (crimeText.includes("body") || crimeText.includes("murder") || crimeText.includes("assault")) {
    recs.push(
      `**Non-Bailable Warrant Execution & Witness Protection (Sec 70 CrPC / 195A IPC):** Issue and execute Non-Bailable Warrants (NBW) via Local Intelligence Unit (LIU) and implement witness protection protocols under Sec 195A IPC for victims in ${mainStation} cases.`
    );
  }

  if (entityType === "location") {
    recs.push(
      `**Hotspot Police Patrol & CCTV Expansion:** Increase Crime Prevention Party (CPP) frequency at ${label} and install high-definition ANPR (Automatic Number Plate Recognition) cameras at key arterial junctions.`
    );
  }

  if (districts.length > 1) {
    recs.push(
      `**Inter-District Joint Taskforce:** Form a dedicated joint investigation unit spanning ${districts.join(" & ")} districts under the direct supervision of Superintendent of Police (SP) / DCP ${districts[0]}.`
    );
  } else if (stations.length > 1) {
    recs.push(
      `**Inter-Station Crime Coordination:** Convene weekly crime coordination conference between Inspectors of ${stations.join(", ")} to cross-reference modus operandi.`
    );
  }

  if (recs.length < 3) {
    recs.push(
      `**Evidentiary Charge-Sheet Audit:** Conduct expedited case review under supervision of Sub-Divisional Police Officer (SDPO) to ensure timely filing of Charge Sheet before the Jurisdictional Magistrate.`
    );
  }

  return recs;
}

export default function NetworkGraphTab() {

  // --- Filter State ---
  const [district, setDistrict] = useState<string>("all");
  const [crimeType, setCrimeType] = useState<string>("all");
  const [dateRange, setDateRange] = useState<string>("90");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [minLinkStrength, setMinLinkStrength] = useState<number>(1);

  const [nodeTypes, setNodeTypes] = useState<Record<string, boolean>>({
    accused: true,
    victim: true,
    location: true,
    financial: true
  });

  // --- Options State ---
  const [districtsList, setDistrictsList] = useState<string[]>([]);
  const [crimeTypesList, setCrimeTypesList] = useState<string[]>([]);

  // --- Graph Data & Selection State ---
  const [loading, setLoading] = useState<boolean>(true);
  const [payload, setPayload] = useState<NetworkResponsePayload | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);

  // --- Offender / Entity Dossier Profile Modal State ---
  const [profileModalOpen, setProfileModalOpen] = useState<boolean>(false);
  const [profileLoading, setProfileLoading] = useState<boolean>(false);
  const [profileData, setProfileData] = useState<any>(null);
  const [pdfDownloading, setPdfDownloading] = useState<boolean>(false);



  // --- Search & Canvas Features ---
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isListening, setIsListening] = useState<boolean>(false);
  const [colorMode, setColorMode] = useState<"type" | "cluster">("type");

  // Cytoscape Container Ref & Instance
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<any>(null);

  const handleSearchNode = useCallback((query: string) => {
    setSearchQuery(query);
    if (!cyRef.current) return;
    const cy = cyRef.current;
    const q = query.trim().toLowerCase();
    
    if (!q) {
      cy.nodes().style({ opacity: 1 });
      cy.edges().style({ opacity: 0.6 });
      return;
    }

    const matched = cy.nodes().filter((node: any) => {
      const label = (node.data("label") || "").toLowerCase();
      const type = (node.data("type") || "").toLowerCase();
      const dist = (node.data("district") || "").toLowerCase();
      return label.includes(q) || type.includes(q) || dist.includes(q);
    });

    if (matched.length > 0) {
      cy.nodes().style({ opacity: 0.2 });
      cy.edges().style({ opacity: 0.1 });
      
      matched.style({ opacity: 1 });
      matched.neighborhood().style({ opacity: 0.8 });
      cy.animate({ fit: { eles: matched, padding: 50 }, duration: 500 });
    }
  }, []);

  const handleVoiceSearch = useCallback(() => {
    if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
      alert("Voice search is not supported in this browser. Please type your search query.");
      return;
    }
    try {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.lang = "en-IN";
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onerror = () => setIsListening(false);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        handleSearchNode(transcript);
      };

      recognition.start();
    } catch (e) {
      console.error("Speech recognition error:", e);
      setIsListening(false);
    }
  }, [handleSearchNode]);

  const handleDownloadImage = useCallback(() => {
    if (!cyRef.current) return;
    try {
      const pngData = cyRef.current.png({ full: true, scale: 2, bg: "#ffffff" });
      const link = document.createElement("a");
      link.href = pngData;
      link.download = `ksp_criminal_network_${Date.now()}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (e) {
      console.error("PNG export error:", e);
    }
  }, []);



  // Fetch Dropdown Filter Options on Mount
  useEffect(() => {
    fetchNetworkOptions()
      .then((res) => {
        if (res.districts) setDistrictsList(res.districts);
        if (res.crime_types) setCrimeTypesList(res.crime_types);
      })
      .catch((err) => console.error("Error fetching options:", err));
  }, []);

  // Fetch Graph Data from Backend with 300ms Debounce
  const loadGraphData = useCallback(async () => {
    setLoading(true);
    try {
      const activeTypes = Object.keys(nodeTypes).filter((k) => nodeTypes[k]);
      const data = await fetchNetworkPayload({
        district,
        crime_type: crimeType,
        date_range: dateRange,
        start_date: dateRange === "custom" ? startDate : undefined,
        end_date: dateRange === "custom" ? endDate : undefined,
        min_link_strength: minLinkStrength,
        node_types: activeTypes
      });
      setPayload(data);
    } catch (e) {
      console.error("Failed to load network graph:", e);
    } finally {
      setLoading(false);
    }
  }, [district, crimeType, dateRange, startDate, endDate, minLinkStrength, nodeTypes]);

  // Debounced load
  useEffect(() => {
    const timer = setTimeout(() => {
      loadGraphData();
    }, 300);
    return () => clearTimeout(timer);
  }, [loadGraphData]);

  // Render Cytoscape.js Force-Directed Graph Canvas
  useEffect(() => {
    if (!containerRef.current || !payload) return;

    let isMounted = true;

    // Convert API nodes & edges to Cytoscape elements format
    const cyElements: any[] = [];

    payload.nodes.forEach((n) => {
      cyElements.push({
        group: "nodes",
        data: {
          id: n.id,
          label: n.label,
          nodeType: n.type,
          color: n.color,
          rawNode: n
        }
      });
    });

    payload.edges.forEach((e) => {
      cyElements.push({
        group: "edges",
        data: {
          id: e.id,
          source: e.source,
          target: e.target,
          weight: e.weight,
          relation: e.relation,
          rawEdge: e
        }
      });
    });

    if (cyRef.current) {
      cyRef.current.destroy();
    }

    import("cytoscape").then((cytoscapeModule) => {
      if (!isMounted || !containerRef.current) return;
      const cytoscape = cytoscapeModule.default;

      const cy = cytoscape({
        container: containerRef.current,
        elements: cyElements,
        style: [
          {
            selector: "node",
            style: {
              "background-color": "data(color)",
              label: "data(label)",
              color: "#0f172a",
              "font-size": "11px",
              "font-weight": "bold",
              "text-valign": "bottom",

              "text-margin-y": 5,
              width: "36px",
              height: "36px",
              "border-width": "2px",
              "border-color": "#ffffff"
            }
          },

          {
            selector: "node[nodeType='accused']",
            style: {
              shape: "ellipse"
            }
          },
          {
            selector: "node[nodeType='victim']",
            style: {
              shape: "round-rectangle"
            }
          },
          {
            selector: "node[nodeType='location']",
            style: {
              shape: "hexagon"
            }
          },
          {
            selector: "node[nodeType='financial']",
            style: {
              shape: "diamond"
            }
          },
          {
            selector: "edge",
            style: {
              width: "mapData(weight, 1, 5, 1.5, 5)",
              "line-color": "#cbd5e1",
              "curve-style": "bezier",
              opacity: 0.75
            }
          },
          {
            selector: ".highlighted-node",
            style: {
              "border-width": "3px",
              "border-color": "#1d4ed8",
              opacity: 1
            }
          },

          {
            selector: ".dimmed",
            style: {
              opacity: 0.15
            }
          },
          {
            selector: "edge.highlighted-edge",
            style: {
              "line-color": "#2563eb",
              width: 4,
              opacity: 1
            }
          }
        ],
        layout: {
          name: "cose",
          animate: true,
          animationDuration: 400,
          refresh: 20,
          fit: true,
          padding: 30,
          componentSpacing: 40,
          nodeRepulsion: () => 8000,
          idealEdgeLength: () => 70,
          edgeElasticity: () => 100
        }
      });

      // --- Interaction Listeners ---

      // Node click -> Populate right detail panel & highlight Ego Network
      cy.on("tap", "node", (evt: any) => {
        const node = evt.target;
        const rawNode: GraphNode = node.data("rawNode");
        setSelectedNode(rawNode);
        setSelectedEdge(null);

        // Ego Network Highlighting Pattern
        cy.batch(() => {
          cy.elements().addClass("dimmed").removeClass("highlighted-node highlighted-edge");

          node.removeClass("dimmed").addClass("highlighted-node");

          const neighborhood = node.neighborhood();
          neighborhood.removeClass("dimmed");
          neighborhood.nodes().addClass("highlighted-node");
          neighborhood.edges().addClass("highlighted-edge");
        });
      });

      // Edge click -> Populate right detail panel with Explainable AI Evidence
      cy.on("tap", "edge", (evt: any) => {
        const edge = evt.target;
        const rawEdge: GraphEdge = edge.data("rawEdge");
        setSelectedEdge(rawEdge);
        setSelectedNode(null);

        cy.batch(() => {
          cy.elements().addClass("dimmed").removeClass("highlighted-node highlighted-edge");
          edge.removeClass("dimmed").addClass("highlighted-edge");
          edge.source().removeClass("dimmed").addClass("highlighted-node");
          edge.target().removeClass("dimmed").addClass("highlighted-node");
        });
      });

      // Tap background -> Reset selections & dimming
      cy.on("tap", (evt: any) => {
        if (evt.target === cy) {
          setSelectedNode(null);
          setSelectedEdge(null);
          cy.batch(() => {
            cy.elements().removeClass("dimmed highlighted-node highlighted-edge");
          });
        }
      });

      cyRef.current = cy;
    });

    return () => {
      isMounted = false;
    };
  }, [payload]);


  // Zoom controls
  const handleZoomIn = () => {
    if (cyRef.current) cyRef.current.zoom(cyRef.current.zoom() * 1.25);
  };
  const handleZoomOut = () => {
    if (cyRef.current) cyRef.current.zoom(cyRef.current.zoom() * 0.8);
  };
  const handleResetView = () => {
    if (cyRef.current) {
      cyRef.current.fit();
      cyRef.current.center();
    }
  };

  const handleNodeTypeToggle = (type: string) => {
    setNodeTypes((prev) => ({ ...prev, [type]: !prev[type] }));
  };

  return (
    <div className="h-[calc(100vh-140px)] flex flex-col space-y-3 animate-fadeIn">
      
      {/* 3-Column Layout Container */}
      <div className="flex-1 flex gap-3 overflow-hidden min-h-0">
        
        {/* COLUMN 1: LEFT FILTER PANEL (~180px Fixed Width) */}
        <aside className="w-[200px] shrink-0 bg-white border border-slate-200 rounded-2xl p-3.5 flex flex-col justify-between overflow-y-auto shadow-2xs space-y-4">
          <div className="space-y-4">
            
            {/* Header */}
            <div className="flex items-center gap-1.5 pb-2 border-b border-slate-100">
              <SlidersHorizontal className="w-4 h-4 text-blue-600" />
              <h2 className="font-bold text-xs text-slate-900">Network Filters</h2>
            </div>

            {/* 1. District Dropdown */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-700 block">District</label>
              <select
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 text-slate-900 text-xs rounded-lg p-2 focus:outline-none focus:border-blue-600 font-medium truncate"
              >
                <option value="all">All Districts</option>
                {districtsList.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>

            {/* 2. Crime Type Dropdown */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-700 block">Crime Category</label>
              <select
                value={crimeType}
                onChange={(e) => setCrimeType(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 text-slate-900 text-xs rounded-lg p-2 focus:outline-none focus:border-blue-600 font-medium truncate"
              >
                <option value="all">All Crime Types</option>
                {crimeTypesList.map((ct) => (
                  <option key={ct} value={ct}>
                    {ct}
                  </option>
                ))}
              </select>
            </div>

            {/* 3. Date Range Selector */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-slate-700 block flex items-center gap-1">
                <Calendar className="w-3 h-3 text-slate-500" /> Date Range
              </label>
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 text-slate-900 text-xs rounded-lg p-2 focus:outline-none focus:border-blue-600 font-medium"
              >
                <option value="30">Last 30 Days</option>
                <option value="90">Last 90 Days</option>
                <option value="365">Last 12 Months</option>
                <option value="all">All Time History</option>
                <option value="custom">Custom Range…</option>
              </select>

              {dateRange === "custom" && (
                <div className="space-y-1.5 pt-1">
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 text-[11px] text-slate-900 rounded p-1.5"
                  />
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 text-[11px] text-slate-900 rounded p-1.5"
                  />
                </div>
              )}
            </div>

            {/* 4. Min Link Strength Slider */}
            <div className="space-y-1 pt-1">
              <div className="flex justify-between items-center text-[11px]">
                <span className="font-semibold text-slate-700">Min. Strength</span>
                <span className="font-bold font-mono text-blue-700 bg-blue-50 px-1.5 rounded border border-blue-200">
                  {minLinkStrength}
                </span>
              </div>
              <input
                type="range"
                min={1}
                max={5}
                value={minLinkStrength}
                onChange={(e) => setMinLinkStrength(parseInt(e.target.value))}
                className="w-full cursor-pointer accent-blue-600"
              />
            </div>

            {/* 5. Semantic Node Type Checkboxes */}
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <label className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block">
                Entity Types
              </label>

              <div className="space-y-1.5 text-xs font-medium">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={nodeTypes.accused}
                    onChange={() => handleNodeTypeToggle("accused")}
                    className="rounded accent-rose-600"
                  />
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shrink-0" />
                  <span className="text-slate-800">Accused</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={nodeTypes.victim}
                    onChange={() => handleNodeTypeToggle("victim")}
                    className="rounded accent-blue-600"
                  />
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-500 shrink-0" />
                  <span className="text-slate-800">Victim</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={nodeTypes.location}
                    onChange={() => handleNodeTypeToggle("location")}
                    className="rounded accent-emerald-600"
                  />
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0" />
                  <span className="text-slate-800">Location</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={nodeTypes.financial}
                    onChange={() => handleNodeTypeToggle("financial")}
                    className="rounded accent-amber-600"
                  />
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0" />
                  <span className="text-slate-800">Financial</span>
                </label>
              </div>
            </div>
          </div>

          <div className="text-[10px] text-slate-400 text-center font-medium pt-2 border-t border-slate-100">
            Real-Time Graph Engine
          </div>
        </aside>

        {/* COLUMN 2: CENTER GRAPH CANVAS PANEL (Fills remaining width) */}
        <main className="flex-1 bg-white border border-slate-200 rounded-2xl relative flex flex-col justify-between overflow-hidden shadow-2xs">
          
          {/* Top Info Banners & Search Bar */}
          <div className="absolute top-3 left-3 right-3 z-10 flex items-center justify-between gap-2 pointer-events-none">
            
            {/* Real-time Node Search Bar with Voice Input */}
            <div className="pointer-events-auto flex items-center gap-1.5 bg-white/95 backdrop-blur border border-slate-200 px-2.5 py-1 rounded-xl shadow-md text-xs">
              <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <input
                type="text"
                placeholder="Search suspect, station or account…"
                value={searchQuery}
                onChange={(e) => handleSearchNode(e.target.value)}
                className="bg-transparent border-none outline-none text-xs text-slate-800 placeholder-slate-400 w-44 font-medium"
              />
              <button
                type="button"
                onClick={handleVoiceSearch}
                title="Voice Search (English & Kannada)"
                className={`p-1 rounded-lg transition ${isListening ? "bg-rose-500 text-white animate-pulse" : "hover:bg-slate-100 text-slate-600"}`}
              >
                {isListening ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
              </button>
            </div>

            {/* Server-Side Node Cap Warning Banner */}
            {payload?.capped && (
              <div className="pointer-events-auto bg-amber-500/90 backdrop-blur text-white text-xs font-semibold px-3 py-1.5 rounded-xl shadow-md flex items-center gap-1.5 border border-amber-400">
                <ShieldAlert className="w-4 h-4 shrink-0" />
                <span>Showing top 300 most-connected nodes — narrow filters to see all</span>
              </div>
            )}

            {!payload?.capped && <div />}

            {/* Live Counter Badge */}
            <div className="pointer-events-auto bg-slate-900/80 backdrop-blur text-white text-[11px] font-mono font-semibold px-3 py-1.5 rounded-xl shadow-md border border-slate-800">
              {payload ? `${payload.nodes_rendered} nodes · ${payload.total_edges} links` : "0 nodes"}
            </div>
          </div>

          {/* Cytoscape Graph Canvas Target */}
          <div className="flex-1 w-full h-full relative">
            
            {/* Loading Indicator */}
            {loading && (
              <div className="absolute inset-0 bg-white/70 backdrop-blur-xs z-20 flex items-center justify-center">
                <div className="flex items-center gap-2 text-xs font-semibold text-blue-700 bg-blue-50 border border-blue-200 px-4 py-2 rounded-xl shadow-md">
                  <div className="w-3 h-3 rounded-full bg-blue-600 animate-ping" />
                  Building Force-Directed Graph…
                </div>
              </div>
            )}

            {/* Empty State Banner */}
            {!loading && payload && payload.nodes.length === 0 && (
              <div className="absolute inset-0 z-10 flex flex-col items-center justify-center text-slate-400 p-6 text-center">
                <Layers className="w-12 h-12 stroke-[1.5] text-slate-300 mb-2" />
                <h4 className="text-sm font-bold text-slate-700">No linked entities in this range</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-sm">
                  Try widening date range, lowering min strength, or checking all entity types in the left filter panel.
                </p>
              </div>
            )}

            <div ref={containerRef} className="w-full h-full min-h-[450px]" />
          </div>

          {/* Bottom-Left Canvas View Controls */}
          <div className="absolute bottom-3 left-3 z-10 flex items-center gap-1.5 bg-white/95 backdrop-blur border border-slate-200 p-1 rounded-xl shadow-md">
            <button
              onClick={handleZoomIn}
              title="Zoom In"
              className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-700 transition cursor-pointer"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={handleZoomOut}
              title="Zoom Out"
              className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-700 transition cursor-pointer"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <div className="w-px h-4 bg-slate-200" />
            <button
              onClick={handleResetView}
              title="Reset View"
              className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-700 transition flex items-center gap-1 text-[11px] font-semibold px-2 cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Reset
            </button>
            <div className="w-px h-4 bg-slate-200" />
            <button
              onClick={handleDownloadImage}
              title="Download Canvas PNG"
              className="p-1.5 hover:bg-blue-50 text-blue-700 rounded-lg transition flex items-center gap-1 text-[11px] font-semibold px-2 cursor-pointer"
            >
              <Download className="w-3.5 h-3.5 text-blue-600" /> Export PNG
            </button>
          </div>

        </main>

        {/* COLUMN 3: RIGHT DETAIL & EXPLAINABLE AI EVIDENCE PANEL (~240px Fixed Width) */}
        <aside className="w-[240px] shrink-0 bg-white border border-slate-200 rounded-2xl p-4 flex flex-col justify-between overflow-y-auto shadow-2xs space-y-4">
          
          {selectedNode ? (
            /* NODE SELECTION DETAIL VIEW */
            <div className="space-y-4 animate-fadeIn">
              
              {/* Header */}
              <div className="pb-3 border-b border-slate-100 space-y-1">
                <div className="flex items-center justify-between">
                  <span
                    className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full font-bold text-white shadow-2xs"
                    style={{ backgroundColor: selectedNode.color }}
                  >
                    {selectedNode.type}
                  </span>
                  {selectedNode.risk_indicator && (
                    <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-1.5 py-0.5 rounded">
                      {selectedNode.risk_indicator}
                    </span>
                  )}
                </div>
                <h3 className="font-bold text-sm text-slate-900 break-words">{selectedNode.label}</h3>
                <div className="text-[11px] text-slate-500 font-mono">ID: {selectedNode.id}</div>
              </div>

              {/* Quick Metrics */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200/80">
                  <div className="text-[10px] font-bold text-slate-500 uppercase">Linked Cases</div>
                  <div className="text-lg font-bold text-slate-900">{selectedNode.linked_case_count}</div>
                </div>
                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200/80">
                  <div className="text-[10px] font-bold text-slate-500 uppercase">Degree Weight</div>
                  <div className="text-lg font-bold text-blue-700">{selectedNode.degree || 0}</div>
                </div>
              </div>

              {/* Location & Jurisdiction */}
              <div className="space-y-2 text-xs">
                <div className="flex items-start gap-1.5 text-slate-700">
                  <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-slate-900 block">{selectedNode.district}</span>
                    <span className="text-[11px] text-slate-500">{selectedNode.station}</span>
                  </div>
                </div>

                {/* Additional Entity Details */}
                {selectedNode.details && (
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 space-y-1.5 text-[11px]">
                    <div className="font-bold text-slate-700 uppercase text-[10px]">Entity Attributes</div>
                    {Object.entries(selectedNode.details).map(([k, v]) => (
                      <div key={k} className="flex justify-between items-center">
                        <span className="text-slate-500">{k}:</span>
                        <span className="font-semibold text-slate-900">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Route to Full Profile */}
              <button
                onClick={async () => {
                  setProfileLoading(true);
                  setProfileModalOpen(true);
                  try {
                    const data = await fetchEntityProfile(selectedNode.id, selectedNode.type);
                    setProfileData(data);
                  } catch (e) {
                    console.error(e);
                  } finally {
                    setProfileLoading(false);
                  }
                }}
                className="w-full flex items-center justify-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 px-3 rounded-xl text-xs transition shadow-2xs"
              >
                <ExternalLink className="w-3.5 h-3.5" /> View Full Profile
              </button>
            </div>
          ) : selectedEdge ? (
            /* EDGE SELECTION EXPLAINABLE AI EVIDENCE VIEW */
            <div className="space-y-4 animate-fadeIn">
              
              {/* Header */}
              <div className="pb-3 border-b border-slate-100 space-y-1">
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full font-bold bg-blue-100 text-blue-800 border border-blue-200">
                  Explainable AI Link
                </span>
                <h3 className="font-bold text-xs text-slate-900">{selectedEdge.relation}</h3>
                <div className="text-[11px] text-blue-700 font-mono font-semibold">
                  Link Strength: {selectedEdge.weight} shared event(s)
                </div>
              </div>

              {/* Source Evidence Box */}
              <div className="space-y-2 text-xs">
                <div className="p-3 bg-blue-50/60 rounded-xl border border-blue-200 space-y-2">
                  <div className="font-bold text-blue-900 text-xs flex items-center gap-1">
                    <Info className="w-3.5 h-3.5 text-blue-600" /> Evidence Audit Trail
                  </div>
                  <p className="text-[11px] text-slate-700 leading-relaxed font-medium">
                    {selectedEdge.evidence.description}
                  </p>
                </div>

                {/* Exact CaseMaster IDs List */}
                {selectedEdge.evidence.cases && selectedEdge.evidence.cases.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="font-bold text-slate-700 text-[11px] uppercase flex items-center gap-1">
                      <FileText className="w-3.5 h-3.5 text-slate-500" /> Underlying Case Master IDs
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {selectedEdge.evidence.cases.map((c) => (
                        <span
                          key={c}
                          className="px-2 py-0.5 bg-slate-100 text-slate-800 font-mono text-[11px] rounded border border-slate-200 font-semibold"
                        >
                          Case #{c}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Exact Transaction IDs List */}
                {selectedEdge.evidence.transactions && selectedEdge.evidence.transactions.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <div className="font-bold text-slate-700 text-[11px] uppercase flex items-center gap-1">
                      <CreditCard className="w-3.5 h-3.5 text-amber-600" /> Financial Transaction IDs
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {selectedEdge.evidence.transactions.map((t) => (
                        <span
                          key={t}
                          className="px-2 py-0.5 bg-amber-50 text-amber-900 font-mono text-[11px] rounded border border-amber-200 font-semibold"
                        >
                          Txn #{t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* EMPTY PLACEHOLDER STATE */
            <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 p-4 space-y-2">
              <Info className="w-8 h-8 text-slate-300 stroke-[1.5]" />
              <h4 className="text-xs font-bold text-slate-700">Entity Details & Evidence</h4>
              <p className="text-[11px] text-slate-500 leading-relaxed font-medium">
                Click any node or link in the graph canvas to inspect detailed attributes and underlying evidence records.
              </p>
            </div>
          )}

          <div className="text-[10px] text-slate-400 text-center font-medium pt-2 border-t border-slate-100">
            Explainable AI Grounding
          </div>
        </aside>

      </div>

      {/* FULL OFFENDER / ENTITY DOSSIER MODAL OVERLAY */}
      {profileModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
            
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center p-1 shadow-xs">
                  <img src="/ksp_logo.png" alt="KSP Logo" className="w-7 h-7 object-contain" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-slate-900">
                      {profileData?.label || selectedNode?.label || "Entity Profile"}
                    </h2>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200 font-mono">
                      {profileData?.risk_level || "HIGH RISK"}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 font-medium">
                    Karnataka State Police Official Offender & Case Intelligence Dossier
                  </p>
                </div>
              </div>

              <button
                onClick={() => {
                  setProfileModalOpen(false);
                  setProfileData(null);
                }}
                className="w-8 h-8 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-700 flex items-center justify-center font-bold text-sm transition"
              >
                ✕
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
              
              {profileLoading ? (
                <div className="py-20 text-center text-slate-500 font-medium flex flex-col items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-blue-600 animate-ping" />
                  <span>Loading full criminal history dossier…</span>
                </div>
              ) : profileData ? (
                <>
                  {/* Entity Metadata Cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                      <div className="text-[10px] font-bold text-slate-500 uppercase">Entity Type</div>
                      <div className="font-bold text-slate-900 text-sm mt-0.5 capitalize">{profileData.entity_type}</div>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                      <div className="text-[10px] font-bold text-slate-500 uppercase">Total Linked FIRs</div>
                      <div className="font-bold text-blue-700 text-sm mt-0.5">{profileData.total_cases} Case(s)</div>
                    </div>
                    {Object.entries(profileData.attributes || {}).map(([k, v]) => (
                      <div key={k} className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <div className="text-[10px] font-bold text-slate-500 uppercase">{k}</div>
                        <div className="font-bold text-slate-900 text-sm mt-0.5">{String(v)}</div>
                      </div>
                    ))}
                  </div>

                  {/* Linked Case Master Records Table */}
                  <div className="space-y-3">
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-blue-600" /> Linked Case Master FIR Records ({profileData.cases?.length || 0})
                    </h3>

                    {profileData.cases && profileData.cases.length > 0 ? (
                      <div className="overflow-x-auto border border-slate-200 rounded-xl">
                        <table className="w-full text-left border-collapse">
                          <thead className="bg-slate-100 text-slate-600 uppercase text-[10px] tracking-wider border-b border-slate-200 font-bold">
                            <tr>
                              <th className="p-3">Case Master ID</th>
                              <th className="p-3">Crime No / Reg. Date</th>
                              <th className="p-3">District / Police Station</th>
                              <th className="p-3">Crime Category</th>
                              <th className="p-3">Assigned IO</th>
                              <th className="p-3">Brief Facts Narrative</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
                            {profileData.cases.map((c: any) => (
                              <tr key={c.CaseMasterID} className="hover:bg-slate-50 transition">
                                <td className="p-3 font-mono font-bold text-blue-700">#{c.CaseMasterID}</td>
                                <td className="p-3">
                                  <div className="font-mono font-semibold">{c.CrimeNo || "N/A"}</div>
                                  <div className="text-[10px] text-slate-400">{c.CrimeRegisteredDate}</div>
                                </td>
                                <td className="p-3">
                                  <div className="font-semibold text-slate-900">{c.DistrictName}</div>
                                  <div className="text-[10px] text-slate-500">{c.StationName}</div>
                                </td>
                                <td className="p-3">
                                  <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-800 text-[10px] font-semibold border border-blue-200">
                                    {c.CrimeGroupName || "IPC Offense"}
                                  </span>
                                </td>
                                <td className="p-3 font-semibold text-slate-700">
                                   {c.IOName || c.ioname || "Inspector Assigned"}
                                </td>
                                <td className="p-3 max-w-xs leading-relaxed text-[11px] text-slate-600">
                                  {c.BriefFacts}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="text-slate-400 italic">No detailed case records available.</p>
                    )}
                  </div>

                  {/* SECTION 3: LAW ENFORCEMENT ACTIONABLE RECOMMENDATIONS IN MODAL */}

                  <div className="space-y-3 pt-2 border-t border-slate-100">
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <ShieldAlert className="w-4 h-4 text-amber-600" /> Case-Tailored Actionable Police Recommendations
                    </h3>
                    <div className="space-y-2 bg-amber-50/60 p-4 rounded-xl border border-amber-200">
                      {(profileData.recommendations && profileData.recommendations.length > 0
                        ? profileData.recommendations
                        : generatePersonalizedRecommendations(profileData)
                      ).map((rec: string, idx: number) => (
                        <div key={idx} className="flex items-start gap-2 text-slate-800 leading-relaxed font-medium">
                          <span className="font-bold text-amber-800 shrink-0 font-mono">{idx + 1}.</span>
                          <div dangerouslySetInnerHTML={{ __html: rec.split("**").map((part, i) => i % 2 === 1 ? `<strong>${part}</strong>` : part).join("") }} />
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : null}

            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
              <div className="text-[11px] text-slate-500 font-medium">
                Grounded in Official Karnataka Police Records
              </div>

              <div className="flex items-center gap-2">
                <button
                  disabled={pdfDownloading}
                  onClick={async () => {
                    if (!profileData) return;
                    setPdfDownloading(true);
                    try {
                      const recs = profileData.recommendations || generatePersonalizedRecommendations(profileData);
                      const markdown = [
                        "# GOVERNMENT OF KARNATAKA — STATE POLICE HEADQUARTERS",
                        "## CONFIDENTIAL // LAW ENFORCEMENT INTELLIGENCE USE ONLY",
                        "",
                        `**Document Reference:** KSP-INT-DOSSIER-2026-${Date.now().toString().slice(-6)}`,
                        `**Generated Date:** ${new Date().toLocaleDateString("en-IN", { day: "2-digit", month: "long", year: "numeric" })}`,
                        "---",
                        "",
                        "### SECTION 1: SUBJECT PROFILE & RISK ASSESSMENT",
                        `- **Subject Label / Name:** ${profileData.label}`,
                        `- **Entity Category:** ${profileData.entity_type?.toUpperCase()}`,
                        `- **Recidivism Risk Level:** ${profileData.risk_level}`,
                        `- **Total FIR Records Linked:** ${profileData.total_cases} Case(s)`,
                        ...Object.entries(profileData.attributes || {}).map(([k, v]) => `- **${k}:** ${v}`),
                        "",
                        "---",
                        "",
                        "### SECTION 2: REGISTERED FIR INVESTIGATION RECORDS",
                        ...(profileData.cases || []).flatMap((c: any, idx: number) => [
                          `#### Case ${idx + 1}: FIR No. ${c.CrimeNo || c.crimeno || 'N/A'} (Case Master ID #${c.CaseMasterID || c.casemasterid})`,
                          `- **Registration Date:** ${c.CrimeRegisteredDate || c.crimeregistereddate || 'N/A'}`,
                          `- **Jurisdiction:** ${c.DistrictName || c.districtname || 'Karnataka'} District — ${c.StationName || c.stationname || 'Local PS'}`,
                          `- **Statutory Offense Group:** ${c.CrimeGroupName || c.crimegroupname || 'Penal Code Offense'}`,
                          `- **Assigned Investigating Officer (IO):** ${c.IOName || c.ioname || 'Inspector Assigned'}`,
                          `- **Brief Facts Narrative:** ${c.BriefFacts || c.brieffacts}`,
                          ""
                        ]),
                        "---",
                        "",
                        "### SECTION 3: LAW ENFORCEMENT ACTIONABLE RECOMMENDATIONS",
                        ...recs.map((r: string, idx: number) => `${idx + 1}. ${r}`),
                        "",
                        "---",
                        "",
                        "**ISSUING AUTHORITY:**",
                        "Office of the Director General of Police, State Crime Records Bureau (SCRB), Bengaluru, Karnataka"
                      ].join("\n");
                      
                      const res = await generatePdfReport(`KSP Intelligence Dossier - ${profileData.label}`, markdown);
                      if (res.download_url) {
                        const link = document.createElement("a");
                        link.href = res.download_url;
                        link.download = res.filename || `ksp_dossier_${Date.now()}.pdf`;
                        link.target = "_blank";
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                      }
                    } catch (e) {
                      console.error("PDF generation failed:", e);
                    } finally {
                      setPdfDownloading(false);
                    }
                  }}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-xs transition flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                >
                  <FileText className="w-3.5 h-3.5" />
                  {pdfDownloading ? "Generating PDF…" : "Download Dossier PDF"}
                </button>
                <button
                  onClick={() => {
                    setProfileModalOpen(false);
                    setProfileData(null);
                  }}
                  className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 font-bold text-xs rounded-xl transition cursor-pointer"
                >
                  Close
                </button>
              </div>

            </div>

          </div>
        </div>
      )}
    </div>
  );
}


