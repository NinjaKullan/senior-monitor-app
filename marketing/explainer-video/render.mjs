// Renders index.html frame by frame in headless Chrome and encodes with ffmpeg.
// Output: out/kettle-explainer.mp4 (1080x1920, 30 fps, H.264, yuv420p, silent) and three stills.
import { spawn } from 'node:child_process';
import { mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const dir = fileURLToPath(new URL('.', import.meta.url));
const STILLS = { 120: 'still-1.png', 465: 'still-3.png', 870: 'still-5.png' };   // 4 s, 15.5 s, 29 s
const MP4 = dir + 'out/kettle-explainer.mp4';
mkdirSync(dir + 'out', { recursive: true });

const browser = await puppeteer.launch({
  executablePath: process.env.CHROME,                 // optional override
  channel: process.env.CHROME ? undefined : 'chrome', // otherwise the installed Google Chrome
  args: ['--allow-file-access-from-files', '--font-render-hinting=none'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1080, height: 1920 });
page.on('pageerror', e => { console.error(e); process.exit(1); });
await page.goto('file://' + dir + 'index.html');
await page.waitForFunction('window.__ready === true');
const frames = await page.evaluate('window.FRAMES');

const ffmpeg = spawn('ffmpeg', [
  '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '30', '-i', '-',
  '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '30', '-an',
  '-fflags', '+bitexact', '-flags', '+bitexact', '-movflags', '+faststart',
  MP4,
], { stdio: ['pipe', 'inherit', 'inherit'] });
const done = new Promise((res, rej) => ffmpeg.on('close', c => c ? rej(new Error('ffmpeg exited ' + c)) : res()));

try {
  for (let n = 0; n < frames; n++) {
    const url = await page.evaluate(n => window.frame(n), n);
    const png = Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
    if (STILLS[n]) writeFileSync(dir + 'out/' + STILLS[n], png);
    if (!ffmpeg.stdin.write(png)) await new Promise(r => ffmpeg.stdin.once('drain', r));
    if (n % 150 === 0) console.log(`frame ${n}/${frames}`);
  }
  ffmpeg.stdin.end();
  await done;
} catch (e) {                 // a failed frame must not leave a short, valid-looking MP4 behind
  done.catch(() => {});
  ffmpeg.kill();
  rmSync(MP4, { force: true });
  throw e;
}
await browser.close();
console.log('wrote out/kettle-explainer.mp4');
