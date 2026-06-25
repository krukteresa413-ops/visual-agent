import type { Node } from '@xyflow/react';
import type { FlowCanvasNodeData } from './canvasTypes';

export interface SelectionContextItem {
  nodeId: string;
  legacyId?: string;
  assetId?: string;
  label?: string;
  type?: string;
  imageUrl?: string;
}

export function buildSelectionContext(nodes: Array<Node<FlowCanvasNodeData>>): SelectionContextItem[] {
  return nodes.map(node => ({
    nodeId: node.id,
    legacyId: node.data.legacy_id || node.data.id,
    assetId: extractAssetId(node.data),
    label: node.data.label,
    type: node.data.type,
    imageUrl: extractImageUrl(node.data),
  }));
}

function extractAssetId(data: FlowCanvasNodeData): string | undefined {
  const provenance = readRecord(data.metadata?.provenance);
  const assetId = provenance?.assetId ?? provenance?.asset_id ?? data.asset_ref?.assetId ?? data.asset_ref?.asset_id ?? data.metadata?.assetId ?? data.metadata?.asset_id;
  return assetId == null ? undefined : String(assetId);
}

function extractImageUrl(data: FlowCanvasNodeData): string | undefined {
  const assetRef = readRecord(data.asset_ref);
  const metadata = readRecord(data.metadata);
  const url = data.thumbnail_url ?? assetRef?.url ?? metadata?.imageUrl ?? metadata?.image_url;
  return url == null ? undefined : String(url);
}

function readRecord(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : undefined;
}
