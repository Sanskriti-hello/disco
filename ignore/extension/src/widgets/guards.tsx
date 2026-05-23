import React from "react";

export type UnknownRecord = Record<string, unknown>;

export function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isWidget(value: unknown): value is { type: string; [k: string]: unknown } {
  return isRecord(value) && typeof value.type === "string";
}

export function isActionObject(value: unknown): value is Record<string, boolean | string | number> {
  if (!isRecord(value)) return false;
  const keys = Object.keys(value);
  if (keys.length === 0) return false;
  return keys.every((k) => ["boolean", "string", "number"].includes(typeof value[k]));
}

export function isMediaObject(value: unknown): value is { image?: string; video?: string; audio?: string } {
  return isRecord(value) && (["image", "video", "audio"] as const).some((k) => typeof value[k] === "string");
}

export function isLinkArray(value: unknown): value is Array<{ title?: string; url?: string; summary?: string }> {
  return Array.isArray(value) && value.every((v) => !v || (isRecord(v) && (typeof v.title === "string" || typeof v.url === "string" || typeof v.summary === "string")));
}

export function summarizeUnknown(value: unknown): string {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) return `${value.length} items`;
  if (isRecord(value)) return `${Object.keys(value).length} fields`;
  return "Unsupported value";
}
