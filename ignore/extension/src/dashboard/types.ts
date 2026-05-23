export interface DashboardSection {
  type: string;
  priority: "high" | "medium" | "low" | string;
  content: Record<string, any>;
}

export interface DynamicDashboard {
  theme: string;
  layout: string;
  sections: DashboardSection[];
  metadata?: Record<string, unknown>;
}

export interface DashboardApiResponse {
  success: boolean;
  template: string;
  dashboard: DynamicDashboard;
  error?: string;
}

export interface DashboardRendererProps {
  template: string;
  data: DynamicDashboard;
}
