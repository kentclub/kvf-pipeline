import { AbsoluteFill, Easing, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Audio, Video } from "@remotion/media";
import { Captions } from "./Captions";
import { BalanceCard, BeforeShot, DayTag, GoalShot, MealCard, ProgressCard, ScanCard, TotalsCard, WeekCard } from "./Cards";
import { ACCENT, DayProps, TAIL_MS } from "./types";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// One clip filling the frame, with a slow push-in. Slowed down if shorter than its slot.
const Clip: React.FC<{ dir: string; name: string; clipSec: number; slotFrames: number; start?: number }> = ({
  dir,
  name,
  clipSec,
  slotFrames,
  start = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rate = Math.min(1, ((clipSec - start) * fps - 2) / slotFrames);
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "black" }}>
      <Video
        src={staticFile(`${dir}/${name}.mp4`)}
        muted
        trimBefore={start > 0 ? Math.round(start * fps) : undefined}
        playbackRate={rate}
        objectFit="cover"
        style={{
          width: "100%",
          height: "100%",
          scale: interpolate(frame, [0, slotFrames], [1, 1.07], clamp),
        }}
      />
    </AbsoluteFill>
  );
};

const DayBadge: React.FC<{ day: number; big: boolean }> = ({ day, big }) => (
  <div
    style={{
      position: "absolute",
      top: big ? 170 : 110,
      left: big ? 0 : 80,
      right: big ? 0 : undefined,
      display: "flex",
      justifyContent: big ? "center" : "flex-start",
    }}
  >
    <div
      style={{
        background: ACCENT,
        color: "black",
        fontFamily: "Inter",
        fontWeight: 900,
        fontSize: big ? 120 : 46,
        letterSpacing: big ? 4 : 2,
        padding: big ? "8px 40px" : "8px 22px",
        borderRadius: big ? 26 : 14,
      }}
    >
      DAY {day}
    </div>
  </div>
);

export const DayVideo: React.FC<DayProps> = (p) => {
  const { fps } = useVideoConfig();
  const f = (ms: number) => Math.round((ms / 1000) * fps);
  // No filmed opener: the first voiceover line ("Day N of ...") becomes the opener with the big badge.
  const op = p.opener;
  const openF = op ? f(op.durationMs) : 0;
  const [this1, this2] = op ? op.thisMs : [];
  const aiCap = op?.captions.find((c) => /^ai$/i.test(c.text.trim()));
  const goalEnd = aiCap ? aiCap.startMs : (this2 ?? 0) + 700;
  const firstLineEnd = f(p.vo.lines[0].endMs);

  return (
    <AbsoluteFill style={{ background: "black" }}>
      {/* Opener: Kent on camera with his own audio */}
      {op ? (
      <Sequence durationInFrames={openF}>
        <Video src={staticFile(`${p.dir}/${op.src}`)} trimBefore={op.trimMs ? f(op.trimMs) : undefined} objectFit="cover" style={{ width: "100%", height: "100%" }} />
        {this1 !== undefined && this2 !== undefined ? (
          <>
            <Sequence from={f(this1)} durationInFrames={f(this2) - f(this1)}>
              <BeforeShot dir={p.dir} />
            </Sequence>
            <Sequence from={f(this2)} durationInFrames={f(goalEnd) - f(this2)}>
              <GoalShot text={p.goalText} />
            </Sequence>
          </>
        ) : null}
        <DayBadge day={p.day} big />
        <Captions caps={op.captions} />
      </Sequence>
      ) : null}

      {/* Voiceover part */}
      <Sequence from={openF}>
        <Audio src={staticFile(`${p.dir}/${p.vo.src}`)} />
        {p.lines.map((line, i) => {
          const seg = p.vo.lines[i];
          const from = f(seg.startMs);
          const isLast = i === p.lines.length - 1;
          const dur = Math.max(1, f(seg.endMs + (isLast ? TAIL_MS : 0)) - from);
          const v = line.visual;
          const caps = p.vo.captions
            .filter((c) => c.line === i)
            .map((c) => ({ ...c, startMs: c.startMs - seg.startMs, endMs: c.endMs - seg.startMs }));
          let body: React.ReactNode = null;
          if ("clip" in v) {
            body = (
              <>
                <Clip dir={p.dir} name={v.clip} start={v.start} clipSec={p.clips[v.clip]} slotFrames={dur} />
                {v.tag ? <DayTag text={v.tag} /> : null}
              </>
            );
          } else if ("clips" in v) {
            const part = Math.floor(dur / v.clips.length);
            body = v.clips.map((c, k) => (
              <Sequence key={c + k} from={k * part} durationInFrames={k === v.clips.length - 1 ? dur - k * part : part}>
                <Clip dir={p.dir} name={c} start={v.starts?.[k]} clipSec={p.clips[c]} slotFrames={part} />
                {v.tags?.[k] ? <DayTag text={v.tags[k]} /> : null}
              </Sequence>
            ));
          } else {
            const panel = Boolean(v.over);
            const under = v.over ? (
              <Clip dir={p.dir} name={v.over.clip} start={v.over.start} clipSec={p.clips[v.over.clip]} slotFrames={dur} />
            ) : null;
            const card =
              v.card === "meal" ? (
                <MealCard label={v.label} items={v.items} panel={panel} />
              ) : v.card === "totals" ? (
                <TotalsCard kcal={v.kcal} protein={v.protein} deficit={v.deficit} caps={caps} durMs={seg.endMs - seg.startMs} panel={panel} />
              ) : v.card === "week" ? (
                <WeekCard days={v.days} panel={panel} />
              ) : v.card === "balance" ? (
                <BalanceCard saved={v.saved} savedLabel={v.savedLabel} lost={v.lost} lostLabel={v.lostLabel} net={v.net} panel={panel} />
              ) : v.card === "scan" ? (
                <ScanCard label={v.label} rows={v.rows} caps={caps} durMs={seg.endMs - seg.startMs} panel={panel} />
              ) : (
                <ProgressCard kg={v.kg} of={v.of} pct={v.pct} panel={panel} />
              );
            body = (
              <>
                {under}
                {card}
              </>
            );
          }
          // Captions on every line, number cards included: the spoken explanation must always be readable.
          return (
            <Sequence key={i} from={from} durationInFrames={dur} name={`Line ${i + 1}`}>
              {body}
              <Captions caps={caps} />
            </Sequence>
          );
        })}
        {op ? (
          <DayBadge day={p.day} big={false} />
        ) : (
          <>
            <Sequence durationInFrames={firstLineEnd}>
              <DayBadge day={p.day} big />
            </Sequence>
            <Sequence from={firstLineEnd}>
              <DayBadge day={p.day} big={false} />
            </Sequence>
          </>
        )}
      </Sequence>
    </AbsoluteFill>
  );
};

export const totalFrames = (p: DayProps, fps: number) =>
  Math.round((((p.opener?.durationMs ?? 0) + p.vo.durationMs + TAIL_MS) / 1000) * fps);

export const fadeOut = Easing.linear;