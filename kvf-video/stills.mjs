// Frame sheet helper: node stills.mjs public/dayN/props.json 0 90 300 ...  -> ../stills/f<frame>.jpg
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import {readFileSync} from 'fs';
import path from 'path';
const [propsPath, ...rest] = process.argv.slice(2);
const inputProps = JSON.parse(readFileSync(propsPath, 'utf8'));
const frames = rest.map(Number);
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const comp = await selectComposition({serveUrl, id: 'Day', inputProps});
console.log('duration', comp.durationInFrames);
for (const fr of frames) {
  await renderStill({serveUrl, composition: comp, inputProps, frame: fr, output: `../stills/f${fr}.jpg`, imageFormat: 'jpeg', jpegQuality: 70, scale: 0.25});
  console.log('ok', fr);
}
