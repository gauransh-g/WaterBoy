import React, { useState, useEffect } from "react";
import { Navbar } from "./components/Navbar";
import { ChatInterface } from "./components/ChatInterface";
import { GroundwaterDashboard } from "./components/GroundwaterDashboard";
import { EvaluationView } from "./components/EvaluationView";
import { SourceViewerModal } from "./components/SourceViewerModal";
import { Citation, BackendHealth } from "./types";
import { fetchHealth } from "./services/api";

export function App() {
  const [activeTab, setActiveTab] = useState<"chat" | "dashboard" | "evaluation">("chat");
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  // Private developer flag to view benchmark suite
  const isDevMode = typeof window !== "undefined" && (
    window.location.search.includes("dev=true") || 
    window.location.search.includes("benchmark=true") ||
    window.location.hash === "#dev"
  );

  const loadHealth = async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch (err) {
      console.warn("Backend not yet reachable:", err);
      setHealth(null);
    }
  };

  useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col antialiased selection:bg-sky-100 selection:text-sky-800">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        onRefreshHealth={loadHealth}
        showDevTab={isDevMode}
      />

      <main className="flex-1">
        {activeTab === "chat" && (
          <ChatInterface onViewSource={(cite) => setActiveCitation(cite)} />
        )}
        {activeTab === "dashboard" && <GroundwaterDashboard />}
        {activeTab === "evaluation" && isDevMode && <EvaluationView />}
      </main>

      <SourceViewerModal
        citation={activeCitation}
        onClose={() => setActiveCitation(null)}
      />
    </div>
  );
}

export default App;
