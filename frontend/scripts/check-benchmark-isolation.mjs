import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const src = path.join(root, 'src');
const allowedLovartFiles = new Set([
  'src/components/CanvasFlow.tsx',
  'src/components/CanvasViewLegacy.tsx',
  'src/lib/models/selectableModels.test.ts',
]);

const productionFiles = [];
const stack = [src];
while (stack.length) {
  const current = stack.pop();
  for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
    const full = path.join(current, entry.name);
    if (entry.isDirectory()) {
      stack.push(full);
      continue;
    }
    if (!/\.(ts|tsx)$/.test(entry.name) || /\.test\.(ts|tsx)$/.test(entry.name)) continue;
    productionFiles.push(full);
  }
}

const failures = [];
for (const file of productionFiles) {
  const rel = path.relative(root, file).replaceAll(path.sep, '/');
  const rawText = fs.readFileSync(file, 'utf8');
  const text = rawText
    .replace(/data-lovart-[A-Za-z0-9_-]+/g, '')
    .replace(/Lovart-style composer/gi, 'shell composer')
    .replace(/Lovart canvas shell/gi, 'canvas shell');
  if (/lovart/i.test(text) && !allowedLovartFiles.has(rel)) {
    failures.push(`${rel}: lovart benchmark reference in production UI path`);
  }
  if (/source\s*===\s*['"]benchmark['"]/.test(text) && rel !== 'src/lib/models/selectableModels.ts') {
    failures.push(`${rel}: benchmark source checked outside selectableModels`);
  }
}

if (failures.length) {
  console.error('Benchmark isolation failed:');
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log('PASS: benchmark providers are isolated from production UI selection');
