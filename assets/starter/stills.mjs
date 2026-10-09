// Batch stills in one browser session: node stills.mjs evidence/stills 1.2 4.5 9.0 [--hide-captions]
import {chromium} from 'playwright';
import {createHash} from 'node:crypto';
import {readFile, mkdir} from 'node:fs/promises';
import {serve} from './server.mjs';
const argv = process.argv.slice(2), hideCaptions = argv.includes('--hide-captions');
const [out = 'evidence/stills', ...times] = argv.filter(a => a !== '--hide-captions');
const plan = JSON.parse(await readFile('plan.json', 'utf8'));
const built = await readFile('dist/plan.sha256', 'utf8').catch(() => null);
if (built !== null && built.trim() !== createHash('sha256').update(await readFile('plan.json')).digest('hex')) throw new Error('plan.json changed since the last build (narrate.py, edited shots?); run npm run build first.');
await mkdir(out, {recursive: true});
const {server, url} = await serve();
const browser = await chromium.launch({headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
try {
  const page = await browser.newPage({viewport: {width: plan.width, height: plan.height}});
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror ' + e.message));
  page.on('response', r => { if (r.status() >= 400) errors.push(r.status() + ' ' + r.url()); });
  await page.goto(url, {waitUntil: 'networkidle'});
  await page.evaluate(() => window.__filmReady);
  if (hideCaptions) await page.evaluate(() => { window.__hideCaptions = true; });   // e.g. the poster still of a narrated film
  for (const t of times) { await page.evaluate(x => window.seek(x), Number(t)); await page.screenshot({path: `${out}/t${Number(t).toFixed(2).padStart(6, '0')}.png`}); }
  console.log(JSON.stringify({stills: times.length, errors, api: await page.evaluate(() => [...new Set(window.__filmApiLog || [])])}));
} finally { await browser.close(); server.close(); }
