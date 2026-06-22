import type { FlowCanvasState, LegacyCanvasConnection, LegacyCanvasElement, LegacyCanvasState } from './canvasTypes';

export function legacyToFlowCanvas(state: LegacyCanvasState): FlowCanvasState {
  const seenIds = new Map<string, number>();

  return {
    nodes: state.elements.map(element => {
      const seen = seenIds.get(element.id) || 0;
      seenIds.set(element.id, seen + 1);
      const runtimeId = seen === 0 ? element.id : `${element.id}__rf_${seen}`;

      return {
        id: runtimeId,
        type: 'canvasElement',
        position: { x: element.x, y: element.y },
        width: element.width,
        height: element.height,
        hidden: element.hidden,
        draggable: !element.locked,
        selectable: !element.locked,
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
    elements: state.nodes.map(node => {
      const { legacy_id: legacyId, ...data } = node.data;
      return {
        ...data,
        id: legacyId || node.id,
        x: node.position.x,
        y: node.position.y,
        width: node.data.width,
        height: node.data.height,
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
  return data;
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
