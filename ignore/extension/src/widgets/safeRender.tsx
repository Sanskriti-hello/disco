import React from "react";
import { isActionObject, isLinkArray, isMediaObject, isRecord } from "./guards";

export const ActionObjectRenderer: React.FC<{ actions: Record<string, unknown> }> = ({ actions }) => (
  <div className="flex flex-wrap gap-2 mt-3">
    {Object.entries(actions).map(([k, v]) => (
      <button key={k} type="button" className="rounded-full border border-cyan-400/30 bg-cyan-500/20 px-4 py-1.5 text-xs font-medium text-cyan-50 transition-colors hover:bg-cyan-500/30 hover:border-cyan-400/50 backdrop-blur-sm">
        {k} {typeof v === "boolean" ? (v ? "On" : "Off") : String(v)}
      </button>
    ))}
  </div>
);

export const MetadataRenderer: React.FC<{ data: Record<string, unknown> }> = ({ data }) => (
  <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-4 mt-3">
    {Object.entries(data).map(([k, v]) => (
      <div key={k} className="flex justify-between items-start gap-4 border-b border-white/5 py-2 last:border-0 text-sm">
        <span className="text-white/50 font-medium">{k}</span>
        <span className="text-white/90 text-right line-clamp-3 break-words max-w-[60%]">{safeRenderValue(v)}</span>
      </div>
    ))}
  </div>
);

export function safeRenderValue(value: unknown): React.ReactNode {
  if (value == null) return <span className="text-white/30">-</span>;
  if (typeof value === "string" || typeof value === "number") return value;
  if (typeof value === "boolean") return value ? "Yes" : "No";

  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-white/30">No items</span>;
    if (isLinkArray(value)) {
      return (
        <ul className="space-y-2 mt-2">
          {value.slice(0, 5).map((l, i) => (
            <li key={`${l.title || l.url || "link"}-${i}`} className="text-sm">
              {l.url ? <a href={l.url} target="_blank" rel="noreferrer" className="text-cyan-400 hover:text-cyan-300 transition-colors inline-flex items-center gap-1">{l.title || l.url} <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg></a> : <span className="text-white/80">{l.title || "Link"}</span>}
            </li>
          ))}
        </ul>
      );
    }
    return (
      <div className="space-y-1.5 mt-2">
        {value.slice(0, 5).map((item, i) => (
          <div key={i} className="text-sm text-white/80">{safeRenderValue(item)}</div>
        ))}
      </div>
    );
  }

  if (isRecord(value)) {
    if (isActionObject(value)) return <ActionObjectRenderer actions={value} />;
    if (isMediaObject(value)) {
      const image = typeof value.image === "string" ? value.image : "";
      return image ? <img loading="lazy" src={image} alt="preview" className="mt-3 h-32 w-full rounded-xl object-cover" /> : null;
    }
    return <MetadataRenderer data={value} />;
  }

  return null;
}

export const ObjectRenderer: React.FC<{ data: unknown; label?: string }> = ({ data, label }) => {
  if (!isRecord(data) && !Array.isArray(data)) {
    return <>{safeRenderValue(data)}</>;
  }

  if (Array.isArray(data)) {
    return (
      <div className="space-y-2">
        {data.map((item, i) => (
          <div key={i}>{safeRenderValue(item)}</div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {label ? <h4 className="text-sm font-semibold text-white/90">{label}</h4> : null}
      <MetadataRenderer data={data} />
    </div>
  );
};
