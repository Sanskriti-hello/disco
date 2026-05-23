import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { DashboardRenderer } from "./dashboard/DashboardRenderer";
import { DashboardErrorBoundary } from "./dashboard/DashboardErrorBoundary";
import type { DashboardApiResponse } from "./dashboard/types";
import "./dashboard/dashboard.css";

declare const chrome: any;

const DashboardApp: React.FC = () => {
  const [config, setConfig] = useState<DashboardApiResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log("[dashboard] booted");
    chrome.storage.local.get(["dashboardConfig"], (result: { dashboardConfig?: DashboardApiResponse }) => {
      const cfg = result.dashboardConfig;
      console.log("[dashboard] config", cfg);
      if (!cfg || !cfg.success) {
        setError((cfg as any)?.error || "No dashboard data found. Generate a dashboard first.");
        return;
      }
      setConfig(cfg);
    });
  }, []);

  if (error) {
    return (
      <div className="dash-error">
        <div>
          <h2>No dashboard payload found</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!config) {
    return <div className="dash-loading">Loading dashboard...</div>;
  }

  return (
    <DashboardErrorBoundary>
      <DashboardRenderer template={config.template} data={config.dashboard} />
    </DashboardErrorBoundary>
  );
};

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(<DashboardApp />);
}
