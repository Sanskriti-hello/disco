import React from "react";

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  message: string;
}

export class DashboardErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error?.message || "Unknown render error" };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("[dashboard] render crash", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="dash-error">
          <div>
            <h2>Dashboard render error</h2>
            <p>{this.state.message}</p>
            <p className="text-xs">Malformed widget payload was safely caught.</p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
