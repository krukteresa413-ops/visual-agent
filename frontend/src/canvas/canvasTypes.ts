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
  // 容器归属:子元素挂到画板(frame)上。x/y 此时是「相对父」坐标(= 绝对坐标当无父时)。
  parentId?: string;
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

// Phase A 生成节点(type==='generator')使用的瞬时字段;均可选,不持久化(序列化前已过滤)。
// 注意:必须用 type(对象字面量)而非 interface —— 命名 interface 不满足 React Flow
// Node<T extends Record<string, unknown>> 约束(interface 因可声明合并而被 TS 视为开放)。
export type GeneratorNodeFields = {
  kind?: 'image' | 'video';
  status?: 'idle' | 'generating' | 'error';
  error?: string;
  onGenerate?: (
    id: string,
    params: { prompt: string; reference_image_url?: string; width: number; height: number; ratio: string; brief: Record<string, unknown> },
  ) => void;
};

export type FlowCanvasNodeData = Omit<LegacyCanvasElement, 'x' | 'y' | 'width' | 'height'> & {
  width: number;
  height: number;
  legacy_id?: string;
} & GeneratorNodeFields;

export type FlowCanvasEdgeData = Omit<LegacyCanvasConnection, 'id' | 'source_id' | 'target_id'> & {
  onLabelCommit?: (edgeId: string, label: string) => void;
};

export interface FlowCanvasState {
  nodes: Array<Node<FlowCanvasNodeData>>;
  edges: Array<Edge<FlowCanvasEdgeData>>;
  viewport: Viewport;
}
