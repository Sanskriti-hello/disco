import React from "react";
import { isWidget } from "./guards";
import type { DashboardWidgetSchema } from "./types";

export function sanitizeWidget(input: unknown, index: number): DashboardWidgetSchema {
  if (!isWidget(input)) {
    console.warn("[widget] invalid widget shape", { index, input });
    return {
      type: "fallback",
      title: "Invalid Widget",
      subtitle: "Widget payload failed validation",
      error: "Invalid widget payload",
      data: { raw: input },
      items: [],
      priority: 99,
    };
  }

  const raw = input as Record<string, unknown>;
  const items = Array.isArray(raw.items) ? raw.items : [];
  const widget: DashboardWidgetSchema = {
    type: String(raw.type || "fallback"),
    title: typeof raw.title === "string" ? raw.title : undefined,
    subtitle: typeof raw.subtitle === "string" ? raw.subtitle : undefined,
    priority: typeof raw.priority === "number" ? raw.priority : 50,
    loading: Boolean(raw.loading),
    error: typeof raw.error === "string" ? raw.error : undefined,
    empty: Boolean(raw.empty),
    items: items as any,
    data: (raw.data && typeof raw.data === "object") ? (raw.data as Record<string, unknown>) : undefined,
  };

  if (!widget.type) {
    widget.type = "fallback";
  }

  return widget;
}

export function sanitizeWidgetList(list: unknown[]): DashboardWidgetSchema[] {
  return list.map((w, i) => sanitizeWidget(w, i));
}

export const WidgetValidationBadge: React.FC<{ valid: boolean }> = ({ valid }) => (
  <span className={`rounded-full px-2 py-0.5 text-[10px] ${valid ? "bg-emerald-500/20 text-emerald-200" : "bg-rose-500/20 text-rose-200"}`}>
    {valid ? "valid" : "invalid"}
  </span>
);
