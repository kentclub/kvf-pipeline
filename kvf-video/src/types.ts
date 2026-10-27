export type Cap = { text: string; startMs: number; endMs: number; line?: number };

// start = seconds into the clip. "over" puts a card as a panel on top of a clip.
export type Over = { clip: string; start?: number };
export type Visual =
  | { clip: string; start?: number; tag?: string }
  | { clips: string[]; starts?: number[]; tags?: string[] }
  | { card: "meal"; label: string; items: string[]; over?: Over }
  | { card: "totals"; kcal: number; protein: number; deficit: number; over?: Over }
  | { card: "progress"; kg: number; of: number; pct: number; over?: Over }
  | { card: "week"; days: { d: string; v: number }[]; over?: Over }
  | { card: "balance"; saved: number; savedLabel: string; lost: number; lostLabel: string; net: number; over?: Over }
  | { card: "scan"; label: string; rows: { k: string; a: string; b: string }[]; over?: Over };

export type DayProps = {
  dir: string;
  day: number;
  goalText: string;
  clips: Record<string, number>; // clip name -> duration in seconds
  lines: { text: string; visual: Visual }[];
  opener: { src: string; trimMs?: number; durationMs: number; captions: Cap[]; thisMs: number[] } | null;
  vo: {
    src: string;
    durationMs: number;
    lines: { startMs: number; endMs: number }[];
    captions: Cap[];
  };
};

export const ACCENT = "#D4FF3A";
export const TAIL_MS = 600;