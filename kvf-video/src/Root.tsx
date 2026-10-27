import { Composition, Still, staticFile } from "remotion";
import { loadFont } from "@remotion/fonts";
import { DayVideo, totalFrames } from "./DayVideo";
import { DayProps } from "./types";
import { Cover, CoverProps } from "./Cover";

// Real props always come from --props=public/dayN/props.json (make_props.py).
// These defaults only keep the composition valid when no props are passed.
const emptyDay: DayProps = {
  dir: "",
  day: 0,
  goalText: "10% BODY FAT",
  clips: {},
  lines: [],
  opener: null,
  vo: { src: "vo.wav", durationMs: 1000, lines: [], captions: [] },
};

Promise.all([
  loadFont({ family: "Inter", url: staticFile("fonts/Inter-SemiBold.otf"), weight: "600" }),
  loadFont({ family: "Inter", url: staticFile("fonts/Inter-ExtraBold.otf"), weight: "800" }),
  loadFont({ family: "Inter", url: staticFile("fonts/Inter-Black.otf"), weight: "900" }),
]);

export const RemotionRoot: React.FC = () => (
  <>
  <Composition
    id="Day"
    component={DayVideo}
    fps={30}
    width={1080}
    height={1920}
    durationInFrames={300}
    defaultProps={emptyDay}
    calculateMetadata={({ props }) => ({ durationInFrames: totalFrames(props, 30) })}
  />
  <Still
    id="Cover"
    component={Cover}
    width={1080}
    height={1920}
    defaultProps={{ bg: "", day: 0, hook: "Hook with one *lime* word" } as CoverProps}
  />
  </>
);
