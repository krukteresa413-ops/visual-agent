import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const source = fs.readFileSync(path.resolve(__dirname, 'ResultTabs.tsx'), 'utf8');

describe('ResultTabs one-click generation contract', () => {
  it('adds one-click generate controls to every asset tab panel', () => {
    expect(source).toContain('data-oneclick-generate');
    expect(source).toContain('OneClickGenerateButton');
    expect(source).toContain('TABS.length');
  });

  it('uses image generation for image-like tabs and avoids image generation for video scripts', () => {
    expect(source).toContain('api.generation.image');
    expect(source).toContain("active === 'video_scripts'");
    expect(source).toContain('generateVideoScriptText');
  });

  it('renders generated result in place and exposes add-to-canvas intent', () => {
    expect(source).toContain('generatedByTab');
    expect(source).toContain('加入画布');
    expect(source).toContain('data-oneclick-result');
  });
});
