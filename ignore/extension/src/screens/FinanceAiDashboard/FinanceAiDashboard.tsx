import { useState } from "react";
import { ClusterSelector } from "../../components/ClusterSelector";

// Inline SVG icons to avoid 403 errors from external sources
const Icons = {
  logo: (
    <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  home: (
    <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  chart: (
    <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
      <path d="M18 20V10M12 20V4M6 20v-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  search: (
    <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
      <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2" />
      <path d="M21 21l-4.35-4.35" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
  calendar: (
    <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
      <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2" />
      <path d="M16 2v4M8 2v4M3 10h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  ),
  settings: (
    <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" stroke="currentColor" strokeWidth="2" />
    </svg>
  ),
  bell: (
    <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  chat: (
    <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  wallet: (
    <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
      <path d="M21 12.5V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-1.5" stroke="currentColor" strokeWidth="2" />
      <circle cx="18" cy="12" r="2" stroke="currentColor" strokeWidth="2" />
    </svg>
  ),
  arrow: (
    <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
      <path d="M7 17L17 7M17 7H7M17 7v10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
};

export const FinanceAIDashboard = (): JSX.Element => {
  const [isClusterSelectorOpen, setIsClusterSelectorOpen] = useState(false);
  const [dashboardConfig, setDashboardConfig] = useState<any>(null);

  // If dashboard is generated, show the dashboard screen
  if (dashboardConfig) {
    return (
      <div className="bg-[#050510] min-h-screen w-full flex flex-col p-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-white">AI Generated Dashboard</h1>
          <button
            onClick={() => setDashboardConfig(null)}
            className="px-4 py-2 bg-[#6375c520] border border-[#6375c5] rounded-lg text-[#6375c5] hover:bg-[#6375c540]"
          >
            ← Back to Home
          </button>
        </div>

        <div className="flex-1 bg-[#6375c510] rounded-3xl backdrop-blur-xl border border-[#ffffff10] overflow-hidden">
          {dashboardConfig.sandbox_embed_url ? (
            <iframe
              src={dashboardConfig.sandbox_embed_url}
              className="w-full h-full border-none"
              title="Dashboard"
            />
          ) : (
            <div className="p-8 overflow-auto h-full">
              <div className="mb-6">
                <span className="px-3 py-1 bg-[#6375c533] text-[#6375c5] rounded-full text-xs font-bold border border-[#6375c555]">
                  {dashboardConfig.domain.toUpperCase()}
                </span>
                <h2 className="text-4xl font-bold text-white mt-2">{dashboardConfig.selected_template}</h2>
              </div>

              {/* Simplified rendering of ui_props since we cannot execute React code string here easily */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {dashboardConfig.ui_props.products?.map((p: any, i: number) => (
                  <div key={i} className="bg-[#ffffff05] border border-[#ffffff10] rounded-2xl p-6 hover:border-[#6375c555] transition-all">
                    <img src={p.image_url || p.image} alt={p.title} className="w-full h-40 object-contain mb-4 rounded-lg" />
                    <h3 className="text-white font-semibold text-lg line-clamp-2">{p.title}</h3>
                    <p className="text-[#6375c5] font-bold text-xl mt-2">{p.price}</p>
                    {p.rating && <p className="text-[#F59E0B] text-sm">★ {p.rating} ({p.review_count} reviews)</p>}
                    <a href={p.url} target="_blank" rel="noopener noreferrer" className="inline-block mt-4 text-[#ffffff66] hover:text-white text-sm">View Store →</a>
                  </div>
                ))}

                {/* Links fallback */}
                {dashboardConfig.ui_props.links?.map((l: any, i: number) => (
                  <div key={i} className="bg-[#ffffff05] border border-[#ffffff10] rounded-2xl p-6">
                    <h3 className="text-white font-semibold">{l.title}</h3>
                    <p className="text-[#ffffff66] text-sm mt-2">{l.summary}</p>
                    <a href={l.url} target="_blank" rel="noopener noreferrer" className="inline-block mt-4 text-[#6375c5] hover:underline">Read more</a>
                  </div>
                ))}
              </div>

              {!dashboardConfig.ui_props.products && !dashboardConfig.ui_props.links && (
                <pre className="text-xs text-green-400 bg-black/50 p-4 rounded-xl overflow-auto">
                  {JSON.stringify(dashboardConfig.ui_props, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  const chartData = [
    { month: "Mon", height: 35 },
    { month: "Tue", height: 48 },
    { month: "Wed", height: 60 },
    { month: "Thu", height: 42 },
    { month: "Fri", height: 100 },
    { month: "Sat", height: 62 },
    { month: "Sun", height: 75 },
  ];

  const sidebarItems = [
    { icon: Icons.home, label: "Home", isActive: true },
    { icon: Icons.chart, label: "Analytics", isActive: false },
    { icon: Icons.search, label: "Search", isActive: false },
    { icon: Icons.calendar, label: "Calendar", isActive: false },
    { icon: Icons.settings, label: "Settings", isActive: false },
  ];

  const headerItems = [
    { icon: Icons.calendar, label: "Calendar" },
    { icon: Icons.chat, label: "Chat" },
    { icon: Icons.bell, label: "Notifications" },
  ];

  const revenueStats = [
    { value: "2.5", label: "Min" },
    { value: "8.2", label: "Max" },
    { value: "5.1", label: "Avg" },
  ];

  return (
    <div className="bg-[#050510] min-h-screen w-full overflow-hidden relative">
      {/* Background blur effects */}
      <div className="fixed top-[-200px] left-[-100px] w-[600px] h-[600px] bg-[#2020ff] rounded-full blur-[200px] opacity-30 pointer-events-none" />
      <div className="fixed bottom-[-200px] right-[-100px] w-[600px] h-[600px] bg-[#2020ff] rounded-full blur-[200px] opacity-30 pointer-events-none" />

      {/* Main layout container */}
      <div className="min-h-screen w-full flex p-4 gap-4">

        {/* Sidebar */}
        <nav className="flex flex-col w-20 items-center gap-6 py-6 px-3 bg-[#6375c520] rounded-3xl backdrop-blur-xl flex-shrink-0">
          <div className="w-10 h-10 text-[#6375c5]">
            {Icons.logo}
          </div>
          <div className="w-full h-px bg-[#ffffff20]" />
          <div className="flex flex-col items-center gap-4 flex-1">
            {sidebarItems.map((item, index) => (
              <button
                key={index}
                className={`w-12 h-12 flex items-center justify-center rounded-xl transition-colors text-[#ffffff80] ${item.isActive ? "bg-[#6375c5] text-white" : "hover:bg-[#ffffff15]"
                  }`}
                aria-label={item.label}
              >
                <div className="w-6 h-6">{item.icon}</div>
              </button>
            ))}
          </div>
        </nav>

        {/* Main content */}
        <div className="flex-1 flex flex-col gap-4 min-w-0">

          {/* Header */}
          <header className="flex items-center justify-between">
            <h1 className="font-sans font-medium text-[#ffffffcc] text-3xl lg:text-4xl">
              Browser Dashboard
            </h1>
            <div className="flex items-center gap-3">
              {headerItems.map((item, index) => (
                <button
                  key={index}
                  className="w-12 h-12 flex items-center justify-center bg-[#ffffff15] rounded-full hover:bg-[#ffffff25] transition-colors text-[#ffffff80]"
                  aria-label={item.label}
                >
                  <div className="w-5 h-5">{item.icon}</div>
                </button>
              ))}
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#6375c5] to-[#8B5CF6] flex items-center justify-center text-white font-semibold">
                U
              </div>
            </div>
          </header>

          {/* Main grid */}
          <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4">

            {/* Left column - AI Chatbot */}
            <div className="bg-[#6375c520] rounded-3xl backdrop-blur-xl p-6 flex flex-col items-center justify-center relative overflow-hidden min-h-[400px]">
              {/* Background glow */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-80 h-80 bg-[#0009ff] rounded-full blur-[150px] opacity-20 pointer-events-none" />

              <h2 className="font-sans font-medium text-[#ffffffcc] text-2xl mb-6 z-10">
                AI Chatbot
              </h2>

              {/* AI visualization */}
              <div className="relative mb-6 z-10">
                <div className="w-48 h-48 lg:w-64 lg:h-64 rounded-full border border-[#ffffff30] bg-gradient-to-br from-transparent via-[#6375c510] to-[#2574ef30] flex items-center justify-center">
                  <div className="text-6xl lg:text-8xl">🤖</div>
                </div>
                <button
                  onClick={() => setIsClusterSelectorOpen(true)}
                  className="absolute -bottom-3 left-1/2 -translate-x-1/2 px-6 py-2 rounded-full border border-[#ffffff40] hover:bg-[#ffffff15] transition-colors bg-[#6375c530]"
                >
                  <span className="font-sans font-medium text-[#ffffffcc] text-sm">
                    Chat Now
                  </span>
                </button>
              </div>

              <div className="text-center z-10">
                <p className="font-sans font-medium text-[#ffffffcc] text-xl mb-1">
                  How can I help you today?
                </p>
                <p className="font-sans text-[#ffffff60] text-sm">
                  Ask me anything or get quick insights
                </p>
              </div>
            </div>

            {/* Right column - Stats */}
            <div className="flex flex-col gap-4">

              {/* Time on Tab card */}
              <div className="bg-[#6375c520] rounded-3xl backdrop-blur-xl p-6 flex-1">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 flex items-center justify-center rounded-full border border-[#b4bcc5] text-[#b4bcc5]">
                      <div className="w-5 h-5">{Icons.wallet}</div>
                    </div>
                    <h2 className="font-sans font-semibold text-[#ffffffcc] text-xl">
                      Time on Tab
                    </h2>
                  </div>
                  <button className="w-10 h-10 flex items-center justify-center rounded-full border border-[#b4bcc580] hover:bg-[#ffffff15] transition-colors text-[#b4bcc5]">
                    <div className="w-5 h-5">{Icons.arrow}</div>
                  </button>
                </div>

                <div className="text-center mb-6">
                  <p className="font-sans font-semibold text-3xl">
                    <span className="text-[#ffffffcc]">2h </span>
                    <span className="text-[#ffffff60]">34m</span>
                  </p>
                </div>

                {/* Bar chart */}
                <div className="flex items-end justify-between gap-2 h-32">
                  {chartData.map((bar, index) => (
                    <div key={index} className="flex-1 flex flex-col items-center gap-2">
                      <div
                        className="w-full bg-[#2d3254] rounded-xl border-t border-[#7884a4] transition-all hover:bg-[#3d4264]"
                        style={{ height: `${bar.height}%` }}
                      />
                      <span className="font-sans text-[#ffffffcc] text-xs">
                        {bar.month}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Activity trend card */}
              <div className="bg-[#6375c520] rounded-3xl backdrop-blur-xl p-6 flex-1">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 flex items-center justify-center rounded-full border border-[#b4bcc5] text-[#b4bcc5]">
                      <div className="w-5 h-5">{Icons.chart}</div>
                    </div>
                    <div>
                      <h2 className="font-sans font-semibold text-[#ffffffcc] text-xl">
                        Activity trend
                      </h2>
                      <p className="font-sans text-[#ffffff80] text-sm">
                        Browsing Statistics
                      </p>
                    </div>
                  </div>
                  <button className="w-10 h-10 flex items-center justify-center rounded-full border border-[#b4bcc580] hover:bg-[#ffffff15] transition-colors text-[#b4bcc5]">
                    <div className="w-5 h-5">{Icons.arrow}</div>
                  </button>
                </div>

                {/* Stats row */}
                <div className="flex items-center gap-6 mb-4">
                  {revenueStats.map((stat, index) => (
                    <div key={index} className="flex items-baseline gap-1">
                      <span className="font-sans font-semibold text-[#ffffffcc] text-lg">
                        {stat.value}
                      </span>
                      <span className="font-sans text-[#ffffff80] text-xs">
                        {stat.label}
                      </span>
                    </div>
                  ))}
                  <div className="ml-auto flex gap-4">
                    <span className="font-sans font-semibold text-[#ffffffcc] text-sm">Today</span>
                    <span className="font-sans text-[#ffffff60] text-sm">Week</span>
                  </div>
                </div>

                {/* Activity visualization placeholder */}
                <div className="h-32 relative flex items-end justify-between gap-1">
                  {[40, 60, 35, 80, 55, 70, 45, 90, 65, 50, 75, 85].map((h, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-gradient-to-t from-[#6375c5] to-[#8B5CF6] rounded-t opacity-60"
                      style={{ height: `${h}%` }}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Cluster Selector Popup */}
      <ClusterSelector
        isOpen={isClusterSelectorOpen}
        onClose={() => setIsClusterSelectorOpen(false)}
        onDashboardGenerated={(config) => {
          setDashboardConfig(config);
          setIsClusterSelectorOpen(false);
        }}
        onDomainSelected={(result) => {
          console.log('Domain selected:', result);
        }}
      />
    </div>
  );
};