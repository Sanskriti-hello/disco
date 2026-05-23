import React from "react";
import type { DashboardSection } from "../dashboard/types";
import { WIDGET_REGISTRY } from "./SectionRegistry";
import { FallbackWidget } from "../widgets/components";

// Adapter to reuse the premium components we already built
export const SectionRenderer: React.FC<{ section: DashboardSection }> = ({ section }) => {
  // Try to find the exact component, map common aliases to known types
  const typeMap: Record<string, string> = {
    "content-grid": "product_grid",
    "media-carousel": "media_carousel",
    "recommendations": "recommendation_slider",
    "quick-actions": "action_list",
  };
  
  const resolvedType = typeMap[section.type] || section.type;
  const Cmp = WIDGET_REGISTRY[resolvedType] || FallbackWidget;

  const content = section.content || {};
  
  const widgetProps = {
    type: resolvedType,
    title: content.title,
    subtitle: content.subtitle || content.description,
    items: content.items || content.actions || [],
    data: content,
  };

  // Skip rendering empty widgets gracefully
  if (!widgetProps.title && (!widgetProps.items || widgetProps.items.length === 0) && resolvedType !== "hero") {
    return null;
  }

  return <Cmp widget={widgetProps as any} />;
};
