#!/usr/bin/env node
/**
 * render_svgs.js
 * Usage: node render_svgs.js <svg_dir> <png_dir> <width> <height>
 *
 * Renders every .svg file in svg_dir to a .png in png_dir
 * using a headless Chromium browser (via Puppeteer).
 */

const puppeteer = require('/tmp/opencode/node_modules/puppeteer');
const fs   = require('fs');
const path = require('path');

const [,, svgDir, pngDir, wStr, hStr] = process.argv;
if (!svgDir || !pngDir) {
  console.error('Usage: node render_svgs.js <svg_dir> <png_dir> <width> <height>');
  process.exit(1);
}

const W = parseInt(wStr || '400', 10);
const H = parseInt(hStr || '600', 10);

fs.mkdirSync(pngDir, { recursive: true });

const svgFiles = fs.readdirSync(svgDir)
  .filter(f => f.endsWith('.svg'))
  .sort();

console.log(`Rendering ${svgFiles.length} SVG frames at ${W}x${H} …`);

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });

  for (let i = 0; i < svgFiles.length; i++) {
    const svgFile = svgFiles[i];
    const svgPath = path.join(svgDir, svgFile);
    const pngPath = path.join(pngDir, svgFile.replace('.svg', '.png'));

    const svgContent = fs.readFileSync(svgPath, 'utf8');
    const html = `<!DOCTYPE html>
<html>
<head><style>
* { margin:0; padding:0; }
html, body { width:${W}px; height:${H}px; background:transparent; overflow:hidden; }
svg { width:${W}px; height:${H}px; }
</style></head>
<body>${svgContent}</body>
</html>`;

    await page.setContent(html, { waitUntil: 'load' });
    await page.screenshot({ path: pngPath, omitBackground: true });

    if ((i + 1) % 50 === 0 || i === svgFiles.length - 1) {
      process.stdout.write(`  ${i + 1}/${svgFiles.length} frames rendered\n`);
    }
  }

  await browser.close();
  console.log('Done.');
})().catch(err => { console.error(err); process.exit(1); });
