// Parse every ```mermaid block under the given files/folders with the same Mermaid version the viewer loads.
//
// One-time setup in a scratch folder (NOT inside the audited repo):
//   mkdir -p <scratch>/mm && cd <scratch>/mm && echo '{"type":"module"}' > package.json
//   npm install --no-audit --no-fund mermaid@11.4.1 jsdom@24.1.3
//   cp <skill>/scripts/check_mermaid.mjs .
// Run:  cd <scratch>/mm && node check_mermaid.mjs <audit folder> [...more paths]
// Prints FAIL lines and "ok=N bad=M"; exits 1 when anything fails.
import { JSDOM } from 'jsdom';
import fs from 'fs';
import path from 'path';

const dom = new JSDOM('<!doctype html><body></body>', { pretendToBeVisual: true });
Object.assign(globalThis, {
  window: dom.window, document: dom.window.document, DOMParser: dom.window.DOMParser,
  Element: dom.window.Element, HTMLElement: dom.window.HTMLElement, Node: dom.window.Node, SVGElement: dom.window.SVGElement,
});
try { globalThis.navigator = dom.window.navigator; } catch { /* read-only in newer Node */ }
const mermaid = (await import('mermaid')).default;
mermaid.initialize({ startOnLoad: false });

const files = process.argv.slice(2).flatMap(p => fs.statSync(p).isDirectory()
  ? fs.readdirSync(p, { recursive: true }).filter(f => f.endsWith('.md')).map(f => path.join(p, f))
  : [p]);
let ok = 0, bad = 0;
for (const f of files) {
  const md = fs.readFileSync(f, 'utf8');
  for (const m of md.matchAll(/```mermaid\n([\s\S]*?)```/g)) {
    try { await mermaid.parse(m[1]); ok++; } catch (e) { bad++; console.log('FAIL', f, String(e.message || e).split('\n')[0]); }
  }
}
console.log(`ok=${ok} bad=${bad}`);
process.exit(bad ? 1 : 0);
