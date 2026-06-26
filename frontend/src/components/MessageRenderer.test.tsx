import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const rendererPath = path.resolve(__dirname, 'MessageRenderer.tsx');
const source = fs.existsSync(rendererPath) ? fs.readFileSync(rendererPath, 'utf8') : '';
const panelSource = fs.readFileSync(path.resolve(__dirname, 'AIChatPanel.tsx'), 'utf8');

describe('MessageRenderer LS3-4 contract', () => {
  it('has a dedicated renderer used by AIChatPanel', () => {
    expect(source).toContain('export default function MessageRenderer');
    expect(panelSource).toContain('MessageRenderer');
    expect(panelSource).toContain('chatState.messages');
  });

  it('renders text, image and video assets with MOYAG-safe markers', () => {
    expect(source).toContain('data-message-renderer');
    expect(source).toContain('data-message-text');
    expect(source).toContain('data-message-image');
    expect(source).toContain('data-message-video');
    expect(source).toContain('<img');
    expect(source).toContain('<video');
  });

  it('renders assistant image assets as compact chat thumbnails, not generation result cards', () => {
    expect(source).toContain('data-message-asset-list');
    expect(source).toContain('data-message-image-thumb');
    expect(source).not.toMatch(/快速图视频|商务图视频|生成完成/);
  });

  it('uses lo tokens instead of Ant or Lovart-specific styling and names', () => {
    expect(source).toContain('var(--lo-bg-float)');
    expect(source).toContain('var(--lo-border-neutral-l1)');
    expect(source).not.toMatch(/Lovart|Ant Design|ant-|nano banana|seedream|DEFAULT_MODELS/i);
  });
});
