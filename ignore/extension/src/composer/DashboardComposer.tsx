import React from "react";
import type { DynamicDashboard } from "../dashboard/types";
import { SectionRenderer } from "./SectionRenderer";

const getThemeStyles = (theme: string) => {
  switch (theme?.toLowerCase()) {
    case "shopping": return "bg-gradient-to-br from-amber-950 via-slate-900 to-orange-900/40 text-amber-50";
    case "study": case "research": return "bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950/40 text-emerald-50";
    case "code": case "coding": return "bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950/40 text-indigo-50";
    case "travel": return "bg-gradient-to-br from-cyan-950 via-slate-900 to-sky-950/40 text-cyan-50";
    case "entertainment": return "bg-gradient-to-br from-purple-950 via-slate-900 to-fuchsia-950/40 text-purple-50";
    default: return "bg-gradient-to-br from-slate-950 via-slate-900 to-slate-900 text-slate-50";
  }
};

export const DashboardComposer: React.FC<{ data: DynamicDashboard }> = ({ data }) => {
  const styles = getThemeStyles(data.theme);
  
  const sections = data.sections || [];
  
  // Adaptive Layout Orchestration
  const heroIndex = sections.findIndex(s => s.type === "hero" || s.type === "hero_card");
  const heroSection = heroIndex >= 0 ? sections[heroIndex] : undefined;
  
  const remainingSections = sections.filter((_, i) => i !== heroIndex);
  const highPriority = remainingSections.filter(s => s.priority === "high");
  const otherSections = remainingSections.filter(s => s.priority !== "high");

  return (
    <div className={`min-h-screen p-4 md:p-8 ${styles} transition-colors duration-700 font-sans`}>
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-white/5 blur-[120px] mix-blend-overlay"></div>
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-black/40 blur-[120px] mix-blend-overlay"></div>
      </div>
      
      <main className="max-w-7xl mx-auto space-y-8 relative z-0">
        {heroSection && (
          <section className="w-full">
            <SectionRenderer section={heroSection} />
          </section>
        )}
        
        {highPriority.length > 0 && (
          <section className="grid gap-6 lg:grid-cols-12 items-start">
            <div className="space-y-6 lg:col-span-8">
              {highPriority.slice(0, 2).map((sec, i) => (
                <SectionRenderer key={`high-main-${i}`} section={sec} />
              ))}
            </div>
            <aside className="space-y-6 lg:col-span-4">
              {highPriority.slice(2).map((sec, i) => (
                <SectionRenderer key={`high-side-${i}`} section={sec} />
              ))}
            </aside>
          </section>
        )}

        {otherSections.length > 0 && (
          <section className="grid gap-6 md:grid-cols-2 xl:grid-cols-3 items-start">
            {otherSections.map((sec, i) => (
              <SectionRenderer key={`other-${i}`} section={sec} />
            ))}
          </section>
        )}
      </main>
    </div>
  );
};
