import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { FinanceAIDashboard } from "./screens/FinanceAiDashboard";

// Initialize the React app
createRoot(document.getElementById("root") as HTMLElement).render(
    <StrictMode>
        <FinanceAIDashboard />
    </StrictMode>
);
