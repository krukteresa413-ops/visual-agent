import fs from 'node:fs';
import path from 'node:path';

const src = fs.readFileSync(path.resolve('src/components/CanvasView.tsx'), 'utf8');
const required = [
  'getVersionRootId',
  'getVersionChain',
  '版本链',
  '查看上一版',
  '对比上一版',
  'data-version-chain',
  'setCompareA(parent.id)',
  'setCompareB(selectedEl.id)',
];
const missing = required.filter(token => !src.includes(token));
if (missing.length) {
  console.error('Missing ChatCanvas version UI tokens:', missing.join(', '));
  process.exit(1);
}
console.log('ChatCanvas version UI contract OK');
