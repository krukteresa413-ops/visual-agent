import type { Edge, Node, Viewport } from '@xyflow/react';

export interface LegacyCanvasElement {
  id: string;
  type: string;
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation?: number;
  zIndex?: number;
  hidden?: boolean;
  locked?: boolean;
  editableLayers?: Array<Record<string, unknown>>;
  thumbnail_url?: string;
  asset_ref?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface LegacyCanvasConnection {
  id: string;
  source_id: string;
  target_id: string;
  label?: string;
  relation_type?: string;
  metadata?: Record<string, unknown>;
}

export interface LegacyCanvasViewport {
  x: number;
  y: number;
  scale: number;
}

export interface LegacyCanvasState {
  elements: LegacyCanvasElement[];
  connections: LegacyCanvasConnection[];
  viewport: LegacyCanvasViewport;
}

export type FlowCanvasNodeData = Omit<LegacyCanvasElement, 'x' | 'y' | 'width' | 'height'> & {
  width: number;
  height: number;
  legacy_id?: string;
};

export type FlowCanvasEdgeData = Omit<LegacyCanvasConnection, 'id' | 'source_id' | 'target_id'> & {
  onLabelCommit?: (edgeId: string, label: string) => void;
};

export interface FlowCanvasState {
  nodes: Array<Node<FlowCanvasNodeData>>;
  edges: Array<Edge<FlowCanvasEdgeData>>;
  viewport: Viewport;
}
