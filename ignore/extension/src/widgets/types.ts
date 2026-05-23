export interface WidgetItem {
  title?: string;
  description?: string;
  image?: string;
  audio?: string;
  video?: string;
  link?: string;
  value?: string | number;
  meta?: Record<string, unknown>;
}

export interface DashboardWidgetSchema {
  type: string;
  title?: string;
  subtitle?: string;
  priority?: number;
  loading?: boolean;
  error?: string;
  empty?: boolean;
  items?: WidgetItem[];
  data?: Record<string, unknown>;
}
