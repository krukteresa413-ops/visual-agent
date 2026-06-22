import fs from 'node:fs';

const canvas = fs.readFileSync('src/components/CanvasViewLegacy.tsx', 'utf8');
const page = fs.readFileSync('src/pages/GeneratePage.tsx', 'utf8');
const css = fs.readFileSync('src/index.css', 'utf8');
const chat = fs.readFileSync('src/components/AIChatPanel.tsx', 'utf8');

const checks = [
  ['Canvas shell root has Lovart shell marker', canvas.includes('data-lovart-canvas-shell')],
  ['Lovart canvas background token is present', canvas.includes('#F5F5F5') || css.includes('--lo-bg-canvas')],
  ['Image action bar is present', canvas.includes('data-lovart-image-action-bar')],
  ['Canvas topbar is 48px high', canvas.includes('data-lovart-canvas-topbar') && canvas.includes('h-12')],
  ['Right chat panel width follows Lovart 399px', page.includes('w-[399px]') || page.includes('w-[400px]')],
  ['Lovart composer is present', /\bdata-lovart-composer(=|\s|>)/.test(chat)],
];

const failed = checks.filter(([, ok]) => !ok);
if (failed.length) {
  console.error('Lovart canvas shell contract failed:');
  for (const [name] of failed) console.error(`- ${name}`);
  process.exit(1);
}
console.log('Lovart canvas shell contract passed');
