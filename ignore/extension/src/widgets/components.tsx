import React, { memo } from "react";
import type { DashboardWidgetSchema } from "./types";

const shell = "rounded-3xl border border-white/5 bg-white/[0.02] p-5 shadow-[inset_0_0_20px_rgba(255,255,255,0.02),0_8px_32px_rgba(0,0,0,0.4)] backdrop-blur-xl relative overflow-hidden";
const LoadingState = () => <div className="h-20 animate-pulse rounded-2xl bg-white/5" />;
const ErrorState = ({ message }: { message: string }) => <div className="rounded-2xl bg-rose-500/10 p-4 text-rose-200 border border-rose-500/20">{message}</div>;
const EmptyState = () => <div className="rounded-2xl bg-white/5 p-4 text-slate-400 text-sm text-center">No content available</div>;

function safeString(input: unknown, fallback = ""): string {
  return typeof input === "string" ? input : fallback;
}

function getFallbackImage(title: string) {
  const hash = title.split("").reduce((a, b) => { a = ((a << 5) - a) + b.charCodeAt(0); return a & a }, 0);
  const sig = Math.abs(hash) % 1000;
  return `https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=800&auto=format&fit=crop&sig=${sig}`;
}

function Frame({ widget, children, noPadding = false, className = "" }: { widget: DashboardWidgetSchema; children: React.ReactNode; noPadding?: boolean; className?: string }) {
  return (
    <section className={`${shell} ${noPadding ? "p-0" : ""} ${className} transition-all duration-500 hover:bg-white/[0.04] hover:shadow-[inset_0_0_20px_rgba(255,255,255,0.05),0_8px_32px_rgba(0,0,0,0.5)]`}>
      <div className="relative z-10">
        {(widget.title || widget.subtitle) && !noPadding && (
          <div className="mb-4">
            {widget.title && <h3 className="text-xl font-bold tracking-tight text-white/95">{widget.title}</h3>}
            {widget.subtitle && <p className="mt-1 text-sm text-white/60">{widget.subtitle}</p>}
          </div>
        )}
        {widget.loading ? <LoadingState /> : widget.error ? <ErrorState message={widget.error} /> : widget.empty ? <EmptyState /> : children}
      </div>
    </section>
  );
}

function ActionButtons({ items }: { items: unknown[] }) {
  if (!items?.length) return null;
  return (
    <div className="flex flex-wrap gap-2 mt-4">
      {items.map((item, i) => {
        const title = typeof item === "string" ? item : (item as any)?.title || "Action";
        const val = (item as any)?.value;
        const display = typeof item === "object" ? `${title}${val ? `: ${val}` : ''}` : title;
        return (
          <button key={i} className="px-4 py-2 rounded-full bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-colors border border-white/5 shadow-sm backdrop-blur-md">
            {display}
          </button>
        );
      })}
    </div>
  );
}

export const HeroCard = memo(({ widget }: { widget: DashboardWidgetSchema }) => (
  <div className="relative overflow-hidden rounded-[2.5rem] bg-gradient-to-br from-indigo-500/30 via-purple-500/20 to-fuchsia-500/30 p-1 md:p-[2px]">
    <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay"></div>
    <div className="relative h-full w-full rounded-[2.4rem] bg-slate-950/60 backdrop-blur-3xl p-8 md:p-12 flex flex-col justify-center min-h-[300px]">
      <div className="max-w-3xl">
        <div className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 mb-6 shadow-inner text-xs font-medium text-cyan-200">
          <span className="flex h-2 w-2 rounded-full bg-cyan-400 mr-2 animate-pulse"></span> AI Workspace
        </div>
        <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-white/90 to-white/60">
          {widget.title || "Intelligence Center"}
        </h2>
        <p className="mt-4 text-lg text-slate-300 leading-relaxed max-w-2xl font-light">
          {widget.subtitle || "Context-aware multimodal dashboard synthesized for your current session."}
        </p>
        <ActionButtons items={widget.items || []} />
      </div>
    </div>
  </div>
));

function GenericItems({ widget }: { widget: DashboardWidgetSchema }) {
  if (!widget.items?.length) return <EmptyState />;
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {widget.items.map((item, i) => {
        const rec = (item && typeof item === "object") ? (item as Record<string, unknown>) : { value: item };
        const title = safeString(rec.title, "Resource");
        const image = safeString(rec.image);
        const description = safeString(rec.description);
        const link = safeString(rec.link);
        
        return (
          <article key={i} className="group flex flex-col rounded-2xl border border-white/5 bg-white/[0.03] overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:bg-white/[0.06] hover:shadow-xl">
            {image ? (
              <div className="aspect-[4/3] w-full overflow-hidden bg-black/20">
                <img loading="lazy" src={image} alt={title} className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" />
              </div>
            ) : null}
            <div className="flex flex-col flex-1 p-4">
              <h4 className="text-base font-semibold text-white/90 line-clamp-1">{title}</h4>
              {description && <p className="mt-1.5 text-xs text-white/50 line-clamp-2 leading-relaxed flex-1">{description}</p>}
              {link && (
                <div className="mt-4 pt-3 border-t border-white/5">
                  <a href={link} target="_blank" rel="noreferrer" className="inline-flex items-center text-xs font-medium text-cyan-400 hover:text-cyan-300 transition-colors">
                    View source <span className="ml-1 opacity-50">&rarr;</span>
                  </a>
                </div>
              )}
            </div>
          </article>
        );
      })}
    </div>
  );
}

export const MediaCarousel = memo(({ widget }: { widget: DashboardWidgetSchema }) => {
  if (!widget.items?.length) return null;
  return (
    <Frame widget={widget} noPadding>
      <div className="p-5 pb-2">
        <h3 className="text-xl font-bold text-white/95">{widget.title || "Gallery"}</h3>
        {widget.subtitle && <p className="text-sm text-white/60 mt-1">{widget.subtitle}</p>}
      </div>
      <div className="flex snap-x snap-mandatory gap-4 overflow-x-auto p-5 pt-2 pb-6 scrollbar-hide">
        {widget.items.map((item, i) => {
          const rec = (item && typeof item === "object") ? (item as Record<string, unknown>) : { title: String(item) };
          const title = safeString(rec.title, "Media");
          const image = safeString(rec.image, getFallbackImage(title));
          return (
            <article key={i} className="group relative min-w-[260px] md:min-w-[320px] snap-center overflow-hidden rounded-2xl bg-black/40 cursor-pointer shadow-lg">
              <div className="aspect-[16/9] w-full overflow-hidden">
                <img loading="lazy" src={image} alt={title} className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-110 opacity-80 group-hover:opacity-100" />
              </div>
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent flex items-end p-4">
                <h4 className="text-sm font-medium text-white shadow-black drop-shadow-md line-clamp-2">{title}</h4>
              </div>
            </article>
          );
        })}
      </div>
    </Frame>
  );
});

export const RecommendationSlider = memo(({ widget }: { widget: DashboardWidgetSchema }) => {
  if (!widget.items?.length) return null;
  return (
    <Frame widget={widget}>
      <div className="flex flex-col space-y-3">
        {widget.items.map((item, i) => {
          const rec = (item && typeof item === "object") ? (item as Record<string, unknown>) : { title: String(item) };
          const title = safeString(rec.title, "Recommendation");
          const desc = safeString(rec.description);
          const link = safeString(rec.link);
          const image = safeString(rec.image);
          
          return (
            <a key={i} href={link || "#"} target={link ? "_blank" : undefined} rel="noreferrer" className="flex items-center gap-4 rounded-2xl bg-white/5 p-3 hover:bg-white/10 transition-colors border border-transparent hover:border-white/10">
              {image ? (
                <div className="h-12 w-12 rounded-xl overflow-hidden shrink-0 bg-black/20">
                  <img src={image} alt="" className="h-full w-full object-cover" />
                </div>
              ) : (
                <div className="h-12 w-12 rounded-xl shrink-0 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center text-indigo-300">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
                </div>
              )}
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-semibold text-white/90 truncate">{title}</h4>
                {desc && <p className="text-xs text-white/50 truncate mt-0.5">{desc}</p>}
              </div>
            </a>
          );
        })}
      </div>
    </Frame>
  );
});

export const ActionList = memo(({ widget }: { widget: DashboardWidgetSchema }) => (
  <Frame widget={widget} className="bg-gradient-to-br from-blue-900/10 to-indigo-900/10 border-blue-500/10">
    <ActionButtons items={widget.items || []} />
  </Frame>
));

export const ProductGrid = memo(({ widget }: { widget: DashboardWidgetSchema }) => <Frame widget={widget}><GenericItems widget={widget} /></Frame>);
export const FlashcardDeck = memo(({ widget }: { widget: DashboardWidgetSchema }) => <Frame widget={widget}><GenericItems widget={widget} /></Frame>);
export const QuizWidget = memo(({ widget }: { widget: DashboardWidgetSchema }) => <Frame widget={widget}><GenericItems widget={widget} /></Frame>);
export const TimelineWidget = memo(({ widget }: { widget: DashboardWidgetSchema }) => <Frame widget={widget}><GenericItems widget={widget} /></Frame>);
export const ResearchPaperCard = memo(({ widget }: { widget: DashboardWidgetSchema }) => <Frame widget={widget}><GenericItems widget={widget} /></Frame>);
export const NewsCard = memo(({ widget }: { widget: DashboardWidgetSchema }) => <Frame widget={widget}><GenericItems widget={widget} /></Frame>);

export const StatsPanel = memo(({ widget }: { widget: DashboardWidgetSchema }) => (
  <Frame widget={widget}>
    <div className="grid grid-cols-2 gap-3">
      {(widget.items || []).map((i, idx) => { 
        const rec = (i && typeof i === 'object') ? (i as Record<string, unknown>) : { title: 'Metric', value: String(i) }; 
        return (
          <div key={idx} className="rounded-2xl bg-white/[0.03] p-4 border border-white/5 flex flex-col justify-center items-center text-center">
            <p className="text-xs font-medium text-white/50 uppercase tracking-wider mb-1">{safeString(rec.title, "Stat")}</p>
            <p className="text-2xl font-bold text-white tracking-tight">{safeString(rec.value, "0")}</p>
          </div>
        ); 
      })}
    </div>
  </Frame>
));

export const MarkdownPreview = memo(({ widget }: { widget: DashboardWidgetSchema }) => (
  <Frame widget={widget}>
    <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-black/40 prose-pre:border prose-pre:border-white/10 prose-headings:font-bold">
      <div dangerouslySetInnerHTML={{ __html: safeString(widget.data?.markdown || widget.subtitle || "").replace(/\n/g, "<br/>") }} />
    </div>
  </Frame>
));

export const ComparisonTable = memo(({ widget }: { widget: DashboardWidgetSchema }) => (
  <Frame widget={widget}>
    <div className="overflow-hidden rounded-xl border border-white/10">
      <table className="w-full text-sm text-left">
        <tbody className="divide-y divide-white/5">
          {(widget.items || []).map((i, idx) => { 
            const rec = (i && typeof i === 'object') ? (i as Record<string, unknown>) : { title: 'Property', value: String(i) }; 
            return (
              <tr key={idx} className="hover:bg-white/5 transition-colors">
                <td className="py-3 px-4 font-medium text-white/80 w-1/3 bg-black/10">{safeString(rec.title)}</td>
                <td className="py-3 px-4 text-white/60">{safeString(rec.description ?? rec.value)}</td>
              </tr>
            ); 
          })}
        </tbody>
      </table>
    </div>
  </Frame>
));

export const AudioPlayer = memo(({ widget }: { widget: DashboardWidgetSchema }) => <Frame widget={widget}><EmptyState /></Frame>);
export const VideoEmbed = memo(({ widget }: { widget: DashboardWidgetSchema }) => <Frame widget={widget}><EmptyState /></Frame>);
export const MapWidget = memo(({ widget }: { widget: DashboardWidgetSchema }) => <Frame widget={widget}><div className="h-64 rounded-2xl bg-black/20 overflow-hidden relative"><div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cartographer.png')] opacity-20" /><div className="absolute inset-0 flex items-center justify-center text-white/30 text-sm font-medium tracking-widest uppercase">Map Visualization</div></div></Frame>);
export const TrendChart = memo(({ widget }: { widget: DashboardWidgetSchema }) => <Frame widget={widget}><div className="h-48 rounded-2xl bg-gradient-to-t from-cyan-500/10 to-transparent border border-cyan-500/20 relative overflow-hidden"><div className="absolute bottom-0 left-0 right-0 h-1/2 bg-gradient-to-t from-cyan-500/20 to-transparent blur-xl" /><div className="absolute inset-0 flex items-center justify-center text-cyan-500/50 text-sm">Trend Data</div></div></Frame>);
export const CalendarWidget = memo(({ widget }: { widget: DashboardWidgetSchema }) => <Frame widget={widget}><EmptyState /></Frame>);
export const TabClusterMap = memo(({ widget }: { widget: DashboardWidgetSchema }) => <Frame widget={widget}><EmptyState /></Frame>);
export const EmbeddedPreview = memo(({ widget }: { widget: DashboardWidgetSchema }) => <Frame widget={widget}><EmptyState /></Frame>);

export const FallbackWidget = memo(({ widget }: { widget: DashboardWidgetSchema }) => null);
