import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const barSource = fs.readFileSync(path.resolve(__dirname, 'ImageActionBar.tsx'), 'utf8');
const flowSource = fs.readFileSync(path.resolve(__dirname, '../CanvasFlow.tsx'), 'utf8');

describe('ImageActionBar React Flow contract', () => {
  it('renders the eight-action bar with busy-based disabling', () => {
    expect(barSource).toContain('data-lovart-image-action-bar');
    // download / to-chat / cutout / back / backward / forward / front / delete
    expect((barSource.match(/id: '/g) || []).length).toBe(8);
    expect(barSource).toContain("id: 'to-chat'");
    expect(barSource).toContain('data-image-action={action.id}');
    expect(barSource).toContain('busy === action.id');
  });

  it('hides 抠图 (cutout) for video elements via elementType', () => {
    expect(barSource).toContain('elementType');
    expect(barSource).toMatch(/elementType === 'video'/);
    expect(barSource).toContain("a.id !== 'cutout'");
  });

  it('is wired from CanvasFlow selected React Flow nodes and viewport', () => {
    expect(flowSource).toContain('selectedActionNode');
    expect(flowSource).toContain('actionBarAnchor(');
    expect(flowSource).toContain('<ImageActionBar');
    expect(flowSource).toContain('onSelectionChange={noteSelectionChange}');
  });

  it('does not import tldraw', () => {
    expect(barSource).not.toMatch(/tldraw/i);
    expect(flowSource).not.toMatch(/tldraw/i);
  });
});
