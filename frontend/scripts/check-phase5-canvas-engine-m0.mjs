import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const failures = [];

function read(relativePath) {
  const fullPath = path.join(root, relativePath);
  if (!fs.existsSync(fullPath)) {
    failures.push(`missing file ${relativePath}`);
    return '';
  }
  return fs.readFileSync(fullPath, 'utf8');
}

const canvasView = read('src/components/CanvasView.tsx');
const legacy = read('src/components/CanvasViewLegacy.tsx');
const packageJson = JSON.parse(read('package.json'));
const deps = { ...(packageJson.dependencies || {}), ...(packageJson.devDependencies || {}) };

if (!deps['@xyflow/react']) failures.push('missing @xyflow/react dependency');
if (!deps['@dagrejs/dagre']) failures.push('missing @dagrejs/dagre dependency');
if (deps.zustand) failures.push('zustand should not be required for React Flow P0');
if (!canvasView.includes('VITE_ENABLE_FLOW_CANVAS')) failures.push('CanvasView missing VITE_ENABLE_FLOW_CANVAS flag');
if (!canvasView.includes('CanvasViewLegacy')) failures.push('CanvasView missing CanvasViewLegacy fallback');
if (!legacy.includes('const [selectedEl, setSelectedEl] = useState<CanvasElement | null>(null);')) {
  failures.push('legacy selection should remain single-source local legacy behavior');
}
if (legacy.includes('useCanvasEngineStore') || legacy.includes('selectedIds')) {
  failures.push('legacy should not keep retired hand-rolled canvasStore/selectedIds bridge');
}
for (const marker of ['rotation?: number', 'zIndex?: number', 'hidden?: boolean', 'locked?: boolean', 'editableLayers?:']) {
  if (!legacy.includes(marker)) failures.push(`legacy CanvasElement missing backend-compatible ${marker}`);
}

if (failures.length) {
  console.error(failures.join('\n'));
  process.exit(1);
}
console.log('phase45_s1_feature_flag_legacy_contract_ok');
