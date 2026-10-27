import { useMemo } from "react";
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import { createTikTokStyleCaptions } from "@remotion/captions";
import type { Caption, TikTokPage } from "@remotion/captions";
import { ACCENT, Cap } from "./types";

const SWITCH_MS = 900;

const Page: React.FC<{ page: TikTokPage }> = ({ page }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const nowMs = page.startMs + (frame / fps) * 1000;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", top: 1290 }}>
      <div
        style={{
          fontFamily: "Inter",
          fontWeight: 900,
          fontSize: 82,
          lineHeight: 1.1,
          textAlign: "center",
          whiteSpace: "pre-wrap",
          maxWidth: 860,
          textTransform: "uppercase",
          color: "white",
          WebkitTextStroke: "12px black",
          wordSpacing: 14,
          paintOrder: "stroke fill",
          textShadow: "0 6px 18px rgba(0,0,0,0.45)",
        }}
      >
        {page.tokens.map((t, i) => {
          const active = t.fromMs <= nowMs && t.toMs > nowMs;
          return (
            <span key={`${t.fromMs}-${i}`} style={{ color: active ? ACCENT : "white" }}>
              {t.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// Shows word-by-word captions. `caps` times are relative to this component's start.
export const Captions: React.FC<{ caps: Cap[] }> = ({ caps }) => {
  const { fps } = useVideoConfig();
  const { pages } = useMemo(
    () =>
      createTikTokStyleCaptions({
        captions: caps.map(
          (c): Caption => ({ text: c.text, startMs: c.startMs, endMs: c.endMs, timestampMs: null, confidence: null }),
        ),
        combineTokensWithinMilliseconds: SWITCH_MS,
      }),
    [caps],
  );
  return (
    <AbsoluteFill>
      {pages.map((page, i) => {
        const next = pages[i + 1] ?? null;
        const from = Math.round((page.startMs / 1000) * fps);
        const lastEnd = page.tokens[page.tokens.length - 1].toMs + 250;
        const end = Math.round((Math.min(next ? next.startMs : Infinity, lastEnd) / 1000) * fps);
        if (end - from <= 0) return null;
        return (
          <Sequence key={i} from={from} durationInFrames={end - from}>
            <Page page={page} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};