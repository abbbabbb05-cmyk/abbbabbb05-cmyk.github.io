// Sahne sayfasını kare kare çeker, ffmpeg'e gönderir (sessiz video).
// Kullanım: node kaydet.js sayfa.html toplam_sure fps cikti.mp4
//           node kaydet.js sayfa.html - - klasor --kareler 1.2,4,9.5   (PNG önizleme)
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

(async () => {
  const [page, dur, fps, out, flag, list] = process.argv.slice(2);
  const browser = await chromium.launch();
  const p = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  p.on('pageerror', e => console.error('SAYFA HATASI:', e.message));
  await p.goto('file://' + path.resolve(page));
  await p.evaluate(() => window.ready);

  if (flag === '--kareler') {
    for (const t of list.split(',').map(Number)) {
      await p.evaluate(x => window.setFrame(x), t);
      const f = path.join(out, `kare_${t.toFixed(2)}.png`);
      await p.screenshot({ path: f });
      console.log(f);
    }
    await browser.close();
    return;
  }

  const F = Number(fps), N = Math.ceil(Number(dur) * F);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(F), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise(r => ff.on('close', r));
  for (let i = 0; i < N; i++) {
    await p.evaluate(x => window.setFrame(x), i / F);
    const buf = await p.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) process.stdout.write(`\rkare ${i}/${N}`);
  }
  ff.stdin.end();
  const code = await done;
  console.log(`\rkare ${N}/${N} bitti`);
  await browser.close();
  process.exit(code || 0);
})();
