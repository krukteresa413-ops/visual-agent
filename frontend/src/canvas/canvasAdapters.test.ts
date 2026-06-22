import { describe, expect, it } from 'vitest';
import { flowToLegacyCanvas, legacyToFlowCanvas, upsertFlowCanvasNode } from './canvasAdapters';
import type { LegacyCanvasState } from './canvasTypes';

const legacyState: LegacyCanvasState = {
  elements: [
    {
      id: 'hero-1',
      type: 'image',
      label: 'Hero Visual',
      x: 12,
      y: 34,
      width: 320,
      height: 180,
      rotation: 15,
      zIndex: 7,
      hidden: false,
      locked: true,
      editableLayers: [{ id: 'title', type: 'text', text: 'MOYAG', editable: true }],
      thumbnail_url: '/uploads/hero.png',
      asset_ref: { asset_id: 42, asset_type: 'key_visual' },
      metadata: { prompt: 'orange shoe', nested: { keep: true } },
    },
    {
      id: 'copy-1',
      type: 'text',
      label: 'Copy',
      x: -20,
      y: 88,
      width: 260,
      height: 120,
      metadata: { tone: 'direct' },
    },
  ],
  connections: [
    {
      id: 'edge-1',
      source_id: 'hero-1',
      target_id: 'copy-1',
      label: 'supports',
      relation_type: 'semantic_support',
      metadata: { confidence: 0.91 },
    },
  ],
  viewport: { x: 5, y: -8, scale: 1.75 },
};

describe('canvas React Flow adapters', () => {
  it('round-trips legacy canvas state without dropping fields', () => {
    const flow = legacyToFlowCanvas(legacyState);
    const roundTrip = flowToLegacyCanvas(flow);

    expect(roundTrip).toEqual(legacyState);
  });

  it('maps legacy viewport scale to React Flow zoom and back', () => {
    const flow = legacyToFlowCanvas(legacyState);

    expect(flow.viewport).toEqual({ x: 5, y: -8, zoom: 1.75 });
    expect(flowToLegacyCanvas(flow).viewport).toEqual({ x: 5, y: -8, scale: 1.75 });
  });

  it('converts an empty canvas', () => {
    const empty: LegacyCanvasState = { elements: [], connections: [], viewport: { x: 0, y: 0, scale: 1 } };

    expect(flowToLegacyCanvas(legacyToFlowCanvas(empty))).toEqual(empty);
  });

  it('keeps duplicate legacy ids visible in React Flow runtime without losing the original id', () => {
    const duplicated: LegacyCanvasState = {
      elements: [
        { id: 'asset-1', type: 'image', label: 'A', x: 0, y: 0, width: 100, height: 100 },
        { id: 'asset-1', type: 'image', label: 'B', x: 120, y: 0, width: 100, height: 100 },
      ],
      connections: [],
      viewport: { x: 0, y: 0, scale: 1 },
    };

    const flow = legacyToFlowCanvas(duplicated);

    expect(flow.nodes).toHaveLength(2);
    expect(new Set(flow.nodes.map(node => node.id)).size).toBe(2);
    expect(flow.nodes.map(node => node.data.legacy_id)).toEqual(['asset-1', 'asset-1']);
  });

  it('converts Flow runtime ids back to legacy ids for API persistence', () => {
    const flow = legacyToFlowCanvas({
      elements: [{ id: 'asset-1', type: 'image', label: 'A', x: 0, y: 0, width: 100, height: 100 }],
      connections: [],
      viewport: { x: 10, y: 20, scale: 1.2 },
    });
    flow.nodes[0].id = 'asset-1__rf_runtime';
    flow.nodes[0].position = { x: 45, y: 55 };

    expect(flowToLegacyCanvas(flow).elements[0]).toMatchObject({ id: 'asset-1', x: 45, y: 55 });
  });

  it('upserts generated canvas elements by stable legacy id without growing node count', () => {
    const base = legacyToFlowCanvas({
      elements: [{ id: 'generated-main', type: 'image', label: 'old', x: 0, y: 0, width: 100, height: 100 }],
      connections: [],
      viewport: { x: 0, y: 0, scale: 1 },
    });

    const next = upsertFlowCanvasNode(base.nodes, {
      id: 'generated-main',
      type: 'image',
      label: 'new',
      x: 20,
      y: 30,
      width: 120,
      height: 130,
      metadata: { refreshed: true },
    });

    expect(next).toHaveLength(1);
    expect(next[0].data.label).toBe('new');
    expect(next[0].position).toEqual({ x: 20, y: 30 });
    expect(next[0].data.legacy_id).toBe('generated-main');
  });
});
