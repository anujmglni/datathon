"use client";

import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Download, Info, MapPin, Network } from "lucide-react";

interface NodeData {
  id: string;
  district_name: string;
  case_count: number;
  top_crime_type: string;
  primary_station: string;
  sample_facts: string;
  risk_type: string;
  investigating_officer: string;
  lat: number;
  lng: number;
}

interface LinkData {
  source: string;
  target: string;
  relation: string;
  shared_accused: string;
  transfer_amount_inr: number;
  linked_firs: string;
  directive: string;
}

interface KarnatakaLeafletMapProps {
  nodes: NodeData[];
  links: LinkData[];
  description?: string;
  howToRead?: string;
}

const RISK_COLOR_HEX: Record<string, string> = {
  severity: "#dc2626", // Red
  hotspot: "#d97706", // Amber
  repeat_offender: "#7c3aed", // Purple
  standard: "#2563eb" // Blue
};

const RISK_LABEL_MAP: Record<string, string> = {
  severity: "🔴 High Severity (Grave)",
  hotspot: "🟡 Financial Fraud Hotspot",
  repeat_offender: "🟣 Repeat Offender Syndicate",
  standard: "🔵 Standard Case Jurisdiction"
};

export default function KarnatakaLeafletMap({ nodes, links, description, howToRead }: KarnatakaLeafletMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const [selectedNode, setSelectedNode] = useState<NodeData | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Initialize Leaflet Map centered on Karnataka [14.5204, 75.7224] zoom level 7
    const map = L.map(mapContainerRef.current, {
      center: [14.5204, 75.7224],
      zoom: 7,
      scrollWheelZoom: false
    });

    // Dark CartoDB Voyager Tile Layer for high-contrast GIS aesthetic
    L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://openstreetmap.org">OpenStreetMap</a>',
      maxZoom: 18
    }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update Markers & Network Polylines on Data Change
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Clear existing layers except base tile layer
    map.eachLayer((layer) => {
      if (layer instanceof L.Marker || layer instanceof L.Polyline || layer instanceof L.CircleMarker) {
        map.removeLayer(layer);
      }
    });

    // 1. Render Inter-District Network Linkage Lines (Polylines)
    links.forEach((link) => {
      const srcNode = nodes.find((n) => n.district_name === link.source);
      const tgtNode = nodes.find((n) => n.district_name === link.target);
      if (!srcNode || !tgtNode) return;

      const polyline = L.polyline(
        [
          [srcNode.lat, srcNode.lng],
          [tgtNode.lat, tgtNode.lng]
        ],
        {
          color: "#ec4899",
          weight: 3,
          dashArray: "6, 6",
          opacity: 0.85
        }
      ).addTo(map);

      // Network Link Popup
      const linkPopupHtml = `
        <div style="font-family: sans-serif; font-size: 11px; padding: 4px; max-width: 250px;">
          <div style="font-weight: bold; color: #be185d; border-bottom: 1px solid #fbcfe8; padding-bottom: 4px; margin-bottom: 4px;">
            🌐 Network Link: ${link.source} ↔ ${link.target}
          </div>
          <div><strong>Relation:</strong> ${link.relation}</div>
          <div><strong>Shared Accused:</strong> ${link.shared_accused}</div>
          <div><strong>Fraud Amount:</strong> ₹${link.transfer_amount_inr.toLocaleString()} INR</div>
          <div style="margin-top: 4px; font-size: 10px; color: #475569;"><strong>Linked FIRs:</strong> ${link.linked_firs}</div>
          <div style="margin-top: 4px; color: #047857; font-weight: bold;">⚡ Directive: ${link.directive}</div>
        </div>
      `;
      polyline.bindPopup(linkPopupHtml);
    });

    // 2. Render District Case Node Circle Markers with Custom Risk Colors
    nodes.forEach((node) => {
      const color = RISK_COLOR_HEX[node.risk_type] || "#2563eb";
      
      const marker = L.circleMarker([node.lat, node.lng], {
        radius: Math.min(Math.max(node.case_count / 150, 10), 22),
        fillColor: color,
        color: "#ffffff",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.85
      }).addTo(map);

      // Node Case Hover Card Popup
      const nodePopupHtml = `
        <div style="font-family: sans-serif; font-size: 11px; padding: 4px; max-width: 260px;">
          <div style="font-weight: bold; font-size: 12px; color: #1e3a8a; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin-bottom: 4px;">
            📍 ${node.district_name} District Jurisdiction
          </div>
          <div style="display: inline-block; background: #eff6ff; color: #1d4ed8; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; margin-bottom: 6px;">
            ${RISK_LABEL_MAP[node.risk_type] || "Standard"} (${node.case_count} Cases)
          </div>
          <div><strong>Station:</strong> ${node.primary_station}</div>
          <div><strong>Top Category:</strong> ${node.top_crime_type}</div>
          <div><strong>Investigating Officer:</strong> ${node.investigating_officer}</div>
          <div style="margin-top: 6px; font-size: 10px; color: #475569; font-style: italic;">
            "${node.sample_facts}"
          </div>
        </div>
      `;

      marker.bindPopup(nodePopupHtml);
      marker.on("mouseover", () => {
        marker.openPopup();
        setSelectedNode(node);
      });
    });
  }, [nodes, links]);

  // PNG Canvas Image Exporter
  const handleExportMapImage = () => {
    const container = mapContainerRef.current;
    if (!container) return;
    const printWin = window.open("", "_blank");
    if (!printWin) return;
    printWin.document.write(`
      <html>
        <head><title>Karnataka GIS Map Export</title></head>
        <body style="font-family:sans-serif; padding:30px;">
          <h2>Karnataka State Police — Geo-Spatial GIS Map</h2>
          <p>Generated: ${new Date().toLocaleString()}</p>
          <div style="border:1px solid #ccc; padding:15px; border-radius:12px;">
            ${container.outerHTML}
          </div>
          <script>window.onload = function() { window.print(); window.close(); }</script>
        </body>
      </html>
    `);
    printWin.document.close();
  };

  return (
    <div id="ndap-karnataka-map-card" className="bg-white border-2 border-slate-200 rounded-3xl p-6 shadow-md relative space-y-4 col-span-full">
      
      {/* Header Controls */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-50 border border-blue-200 rounded-xl text-blue-600">
            <MapPin className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-extrabold text-base text-slate-900 flex items-center gap-2">
              Karnataka State GIS Map & Cross-District Network Linkages
              <span className="text-[10px] bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full font-mono font-semibold">
                NDAP GIS Engine (Leaflet Stack)
              </span>
            </h2>
            <p className="text-xs text-slate-500 font-medium">
              Interactive Leaflet GIS map displaying district case nodes color-coded by intelligence risk type and cross-district network linkage lines.
            </p>
          </div>
        </div>

        <button
          onClick={handleExportMapImage}
          className="flex items-center gap-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-bold px-3 py-1.5 rounded-xl border border-blue-200 transition cursor-pointer"
        >
          <Download className="w-3.5 h-3.5" />
          Export Map (PDF/Print)
        </button>
      </div>

      {/* RISK COLOR LEGEND OVERLAY */}
      <div className="flex flex-wrap items-center gap-4 bg-slate-50 border border-slate-200 p-2.5 rounded-xl text-xs">
        <span className="text-slate-500 font-bold text-[11px] uppercase tracking-wider">NDAP Risk Legend:</span>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-rose-600 border border-white" />
          <span className="text-slate-800 font-semibold text-[11px]">🔴 High Severity</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-amber-500 border border-white" />
          <span className="text-slate-800 font-semibold text-[11px]">🟡 Financial Hotspot</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-purple-600 border border-white" />
          <span className="text-slate-800 font-semibold text-[11px]">🟣 Repeat Offender Syndicate</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-blue-600 border border-white" />
          <span className="text-slate-800 font-semibold text-[11px]">🔵 Standard Node</span>
        </div>
        <div className="flex items-center gap-1.5 border-l border-slate-200 pl-3">
          <span className="w-5 h-0.5 bg-pink-500 border-t border-dashed border-pink-400" />
          <span className="text-pink-600 font-semibold text-[11px]">🌐 Cross-District Linkage</span>
        </div>
      </div>

      {/* LEAFLET MAP TARGET CONTAINER (Height ~460px) */}
      <div className="relative w-full h-[460px] rounded-2xl overflow-hidden border border-slate-200 shadow-inner z-0">
        <div ref={mapContainerRef} className="w-full h-full" />
      </div>

      {/* Plain Language Summary Box */}
      {description && (
        <div className="bg-blue-50/70 border-l-4 border-blue-600 rounded-r-2xl p-3 text-xs text-blue-950 space-y-1">
          <p className="leading-relaxed font-medium">{description}</p>
          {howToRead && (
            <p className="text-[11px] text-blue-700 italic pt-1 border-t border-blue-100/60">
              How to read: {howToRead}
            </p>
          )}
        </div>
      )}

    </div>
  );
}
