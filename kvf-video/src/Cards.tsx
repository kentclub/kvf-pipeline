import { AbsoluteFill, Img, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { ACCENT, Cap } from "./types";

const BG = "#0E0F0C";
const ease = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Pill: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      alignSelf: "flex-start",
      background: ACCENT,
      color: "black",
      fontFamily: "Inter",
      fontWeight: 900,
      fontSize: 44,
      letterSpacing: 2,
      padding: "10px 26px",
      borderRadius: 14,
    }}
  >
    {children}
  </div>
);

// Full dark card, or (panel) a translucent box near the top so the clip under it stays visible.
const CardFrame: React.FC<{ panel?: boolean; gap: number; children: React.ReactNode }> = ({ panel, gap, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!panel) {
    return (
      <AbsoluteFill style={{ background: BG, padding: "0 90px", justifyContent: "center", gap }}>
        {children}
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: 220,
          left: 60,
          right: 60,
          background: "rgba(14,15,12,0.82)",
          borderRadius: 40,
          padding: "48px 56px",
          display: "flex",
          flexDirection: "column",
          gap: gap * 0.6,
          opacity: interpolate(frame, [0, 0.25 * fps], [0, 1], clamp),
          translate: interpolate(frame, [0, 0.35 * fps], ["0px 40px", "0px 0px"], { ...clamp, easing: ease }),
        }}
      >
        {children}
      </div>
    </AbsoluteFill>
  );
};

const fmt = (n: number, decimals = 0) =>
  n.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });

// Meal with no clip: label + items appearing one by one.
export const MealCard: React.FC<{ label: string; items: string[]; panel?: boolean }> = ({ label, items, panel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = panel ? 0.72 : 1;
  return (
    <CardFrame panel={panel} gap={36}>
      <Pill>{label}</Pill>
      {items.map((it, i) => (
        <div
          key={it}
          style={{
            fontFamily: "Inter",
            fontWeight: 900,
            fontSize: 104 * k,
            lineHeight: 1.02,
            color: "white",
            opacity: interpolate(frame, [i * 0.45 * fps, (i * 0.45 + 0.35) * fps], [0, 1], { ...clamp, easing: ease }),
            translate: interpolate(frame, [i * 0.45 * fps, (i * 0.45 + 0.35) * fps], ["0px 40px", "0px 0px"], {
              ...clamp,
              easing: ease,
            }),
          }}
        >
          {it}
        </div>
      ))}
    </CardFrame>
  );
};

// Finds when a number is spoken in this line, relative to the line start.
const cueMs = (caps: Cap[], n: number, fallback: number) => {
  const digits = String(n);
  const hit = caps.find((c) => c.text.replace(/[^0-9]/g, "") === digits);
  return hit ? hit.startMs : fallback;
};

const Stat: React.FC<{ value: number; unit: string; label: string; atMs: number; decimals?: number; k?: number }> = ({
  value,
  unit,
  label,
  atMs,
  decimals = 0,
  k = 1,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const start = (atMs / 1000) * fps;
  const shown = interpolate(frame, [start, start + 0.6 * fps], [0, value], { ...clamp, easing: ease });
  return (
    <div
      style={{
        opacity: interpolate(frame, [start - 2, start + 4], [0, 1], clamp),
        display: "flex",
        flexDirection: "column",
        gap: 2,
      }}
    >
      <div style={{ fontFamily: "Inter", fontWeight: 900, fontSize: 150 * k, color: "white", lineHeight: 1 }}>
        {fmt(shown, decimals)}
        <span style={{ fontSize: 64 * k, color: ACCENT, marginLeft: 14 }}>{unit}</span>
      </div>
      <div style={{ fontFamily: "Inter", fontWeight: 800, fontSize: 46 * k, color: "#A7A99F", letterSpacing: 1 }}>
        {label}
      </div>
    </div>
  );
};

export const TotalsCard: React.FC<{
  kcal: number;
  protein: number;
  deficit: number;
  caps: Cap[];
  durMs: number;
  panel?: boolean;
}> = ({ kcal, protein, deficit, caps, durMs, panel }) => {
  const k = panel ? 0.72 : 1;
  return (
    <CardFrame panel={panel} gap={54}>
      <Pill>TODAY</Pill>
      <Stat k={k} value={kcal} unit="kcal" label="EATEN" atMs={cueMs(caps, kcal, durMs * 0.1)} />
      <Stat k={k} value={protein} unit="g" label="PROTEIN" atMs={cueMs(caps, protein, durMs * 0.4)} />
      <Stat k={k} value={Math.abs(deficit)} unit="kcal" label={deficit < 0 ? "OVER" : "DEFICIT"} atMs={cueMs(caps, Math.abs(deficit), durMs * 0.7)} />
    </CardFrame>
  );
};

// Overall progress toward 10% body fat.
export const ProgressCard: React.FC<{ kg: number; of: number; pct: number; panel?: boolean }> = ({ kg, of, pct, panel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = panel ? 0.72 : 1;
  const fill = interpolate(frame, [0.4 * fps, 1.6 * fps], [0, pct], { ...clamp, easing: ease });
  return (
    <CardFrame panel={panel} gap={40}>
      <Pill>FAT LOST SO FAR</Pill>
      <div style={{ fontFamily: "Inter", fontWeight: 900, fontSize: 210 * k, color: "white", lineHeight: 1 }}>
        {fmt(interpolate(frame, [0, 1.2 * fps], [0, kg], { ...clamp, easing: ease }), 2)}
        <span style={{ fontSize: 80 * k, color: ACCENT, marginLeft: 16 }}>kg</span>
      </div>
      <div style={{ height: 56 * k, borderRadius: 28, background: "#2A2C25", overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${fill}%`, minWidth: fill > 0 ? 56 * k : 0, background: ACCENT, borderRadius: 28 }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "Inter", fontWeight: 800, fontSize: 46 * k }}>
        <span style={{ color: ACCENT }}>{fmt(pct, 1)}%</span>
        <span style={{ color: "#A7A99F" }}>{fmt(of - kg, 1)} kg to go</span>
      </div>
    </CardFrame>
  );
};

// Opener inserts: "from this" (old photo) and "to this" (goal).
export const BeforeShot: React.FC<{ dir: string }> = ({ dir }) => (
  <AbsoluteFill style={{ background: BG }}>
    <Img src={staticFile(`${dir}/before.jpg`)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
    <div style={{ position: "absolute", top: 360, left: 90 }}>
      <Pill>LAST YEAR</Pill>
    </div>
  </AbsoluteFill>
);

export const GoalShot: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const [big, ...rest] = text.split(" ");
  return (
    <AbsoluteFill style={{ background: ACCENT, justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          fontFamily: "Inter",
          fontWeight: 900,
          color: "black",
          textAlign: "center",
          lineHeight: 0.95,
          scale: interpolate(frame, [0, 0.3 * fps], [0.85, 1], { ...clamp, easing: ease }),
        }}
      >
        <div style={{ fontSize: 330 }}>{big}</div>
        <div style={{ fontSize: 120 }}>{rest.join(" ")}</div>
      </div>
    </AbsoluteFill>
  );
};
const RED = "#FF6B5A";
const appear = (frame: number, fps: number, at: number) => ({
  opacity: interpolate(frame, [at * fps, (at + 0.3) * fps], [0, 1], clamp),
  translate: interpolate(frame, [at * fps, (at + 0.35) * fps], ["0px 30px", "0px 0px"], { ...clamp, easing: ease }),
});

// Small weekday tag on a clip (sits under the small DAY badge).
export const DayTag: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 200, left: 80, ...appear(frame, fps, 0) }}>
      <div
        style={{
          background: "rgba(14,15,12,0.85)",
          color: "white",
          fontFamily: "Inter",
          fontWeight: 900,
          fontSize: 54,
          letterSpacing: 3,
          padding: "8px 24px",
          borderRadius: 14,
          border: `4px solid ${ACCENT}`,
        }}
      >
        {text}
      </div>
    </div>
  );
};

// Daily deficit bars for a week: lime up = deficit, red down = over.
export const WeekCard: React.FC<{ days: { d: string; v: number }[]; panel?: boolean }> = ({ days, panel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const max = Math.max(...days.map((x) => Math.abs(x.v)));
  const H = 230;
  return (
    <CardFrame panel={panel} gap={40}>
      <Pill>THE WEEK</Pill>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "stretch", height: H * 2 + 20 }}>
        {days.map((x, i) => {
          const g = interpolate(frame, [(0.1 + i * 0.07) * fps, (0.5 + i * 0.07) * fps], [0, 1], { ...clamp, easing: ease });
          const h = (Math.abs(x.v) / max) * H * g;
          const pos = x.v >= 0;
          return (
            <div key={x.d} style={{ width: 96, display: "flex", flexDirection: "column", alignItems: "center" }}>
              <div style={{ height: H, display: "flex", alignItems: "flex-end" }}>
                {pos ? <div style={{ width: 84, height: h, background: ACCENT, borderRadius: "14px 14px 0 0" }} /> : null}
              </div>
              <div style={{ width: 96, height: 6, background: "#5A5C55" }} />
              <div style={{ height: H, display: "flex", alignItems: "flex-start" }}>
                {!pos ? <div style={{ width: 84, height: h, background: RED, borderRadius: "0 0 14px 14px" }} /> : null}
              </div>
              <div style={{ fontFamily: "Inter", fontWeight: 900, fontSize: 36, color: pos ? "white" : RED, marginTop: 10 }}>{x.d}</div>
            </div>
          );
        })}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "Inter", fontWeight: 800, fontSize: 40 }}>
        <span style={{ color: ACCENT }}>DEFICIT</span>
        <span style={{ color: RED }}>OVER</span>
      </div>
    </CardFrame>
  );
};

// Week bottom line: saved vs lost vs net.
export const BalanceCard: React.FC<{ saved: number; savedLabel: string; lost: number; lostLabel: string; net: number; panel?: boolean }> = ({
  saved, savedLabel, lost, lostLabel, net, panel,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = panel ? 0.8 : 1;
  const Row: React.FC<{ at: number; label: string; value: number; color: string; sign: string; big?: boolean }> = ({ at, label, value, color, sign, big }) => (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", ...appear(frame, fps, at) }}>
      <span style={{ fontFamily: "Inter", fontWeight: 800, fontSize: (big ? 52 : 46) * k, color: big ? "white" : "#A7A99F" }}>{label}</span>
      <span style={{ fontFamily: "Inter", fontWeight: 900, fontSize: (big ? 110 : 84) * k, color }}>
        {sign}
        {fmt(interpolate(frame, [at * fps, (at + 0.6) * fps], [0, value], { ...clamp, easing: ease }))}
        <span style={{ fontSize: 40 * k, marginLeft: 8 }}>kcal</span>
      </span>
    </div>
  );
  return (
    <CardFrame panel={panel} gap={34}>
      <Pill>THE WEEK</Pill>
      <Row at={0.2} label={savedLabel} value={saved} color={ACCENT} sign="+" />
      <Row at={1.0} label={lostLabel} value={lost} color={RED} sign="-" />
      <div style={{ height: 5, background: "#5A5C55", ...appear(frame, fps, 1.8) }} />
      <Row at={1.9} label="WEEK DEFICIT" value={net} color={ACCENT} sign="" big />
    </CardFrame>
  );
};

// Scan comparison rows; each row appears when its first word is spoken (fallback: staggered).
export const ScanCard: React.FC<{ label: string; rows: { k: string; a: string; b: string }[]; caps: Cap[]; durMs: number; panel?: boolean }> = ({
  label, rows, caps, durMs, panel,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = panel ? 0.8 : 1;
  const cue = (word: string, fb: number) => {
    const hit = caps.find((c) => c.text.trim().toLowerCase().replace(/[^a-z]/g, "") === word);
    return (hit ? hit.startMs : fb) / 1000;
  };
  const ats = [cue("weight", durMs * 0.3), cue("mass", durMs * 0.45) - 0.3, cue("percentage", durMs * 0.65) - 0.3];
  return (
    <CardFrame panel={panel} gap={36}>
      <Pill>{label}</Pill>
      {rows.map((r, i) => {
        const at = Math.max(0.15, ats[i] ?? 0.3 + i * 0.5);
        return (
          <div key={r.k} style={{ display: "flex", flexDirection: "column", gap: 4, ...appear(frame, fps, at) }}>
            <span style={{ fontFamily: "Inter", fontWeight: 800, fontSize: 42 * k, color: "#A7A99F", letterSpacing: 1 }}>{r.k}</span>
            <span style={{ fontFamily: "Inter", fontWeight: 900, fontSize: 96 * k, color: "white", lineHeight: 1 }}>
              <span style={{ color: "#A7A99F" }}>{r.a}</span>
              <span style={{ color: ACCENT, margin: "0 18px" }}>{"\u2192"}</span>
              {r.b}
            </span>
          </div>
        );
      })}
    </CardFrame>
  );
};