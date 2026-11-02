import React from "react";
import { Droplet, Database, CheckCircle, RefreshCw, Layers } from "lucide-react";
import { BackendHealth } from "../types";

interface NavbarProps {
  activeTab: "chat" | "dashboard" | "evaluation";
  setActiveTab: (tab: "chat" | "dashboard" | "evaluation") => void;
  health: BackendHealth | null;
  onRefreshHealth: () => void;
  showDevTab?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  health,
  onRefreshHealth,
  showDevTab = false
}) => {
  return (
    <header className="border-b border-slate-200/80 bg-white/95 backdrop-blur sticky top-0 z-40 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab("chat")}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-blue-500 flex items-center justify-center shadow-md shadow-sky-500/20">
            <Droplet className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
              WaterBoy
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-sky-50 text-sky-600 border border-sky-200">
                Groundwater AI
              </span>
            </h1>
            <p className="text-xs text-sky-600 font-medium">National Groundwater Intelligence Platform</p>
          </div>
        </div>

        {/* Navigation Tabs (Benchmark kept private, only public core tools) */}
        <nav className="flex items-center space-x-1 sm:space-x-1.5 bg-slate-100 p-1 rounded-xl border border-slate-200/80">
          <button
            onClick={() => setActiveTab("chat")}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === "chat"
                ? "bg-white text-sky-600 shadow-xs border border-slate-200/60"
                : "text-slate-600 hover:text-sky-600 hover:bg-white/50"
            }`}
          >
            AI Assistant
          </button>
          <button
            onClick={() => setActiveTab("dashboard")}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-1.5 ${
              activeTab === "dashboard"
                ? "bg-white text-sky-600 shadow-xs border border-slate-200/60"
                : "text-slate-600 hover:text-sky-600 hover:bg-white/50"
            }`}
          >
            <Database className="w-4 h-4 text-sky-500" />
            CGWB Multi-Year Explorer
          </button>

          {showDevTab && (
            <button
              onClick={() => setActiveTab("evaluation")}
              className={`px-3 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-1 ${
                activeTab === "evaluation"
                  ? "bg-white text-sky-600 shadow-xs border border-slate-200/60"
                  : "text-slate-500 hover:text-sky-600 hover:bg-white/50"
              }`}
            >
              [Dev Benchmark]
            </button>
          )}
        </nav>

        {/* Status Indicator */}
        <div className="hidden md:flex items-center space-x-3">
          {health ? (
            <div className="flex items-center space-x-2 text-xs bg-sky-50 text-sky-700 border border-sky-200/80 px-3.5 py-1.5 rounded-full font-medium">
              <CheckCircle className="w-3.5 h-3.5 text-sky-500" />
              <span>
                System Online • <strong className="font-semibold text-slate-900">{health.total_indexed_chunks}</strong> Chunks
              </span>
            </div>
          ) : (
            <div className="flex items-center space-x-2 text-xs bg-amber-50 text-amber-700 border border-amber-200 px-3.5 py-1.5 rounded-full font-medium">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-amber-500" />
              <span>Connecting to Backend...</span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
