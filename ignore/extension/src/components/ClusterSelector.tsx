import React, { useState, useEffect } from "react";

// Declare chrome global for TypeScript
declare const chrome: {
    runtime?: {
        sendMessage: (
            message: { action?: string; type?: string; apiKey?: string; clusterId?: number; userPrompt?: string },
            callback?: (response: unknown) => void
        ) => void;
        lastError?: { message: string };
    };
    storage?: {
        local: {
            get: (keys: string | string[], callback: (result: Record<string, unknown>) => void) => void;
            set: (data: Record<string, unknown>) => void;
        };
    };
};

interface Tab {
    id: number;
    title: string;
    url: string;
    content: string;
}

interface Cluster {
    cluster_id: number;
    tabs: Tab[];
    domain: string;
    summary: string;
    cluster_name: string;
}

interface DomainResult {
    domain: string;
    tabs: Tab[];
    summary: string;
    userPrompt: string;
    timestamp: number;
}

// Domain icons and colors
const DOMAIN_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
    study: { icon: "📚", color: "#8B5CF6", label: "Study" },
    shopping: { icon: "🛒", color: "#F59E0B", label: "Shopping" },
    travel: { icon: "✈️", color: "#06B6D4", label: "Travel" },
    code: { icon: "💻", color: "#10B981", label: "Code" },
    entertainment: { icon: "🎬", color: "#EC4899", label: "Entertainment" },
    generic: { icon: "📋", color: "#6B7280", label: "General" }
};

// Hardcoded API key (loaded from env during build)
const API_KEY = "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";

interface ClusterSelectorProps {
    isOpen: boolean;
    onClose: () => void;
    onDomainSelected?: (result: DomainResult) => void;
}

export const ClusterSelector: React.FC<ClusterSelectorProps> = ({
    isOpen,
    onClose,
    onDomainSelected
}) => {
    const [clusters, setClusters] = useState<Cluster[]>([]);
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState("Click 'Analyze Tabs' to start");
    const [selectedCluster, setSelectedCluster] = useState<number | null>(null);
    const [customPrompt, setCustomPrompt] = useState("");
    const [domainResult, setDomainResult] = useState<DomainResult | null>(null);
    const [step, setStep] = useState<"init" | "clusters" | "result">("init");

    // Auto-analyze when popup opens
    useEffect(() => {
        if (isOpen && step === "init" && clusters.length === 0) {
            // Auto-start analysis when opened
        }
    }, [isOpen]);

    // Cluster tabs with proper error handling
    const handleClusterTabs = () => {
        if (!chrome?.runtime?.sendMessage) {
            setStatus("Extension not available. Please reload the extension.");
            return;
        }

        setLoading(true);
        setStatus("Analyzing your tabs...");

        chrome.runtime.sendMessage(
            { action: "clusterTabs", apiKey: API_KEY },
            (response: unknown) => {
                // MANDATORY: Check for runtime errors first
                if (chrome.runtime?.lastError) {
                    console.error("Runtime error:", chrome.runtime.lastError.message);
                    setLoading(false);
                    setStatus(`Error: ${chrome.runtime.lastError.message}`);
                    return;
                }

                const res = response as { success?: boolean; clusters?: Cluster[]; totalTabs?: number; error?: string };
                setLoading(false);

                if (res?.success && res.clusters) {
                    setClusters(res.clusters);
                    setStatus(`Found ${res.totalTabs} tabs in ${res.clusters.length} clusters`);
                    setStep("clusters");
                } else {
                    setStatus(res?.error || "Failed to analyze tabs. Make sure you have tabs open.");
                }
            }
        );
    };

    // Select domain with proper error handling
    const handleSelectDomain = () => {
        if (selectedCluster === null && !customPrompt.trim()) {
            setStatus("Please select a cluster or enter a custom prompt");
            return;
        }

        if (!chrome?.runtime?.sendMessage) {
            setStatus("Extension not available. Please reload the extension.");
            return;
        }

        setLoading(true);
        setStatus("Determining best domain...");

        const clusterId = selectedCluster !== null ? selectedCluster : clusters[0]?.cluster_id ?? 0;

        chrome.runtime.sendMessage(
            {
                action: "selectDomain",
                apiKey: API_KEY,
                clusterId: clusterId,
                userPrompt: customPrompt.trim()
            },
            (response: unknown) => {
                // MANDATORY: Check for runtime errors first
                if (chrome.runtime?.lastError) {
                    console.error("Runtime error:", chrome.runtime.lastError.message);
                    setLoading(false);
                    setStatus(`Error: ${chrome.runtime.lastError.message}`);
                    return;
                }

                const res = response as { success?: boolean; result?: DomainResult; error?: string };
                setLoading(false);

                if (res?.success && res.result) {
                    setDomainResult(res.result);
                    setStatus("Domain selected!");
                    setStep("result");
                    onDomainSelected?.(res.result);
                } else {
                    setStatus(res?.error || "Failed to select domain");
                }
            }
        );
    };

    // Reset
    const handleReset = () => {
        setStep("init");
        setClusters([]);
        setSelectedCluster(null);
        setCustomPrompt("");
        setDomainResult(null);
        setStatus("Click 'Analyze Tabs' to start");
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Popup Container */}
            <div className="relative w-[550px] max-h-[85vh] overflow-auto bg-[#0a0a1a] rounded-3xl border-2 border-[#6375c540] shadow-2xl">
                {/* Header */}
                <div className="sticky top-0 bg-[#0a0a1a] p-5 pb-3 border-b border-[#ffffff1a] flex items-center justify-between z-10">
                    <h2 className="font-['Hanken_Grotesk'] font-medium text-[#ffffffcc] text-xl">
                        🎯 What are you working on?
                    </h2>
                    <button
                        onClick={onClose}
                        className="w-8 h-8 flex items-center justify-center rounded-full bg-[#ffffff1a] hover:bg-[#ffffff26] transition-colors text-[#ffffffcc]"
                    >
                        ✕
                    </button>
                </div>

                {/* Content */}
                <div className="p-5">
                    {/* Status */}
                    <p className="text-[#ffffff80] text-sm mb-4 text-center">{status}</p>

                    {/* Step 1: Analyze button */}
                    {step === "init" && (
                        <div className="space-y-4">
                            <p className="text-[#ffffffcc] text-center text-sm">
                                Click below to analyze your open tabs and find what you're working on.
                            </p>
                            <button
                                onClick={handleClusterTabs}
                                disabled={loading}
                                className="w-full py-4 rounded-xl bg-gradient-to-r from-[#6375c5] to-[#8B5CF6] text-white font-semibold hover:opacity-90 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <>
                                        <span className="animate-spin">⏳</span>
                                        Analyzing...
                                    </>
                                ) : (
                                    <>🔍 Analyze My Tabs</>
                                )}
                            </button>
                        </div>
                    )}

                    {/* Step 2: Show Clusters */}
                    {step === "clusters" && (
                        <div className="space-y-4">
                            <p className="text-[#ffffffcc] text-sm font-medium">Select what you're working on:</p>

                            {/* Cluster cards */}
                            <div className="space-y-2 max-h-[280px] overflow-auto">
                                {clusters.map((cluster) => {
                                    const config = DOMAIN_CONFIG[cluster.domain] || DOMAIN_CONFIG.generic;
                                    const isSelected = selectedCluster === cluster.cluster_id;

                                    return (
                                        <button
                                            key={cluster.cluster_id}
                                            onClick={() => setSelectedCluster(cluster.cluster_id)}
                                            className={`w-full p-4 rounded-xl text-left transition-all border ${isSelected
                                                ? "border-[#6375c5] bg-[#6375c540]"
                                                : "border-[#ffffff1a] bg-[#6375c520] hover:bg-[#6375c530]"
                                                }`}
                                        >
                                            <div className="flex items-center gap-3">
                                                <span className="text-2xl">{config.icon}</span>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <h3 className="text-[#ffffffcc] font-semibold truncate">
                                                            {cluster.cluster_name}
                                                        </h3>
                                                        <span
                                                            className="text-xs px-2 py-0.5 rounded-full flex-shrink-0"
                                                            style={{ backgroundColor: config.color + "33", color: config.color }}
                                                        >
                                                            {config.label}
                                                        </span>
                                                    </div>
                                                    <p className="text-[#ffffff80] text-xs mt-1 truncate">{cluster.summary}</p>
                                                    <p className="text-[#ffffff60] text-xs">{cluster.tabs.length} tabs</p>
                                                </div>
                                                {isSelected && (
                                                    <span className="text-[#6375c5] text-lg flex-shrink-0">✓</span>
                                                )}
                                            </div>
                                        </button>
                                    );
                                })}
                            </div>

                            {/* Other option */}
                            <div className="border-t border-[#ffffff1a] pt-4">
                                <p className="text-[#ffffff99] text-sm mb-2">
                                    📝 Or type what you need:
                                </p>
                                <textarea
                                    value={customPrompt}
                                    onChange={(e) => setCustomPrompt(e.target.value)}
                                    placeholder="e.g., 'Make a quiz from my research' or 'Compare laptop prices'"
                                    className="w-full p-3 rounded-xl bg-[#1a1a2e] text-white border border-[#ffffff33] resize-none h-16 focus:outline-none focus:border-[#6375c5] text-sm placeholder:text-[#ffffff40]"
                                />
                            </div>

                            {/* Action buttons */}
                            <div className="flex gap-3 pt-2">
                                <button
                                    onClick={handleReset}
                                    className="flex-1 py-3 rounded-xl border border-[#ffffff33] text-[#ffffffcc] font-medium hover:bg-[#ffffff11] transition-all text-sm"
                                >
                                    ← Back
                                </button>
                                <button
                                    onClick={handleSelectDomain}
                                    disabled={loading || (selectedCluster === null && !customPrompt.trim())}
                                    className="flex-1 py-3 rounded-xl bg-gradient-to-r from-[#6375c5] to-[#8B5CF6] text-white font-semibold hover:opacity-90 disabled:opacity-50 transition-all text-sm"
                                >
                                    {loading ? "Processing..." : "Continue →"}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Step 3: Show Result */}
                    {step === "result" && domainResult && (
                        <div className="space-y-4 text-center">
                            <div className="text-5xl mb-2">
                                {DOMAIN_CONFIG[domainResult.domain]?.icon || "📋"}
                            </div>

                            <h3 className="text-[#ffffffcc] text-xl font-semibold">
                                {DOMAIN_CONFIG[domainResult.domain]?.label || "General"} Mode
                            </h3>

                            <p className="text-[#ffffff80] text-sm">{domainResult.summary}</p>

                            {/* Result JSON */}
                            <div className="bg-[#1a1a2e] rounded-xl p-4 text-left">
                                <p className="text-[#ffffff60] text-xs mb-2">Domain Result:</p>
                                <pre className="text-[#10B981] text-xs overflow-auto">
                                    {JSON.stringify({
                                        domain: domainResult.domain,
                                        tabCount: domainResult.tabs.length,
                                        summary: domainResult.summary,
                                        userPrompt: domainResult.userPrompt || null
                                    }, null, 2)}
                                </pre>
                            </div>

                            <button
                                onClick={handleReset}
                                className="w-full py-3 rounded-xl border border-[#ffffff33] text-[#ffffffcc] font-medium hover:bg-[#ffffff11] transition-all text-sm"
                            >
                                ← Start Over
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ClusterSelector;
