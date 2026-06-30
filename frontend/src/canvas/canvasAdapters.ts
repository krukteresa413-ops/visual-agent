import type { FlowCanvasState, LegacyCanvasConnection, LegacyCanvasElement, LegacyCanvasState } from './canvasTypes';
import { orderByParent } from './frameNesting';

// 工具栏小工具用专属 React Flow 节点类型渲染;其余素材沿用 AssetNode(canvasElement)。
// 元素的逻辑类型(element.type)存在 data.type 里,据此选渲染组件,保证回流时不被打回 canvasElement。
const NODE_TYPE_BY_ELEMENT: Record<string, string> = {
  shape: 'shape',
  text: 'text',
  mark: 'mark',
  freedraw: 'freedraw',
  frame: 'frame',
};
function nodeTypeForElement(elementType: string): string {
  return NODE_TYPE_BY_ELEMENT[elementType] || 'canvasElement';
}

export function legacyToFlowCanvas(state: LegacyCanvasState): FlowCanvasState {
  const seenIds = new Map<string, number>();

  return {
    // 父在子前排序:React Flow 要求父节点在数组中排在子节点之前。
    nodes: orderByParent(state.elements).map(element => {
      const seen = seenIds.get(element.id) || 0;
      seenIds.set(element.id, seen + 1);
      const runtimeId = seen === 0 ? element.id : `${element.id}__rf_${seen}`;

      return {
        id: runtimeId,
        type: nodeTypeForElement(element.type),
        position: { x: element.x, y: element.y },
        width: element.width,
        height: element.height,
        hidden: element.hidden,
        draggable: !element.locked,
        selectable: !element.locked,
        ...(element.parentId ? { parentId: element.parentId } : {}),
        data: {
          ...withoutGeometry(element),
          legacy_id: element.id,
          width: element.width,
          height: element.height,
        },
      };
    }),
    edges: state.connections.map(connection => ({
      id: connection.id,
      source: connection.source_id,
      target: connection.target_id,
      label: connection.label,
      data: withoutEndpoints(connection),
    })),
    viewport: {
      x: state.viewport.x,
      y: state.viewport.y,
      zoom: state.viewport.scale,
    },
  };
}

export function flowToLegacyCanvas(state: FlowCanvasState): LegacyCanvasState {
  return {
    // Phase A:「生成节点」(type==='generator')是临时输入卡片,不持久化(否则回流会变成空的 AssetNode)。
    elements: state.nodes.filter(node => node.type !== 'generator').map(node => {
      const { legacy_id: legacyId, ...data } = node.data;
      return {
        ...data,
        id: legacyId || node.id,
        x: node.position.x,
        y: node.position.y,
        width: node.data.width,
        height: node.data.height,
        ...(node.parentId ? { parentId: node.parentId } : {}),
      };
    }),
    connections: state.edges.map(edge => {
      const { onLabelCommit: _onLabelCommit, ...data } = edge.data || {};
      return {
        id: edge.id,
        source_id: edge.source,
        target_id: edge.target,
        label: typeof edge.label === 'string' ? edge.label : data.label,
        ...data,
      };
    }),
    viewport: {
      x: state.viewport.x,
      y: state.viewport.y,
      scale: state.viewport.zoom,
    },
  };
}

function withoutGeometry(element: LegacyCanvasElement) {
  const { x: _x, y: _y, width: _width, height: _height, ...data } = element;
  // parentId 是 React Flow 节点的顶层属性,单独承载;从 data 剔除以免 un-parent 后残留旧值。
  const clean: typeof data = { ...data };
  delete clean.parentId;
  return clean;
}

function withoutEndpoints(connection: LegacyCanvasConnection) {
  const { id: _id, source_id: _sourceId, target_id: _targetId, ...data } = connection;
  return data;
}


export function upsertFlowCanvasNode(
  nodes: FlowCanvasState['nodes'],
  element: LegacyCanvasElement
): FlowCanvasState['nodes'] {
  const flow = legacyToFlowCanvas({ elements: [element], connections: [], viewport: { x: 0, y: 0, scale: 1 } });
  const nextNode = flow.nodes[0];
  const targetId = element.id;
  const existingIndex = nodes.findIndex(node => (node.data.legacy_id || node.id) === targetId);

  if (existingIndex < 0) return [...nodes, nextNode];

  return nodes.map((node, index) => {
    if (index !== existingIndex) return node;
    return {
      ...nextNode,
      id: node.id,
      selected: node.selected,
    };
  });
}
