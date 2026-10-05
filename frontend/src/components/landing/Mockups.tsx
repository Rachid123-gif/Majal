import type { FeatureId } from "@/content/features";
import type { Locale } from "@/content/types";

/*
 * Illustrative screen mockups. They contain NO figures on purpose: they show the kind of
 * screen, not data. They will be replaced by real screenshots as the stages are delivered.
 */

const LABELS = {
  fr: {
    source: "Source · date",
    attention: "Point d'attention",
    verified: "Chiffres vérifiés",
    fictive: "Fictif",
    cite: "Document · page",
  },
  ar: {
    source: "المصدر · التاريخ",
    attention: "نقطة انتباه",
    verified: "أرقام متحقَّق منها",
    fictive: "افتراضي",
    cite: "الوثيقة · الصفحة",
  },
};
type Labels = (typeof LABELS)["fr"];

const SEQ = ["#e8efe9", "#bcd3cc", "#7fb0a7", "#3f8580", "#12545a", "#12343b"];

function Frame({ children, title }: { children: React.ReactNode; title?: string }) {
  return (
    <div className="mockup-frame border-petrol/10 overflow-hidden rounded-xl border bg-white shadow-[0_30px_60px_-30px_rgba(18,52,59,0.45)]">
      <div className="border-petrol/10 bg-cream/70 flex items-center gap-1.5 border-b px-3 py-2">
        <span className="bg-petrol/15 h-2 w-2 rounded-full" />
        <span className="bg-petrol/15 h-2 w-2 rounded-full" />
        <span className="bg-petrol/15 h-2 w-2 rounded-full" />
        {title && <span className="text-slate ms-3 truncate text-[11px]">{title}</span>}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function Lines({ widths, className = "bg-petrol/10" }: { widths: number[]; className?: string }) {
  return (
    <div className="space-y-2">
      {widths.map((w, i) => (
        <div key={i} className={`h-2 rounded-full ${className}`} style={{ width: `${w}%` }} />
      ))}
    </div>
  );
}

function DiagnosticMock({ l }: { l: Labels }) {
  // Abstract tessellation, not real boundaries.
  const cells = [
    [0, 0, 2],
    [1, 0, 4],
    [2, 0, 3],
    [3, 0, 1],
    [0, 1, 5],
    [1, 1, 3],
    [2, 1, 2],
    [3, 1, 4],
    [0, 2, 1],
    [1, 2, 2],
    [2, 2, 5],
    [3, 2, 3],
  ];
  return (
    <Frame>
      <div className="flex gap-4">
        <svg viewBox="0 0 220 170" className="w-2/3" aria-hidden>
          {cells.map(([cx, cy, v], i) => {
            const x = 20 + cx * 48 + (cy % 2) * 24;
            const y = 18 + cy * 46;
            return (
              <polygon
                key={i}
                points={`${x},${y + 12} ${x + 22},${y} ${x + 44},${y + 12} ${x + 44},${y + 38} ${x + 22},${y + 50} ${x},${y + 38}`}
                fill={SEQ[v]}
                stroke="#fff"
                strokeWidth={2}
                className="mock-cell"
                style={{ animationDelay: `${i * 60}ms` }}
              />
            );
          })}
        </svg>
        <div className="flex w-1/3 flex-col justify-center gap-2">
          {SEQ.slice(1).map((c) => (
            <div key={c} className="flex items-center gap-2">
              <span className="h-3 w-5 rounded-sm" style={{ background: c }} />
              <span className="bg-petrol/10 h-1.5 flex-1 rounded-full" />
            </div>
          ))}
          <span className="border-petrol/20 text-petrol mt-2 w-fit rounded-full border px-2 py-0.5 text-[10px]">
            {l.source}
          </span>
        </div>
      </div>
    </Frame>
  );
}

function CommuneMock({ l }: { l: Labels }) {
  return (
    <Frame>
      <Lines widths={[45]} className="bg-petrol/30" />
      <div className="mt-4 grid grid-cols-2 gap-3">
        {[70, 40, 85, 25].map((w, i) => (
          <div key={i} className="border-petrol/10 rounded-lg border p-3">
            <Lines widths={[60]} />
            <div className="bg-cream mt-3 h-2 rounded-full">
              <div
                className={`mock-bar h-2 rounded-full ${i === 3 ? "bg-terracotta" : "bg-petrol/70"}`}
                style={{ width: `${w}%` }}
              />
            </div>
          </div>
        ))}
      </div>
      <div className="bg-terracotta/10 text-terracotta mt-3 flex items-center gap-2 rounded-lg px-3 py-2 text-[11px] font-medium">
        <span aria-hidden>▲</span> {l.attention}
      </div>
    </Frame>
  );
}

function Fact({ id }: { id: string }) {
  return <span className="bg-petrol/10 text-petrol rounded px-1 font-mono text-[10px]">{id}</span>;
}

function ReportMock({ l }: { l: Labels }) {
  return (
    <Frame>
      <div className="mx-auto max-w-[85%] space-y-3 bg-white">
        <Lines widths={[55]} className="bg-petrol/35" />
        <p className="text-slate text-[11px] leading-6">
          <span className="bg-petrol/10 inline-block h-2 w-24 rounded-full align-middle" />{" "}
          <Fact id="{{F012}}" />{" "}
          <span className="bg-petrol/10 inline-block h-2 w-16 rounded-full align-middle" />{" "}
          <span className="bg-petrol/10 inline-block h-2 w-20 rounded-full align-middle" />{" "}
          <Fact id="{{F027}}" />{" "}
          <span className="bg-petrol/10 inline-block h-2 w-28 rounded-full align-middle" />
        </p>
        <Lines widths={[92, 80, 88, 60]} />
        <div className="flex items-center justify-between pt-1">
          <span className="text-petrol flex items-center gap-1 text-[11px] font-medium">
            <span aria-hidden>✓</span> {l.verified}
          </span>
          <span className="flex gap-1">
            <span className="border-petrol/20 rounded border px-1.5 text-[10px]">DOCX</span>
            <span className="border-petrol/20 rounded border px-1.5 text-[10px]">PDF</span>
          </span>
        </div>
      </div>
    </Frame>
  );
}

function CitizensMock({ l }: { l: Labels }) {
  const bubbles = [
    { w: "w-3/4", dir: "ltr" as const, tone: "bg-cream" },
    { w: "w-2/3", dir: "rtl" as const, tone: "bg-petrol/5" },
    { w: "w-1/2", dir: "ltr" as const, tone: "bg-cream" },
  ];
  return (
    <Frame>
      <div className="grid grid-cols-5 gap-4">
        <div className="col-span-3 space-y-2">
          {bubbles.map((b, i) => (
            <div key={i} dir={b.dir} className={`${b.w} ${b.tone} rounded-2xl px-3 py-2`}>
              <Lines widths={[90, 60]} />
            </div>
          ))}
        </div>
        <div className="col-span-2 flex flex-col justify-center gap-2">
          {[90, 70, 55, 35].map((w, i) => (
            <div key={i} className="bg-cream h-2.5 rounded-full">
              <div
                className="mock-bar bg-petrol/70 h-2.5 rounded-full"
                style={{ width: `${w}%` }}
              />
            </div>
          ))}
          <span className="bg-terracotta/10 text-terracotta mt-1 w-fit rounded-full px-2 py-0.5 text-[10px] font-medium">
            {l.fictive}
          </span>
        </div>
      </div>
    </Frame>
  );
}

function DataNeedsMock() {
  return (
    <Frame>
      <div className="space-y-3">
        {[80, 35, 55, 20].map((w, i) => (
          <div key={i} className="flex items-center gap-3">
            <span className="bg-petrol/15 h-2 w-16 rounded-full" />
            <div className="bg-cream h-3 flex-1 rounded-full">
              <div className="mock-bar bg-petrol/70 h-3 rounded-full" style={{ width: `${w}%` }} />
            </div>
          </div>
        ))}
      </div>
      <div className="border-petrol/15 mt-4 flex items-center gap-3 rounded-lg border border-dashed p-3">
        <span className="bg-petrol text-cream grid h-9 w-7 place-items-center rounded-sm text-[9px]">
          DOC
        </span>
        <Lines widths={[70, 45]} />
      </div>
    </Frame>
  );
}

function AssistantMock({ l }: { l: Labels }) {
  return (
    <Frame>
      <div className="space-y-3">
        <div className="bg-petrol text-cream ms-auto w-2/3 rounded-2xl rounded-ee-sm px-3 py-2">
          <Lines widths={[85, 50]} className="bg-cream/40" />
        </div>
        <div className="bg-cream w-3/4 rounded-2xl rounded-es-sm px-3 py-2">
          <Lines widths={[95, 80, 60]} />
          <span className="border-petrol/20 text-petrol mt-2 inline-block rounded border px-1.5 text-[10px]">
            {l.cite}
          </span>
        </div>
      </div>
    </Frame>
  );
}

function PresentationMock() {
  return (
    <div className="mockup-frame bg-petrol rounded-xl p-5 shadow-[0_30px_60px_-30px_rgba(18,52,59,0.6)]">
      <div className="border-cream/15 flex aspect-video flex-col justify-between rounded-lg border p-4">
        <span className="bg-terracotta-light/30 h-1.5 w-20 rounded-full" />
        <div className="space-y-2">
          <div className="bg-cream/80 h-4 w-2/3 rounded-full" />
          <div className="bg-cream/30 h-2 w-1/2 rounded-full" />
        </div>
        <div className="flex justify-end gap-1.5">
          {["←", "→"].map((k) => (
            <kbd key={k} className="border-cream/30 text-cream rounded border px-1.5 text-[11px]">
              {k}
            </kbd>
          ))}
        </div>
      </div>
    </div>
  );
}

const MOCKUPS: Record<FeatureId, (props: { l: Labels }) => React.ReactElement> = {
  diagnostic: DiagnosticMock,
  commune: CommuneMock,
  report: ReportMock,
  citizens: CitizensMock,
  dataNeeds: DataNeedsMock,
  assistant: AssistantMock,
  presentation: PresentationMock,
};

export function FeatureMockup({ id, locale }: { id: FeatureId; locale: Locale }) {
  const Mock = MOCKUPS[id];
  return (
    <div aria-hidden>
      <Mock l={LABELS[locale]} />
    </div>
  );
}
