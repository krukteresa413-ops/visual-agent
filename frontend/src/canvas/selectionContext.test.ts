import { describe, expect, it } from 'vitest';
import { buildSelectionContext } from './selectionContext';
import type { Node } from '@xyflow/react';
import type { FlowCanvasNodeData } from './canvasTypes';

describe('selection context for AI Companion', () => {
  it('extracts stable node id and provenance asset id for one selected node', () => {
    const nodes: Array<Node<FlowCanvasNodeData>> = [
      {
        id: 'runtime-1',
        position: { x: 0, y: 0 },
        data: {
          id: 'legacy-1',
          legacy_id: 'legacy-1',
          type: 'image',
          label: 'Main image',
          width: 100,
          height: 80,
          metadata: { provenance: { assetId: 'asset-main' } },
        },
      },
    ];

    expect(buildSelectionContext(nodes)).toEqual([
      { nodeId: 'runtime-1', legacyId: 'legacy-1', assetId: 'asset-main', label: 'Main image', type: 'image' },
    ]);
  });

  it('extracts two selected asset ids and supports asset_ref fallback', () => {
    const nodes: Array<Node<FlowCanvasNodeData>> = [
      {
        id: 'runtime-1',
        position: { x: 0, y: 0 },
        data: { id: 'legacy-1', type: 'image', label: 'A', width: 100, height: 80, metadata: { provenance: { assetId: 'asset-a' } } },
      },
      {
        id: 'runtime-2',
        position: { x: 0, y: 0 },
        data: { id: 'legacy-2', type: 'image', label: 'B', width: 100, height: 80, asset_ref: { asset_id: 'asset-b' } },
      },
    ];

    expect(buildSelectionContext(nodes).map(item => item.assetId)).toEqual(['asset-a', 'asset-b']);
  });
});
