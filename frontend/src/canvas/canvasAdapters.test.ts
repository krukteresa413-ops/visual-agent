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

  it('preserves generated image nodes (thumbnail + asset_ref) through Legacy→Flow conversion', () => {
    const state: LegacyCanvasState = {
      elements: [
        {
          id: 'gen-img-1',
          type: 'image',
          label: '生成主图',
          x: 0,
          y: 0,
          width: 512,
          height: 512,
          thumbnail_url: '/uploads/generated/abc.png',
          asset_ref: { asset_id: 101, asset_type: 'key_visual' },
          metadata: { source: 'generation' },
        },
      ],
      connections: [],
      viewport: { x: 0, y: 0, scale: 1 },
    };
    const flow = legacyToFlowCanvas(state);

    expect(flow.nodes).toHaveLength(1);
    expect(flow.nodes[0].data.thumbnail_url).toBe('/uploads/generated/abc.png');
    expect(flow.nodes[0].data.asset_ref).toEqual({ asset_id: 101, asset_type: 'key_visual' });
    expect(flowToLegacyCanvas(flow).elements[0]).toMatchObject(state.elements[0]);
  });


  it('drops transient generator nodes from persisted Flow→Legacy state', () => {
    const flow = {
      nodes: [
        {
          id: 'asset-1',
          type: 'canvasElement',
          position: { x: 0, y: 0 },
          data: { type: 'image', label: 'A', width: 100, height: 100, legacy_id: 'asset-1' },
        },
        {
          id: 'gen_image_1',
          type: 'generator',
          position: { x: 200, y: 0 },
          data: { kind: 'image', status: 'idle', type: 'generator', label: 'gen', width: 300, height: 300 },
        },
      ],
      edges: [],
      viewport: { x: 0, y: 0, zoom: 1 },
    } as unknown as Parameters<typeof flowToLegacyCanvas>[0];

    const legacy = flowToLegacyCanvas(flow);

    expect(legacy.elements).toHaveLength(1);
    expect(legacy.elements[0].id).toBe('asset-1');
  });

  it('preserves connection metadata through Legacy→Flow conversion', () => {
    const state: LegacyCanvasState = {
      elements: [
        { id: 'source', type: 'image', label: '源图', x: 0, y: 0, width: 100, height: 100 },
        { id: 'variant', type: 'image', label: '变体', x: 120, y: 0, width: 100, height: 100 },
      ],
      connections: [
        {
          id: 'edge-instruction',
          source_id: 'source',
          target_id: 'variant',
          label: '换蓝色背景',
          relation_type: 'variant_of',
          metadata: { instruction: '换蓝色背景' },
        },
      ],
      viewport: { x: 0, y: 0, scale: 1 },
    };
    const flow = legacyToFlowCanvas(state);

    expect(flow.edges[0].data.relation_type).toBe('variant_of');
    expect(flow.edges[0].data.metadata).toEqual({ instruction: '换蓝色背景' });
    expect(flowToLegacyCanvas(flow).connections[0]).toMatchObject(state.connections[0]);
  });

  it('round-trips parentId + child relative position and orders parent before child', () => {
    const state: LegacyCanvasState = {
      elements: [
        // 故意把子元素放在前面,验证 legacyToFlow 会把父排到前面(React Flow 要求父在子前)
        { id: 'child', type: 'shape', label: '', x: 50, y: 60, width: 40, height: 40, parentId: 'frame', metadata: { shape: 'rect' } },
        { id: 'frame', type: 'frame', label: '画板', x: 100, y: 100, width: 400, height: 300 },
      ],
      connections: [],
      viewport: { x: 0, y: 0, scale: 1 },
    };

    const flow = legacyToFlowCanvas(state);
    expect(flow.nodes.map(node => node.id)).toEqual(['frame', 'child']);
    const child = flow.nodes.find(node => node.id === 'child');
    expect(child?.parentId).toBe('frame');
    expect(child?.position).toEqual({ x: 50, y: 60 }); // 相对父坐标保持不变,不被转成绝对

    const back = flowToLegacyCanvas(flow);
    expect(back.elements.find(el => el.id === 'child')).toMatchObject({ x: 50, y: 60, parentId: 'frame' });
  });

  it('does not add parentId to top-level elements', () => {
    const flow = legacyToFlowCanvas({
      elements: [{ id: 'a', type: 'image', label: 'A', x: 0, y: 0, width: 100, height: 100 }],
      connections: [],
      viewport: { x: 0, y: 0, scale: 1 },
    });

    expect('parentId' in flow.nodes[0]).toBe(false);
    expect('parentId' in flowToLegacyCanvas(flow).elements[0]).toBe(false);
  });

});
