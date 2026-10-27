import { AbsoluteFill, Img, staticFile } from "remotion";
import { ACCENT } from "./types";

// Cover / thumbnail for every post. Locked design:
// his face (a frame from the opener), big lime "DAY N" badge on top, one short hook line at the bottom.
// Everything sits inside y 240..1680 so Instagram's 3:4 profile grid crop keeps it.
// zoom / y (px) move the photo so the face sits between the badge and the hook.
// badge: text of the top block (default "DAY N"); weekly Monday covers use "WEEK N".
export type CoverProps = { bg: string; day: number; hook: string; zoom?: number; y?: number; badge?: string };

// "AI SWAPPED MY *OATS*" -> words wrapped in *stars* are lime.
const Hook: React.FC<{ text: string }> = ({ text }) => (
  <div
    style={{
      fontFamily: "Inter",
      fontWeight: 900,
      fontSize: 128,
      lineHeight: 1.02,
      textTransform: "uppercase",
      textAlign: "center",
      color: "white",
      WebkitTextStroke: "16px black",
      paintOrder: "stroke fill",
      textShadow: "0 8px 24px rgba(0,0,0,0.5)",
      maxWidth: 940,
    }}
  >
    {text.split(" ").map((w, i) => {
      const m = w.match(/^\*(.+)\*([?!.,:]*)$/); // *word* or *word*? -> lime word, white punctuation
      return m ? (
        <span key={i}>
          <span style={{ color: ACCENT }}>{m[1]}</span>
          {m[2]}{" "}
        </span>
      ) : (
        <span key={i}>{w} </span>
      );
    })}
  </div>
);

export const Cover: React.FC<CoverProps> = ({ bg, day, hook, zoom = 1, y = 0, badge }) => (
  <AbsoluteFill style={{ background: "black" }}>
    <Img
      src={staticFile(bg)}
      style={{ width: "100%", height: "100%", objectFit: "cover", transform: `translateY(${y}px) scale(${zoom})` }}
    />
    <AbsoluteFill
      style={{
        background:
          "linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 28%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.7) 88%)",
      }}
    />
    <div style={{ position: "absolute", top: 290, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
      <div
        style={{
          background: ACCENT,
          color: "black",
          fontFamily: "Inter",
          fontWeight: 900,
          fontSize: 150,
          letterSpacing: 4,
          padding: "10px 52px",
          borderRadius: 32,
          boxShadow: "0 10px 30px rgba(0,0,0,0.35)",
        }}
      >
        {badge ?? `DAY ${day}`}
      </div>
    </div>
    <div style={{ position: "absolute", bottom: 270, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
      <Hook text={hook} />
    </div>
  </AbsoluteFill>
);