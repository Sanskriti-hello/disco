import React from "react";
import type { DashboardRendererProps } from "./types";
import { DashboardComposer } from "../composer/DashboardComposer";

export const DashboardRenderer: React.FC<DashboardRendererProps> = ({ data }) => {
  return <DashboardComposer data={data} />;
};
