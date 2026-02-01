import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { FinanceAIDashboard } from "./screens/FinanceAiDashboard/FinanceAiDashboard";

const rootElement = document.getElementById("root");
if (!rootElement) {
    const err = "Root element not found";
    console.error(err);
    const pre = document.createElement("pre");
    pre.style.whiteSpace = "pre-wrap";
    pre.style.color = "red";
    pre.textContent = err;
    document.body.appendChild(pre);
} else {
    try {
        createRoot(rootElement).render(
            <StrictMode>
                <FinanceAIDashboard />
            </StrictMode>
        );
    } catch (e: any) {
        console.error("Render error:", e);
        const pre = document.createElement("pre");
        pre.style.whiteSpace = "pre-wrap";
        pre.style.color = "red";
        pre.textContent = e?.stack || String(e);
        document.body.appendChild(pre);
        // Expose error for easier inspection in extension manager
        (window as any).__EXT_RENDER_ERROR = e;
    }
}