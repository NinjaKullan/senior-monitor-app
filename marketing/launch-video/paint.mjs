// Paints one backdrop with Gemini. Not part of the render: run by hand, pick the best candidate.
// Same call pattern and daily cap as tools/social/make_strip.py (which needs Pillow; this needs nothing).
// Usage: node paint.mjs <name> [reference.png ...]   -> candidates/<name>-<n>.png  (run inside this folder)
// Copied from marketing/explainer-video/paint.mjs (branch video-explainer); the aspect ratio and the layer-style switch differ.
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';

const HOST = 'https://generativelanguage.googleapis.com/v1beta/models';
const MODELS = ['gemini-3.1-flash-image', 'gemini-2.5-flash-image'];
const COUNTER = homedir() + '/.kettle_image_count.json', CAP = Number(process.env.KETTLE_IMAGE_CAP || 30);
const [name, ...refs] = process.argv.slice(2);
const key = process.env.GEMINI_API_KEY;
if (!key) throw new Error('GEMINI_API_KEY is not set');

const md = readFileSync(new URL('assets/PROMPTS.md', import.meta.url), 'utf8');
const block = n => { const m = md.match(new RegExp(`## ${n}\\n[\\s\\S]*?\`\`\`\\n([\\s\\S]*?)\\n\`\`\``)); if (!m) throw new Error('no prompt: ' + n); return m[1]; };
// Layers (name starts with layer-) are single objects on a key colour; they get their own style block.
const prompt = block(name.startsWith('layer-') ? 'layer-style' : 'style') + '\n\n' + block(name);

function countCall() {
  const today = new Date().toISOString().slice(0, 10);
  let d = {}; try { d = JSON.parse(readFileSync(COUNTER, 'utf8')); } catch {}
  if (d.date !== today) d = { date: today, count: 0 };
  if (d.count >= CAP) throw new Error(`daily image cap reached (${CAP})`);
  d.count++; writeFileSync(COUNTER, JSON.stringify(d));
}

const parts = [{ text: prompt }, ...refs.map(p => ({ inline_data: { mime_type: 'image/png', data: readFileSync(p).toString('base64') } }))];
let last = '';
for (const model of MODELS) {
  for (const gen of [{ responseModalities: ['IMAGE'], imageConfig: { aspectRatio: '16:9' } }, { responseModalities: ['IMAGE'] }]) {
    for (let attempt = 0; attempt < 4; attempt++) {
      countCall();
      const r = await fetch(`${HOST}/${model}:generateContent`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'x-goog-api-key': key },
        body: JSON.stringify({ contents: [{ parts }], generationConfig: gen }) });
      if (!r.ok) { last = `${model} HTTP ${r.status}: ${(await r.text()).slice(0, 300)}`;
        if ([429, 500, 503].includes(r.status)) { await new Promise(s => setTimeout(s, 8000 * (attempt + 1))); continue; } break; }
      const blob = (await r.json()).candidates?.[0]?.content?.parts?.find(p => p.inlineData || p.inline_data);
      if (!blob) { last = `${model}: no image in response`; break; }
      mkdirSync('candidates', { recursive: true });
      let n = 1; while (existsSync(`candidates/${name}-${n}.png`)) n++;
      writeFileSync(`candidates/${name}-${n}.png`, Buffer.from((blob.inlineData || blob.inline_data).data, 'base64'));
      console.log(`${model} -> candidates/${name}-${n}.png`); process.exit(0);
    }
  }
}
throw new Error('image generation failed: ' + last);
