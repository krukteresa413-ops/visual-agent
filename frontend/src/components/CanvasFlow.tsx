import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Connection,
  type Edge,
  type Node,
  type Viewport,
} from '@xyflow/react';
import { api } from '../api/client';
import { legacyToFlowCanvas, upsertFlowCanvasNode } from '../canvas/canvasAdapters';
import { useCanvasPersistence } from '../canvas/useCanvasPersistence';
import { buildSelectionContext, type SelectionContextItem } from '../canvas/selectionContext';
import type { FlowCanvasState, LegacyCanvasState } from '../canvas/canvasTypes';
import AssetNode from './nodes/AssetNode';
import ImageActionBar from './canvas/ImageActionBar';
import EditableRelationEdge from './canvas/EditableRelationEdge';
import { actionBarAnchor } from './canvas/actionBarAnchor';
import type CanvasViewLegacy from './CanvasViewLegacy';

type CanvasFlowProps = React.ComponentProps<typeof CanvasViewLegacy>;

const emptyFlow: FlowCanvasState = {
  nodes: [],
  edges: [],
  viewport: { x: 0, y: 0, zoom: 1 },
};

function buildFallbackState(props: CanvasFlowProps): LegacyCanvasState {
  const elements: LegacyCanvasState['elements'] = [];
  let col = 0;
  const add = (id: string, type: string, label: string, data: any, width = 320, height = 400) => {
    if (!data) return;
    elements.push({
      id,
      type,
      label,
      x: 60 + col * 370,
      y: 60,
      width,
      height,
      thumbnail_url: data?.url || data?.preview_url,
      metadata: data,
      asset_ref: { asset_type: type },
    });
    col += 1;
  };

  add('kv01', 'key_visual', 'KV_01_Main', props.mainImage);
  add('whitebg', 'white_bg', 'White BG', props.whiteBg, 280, 350);
  (props.sceneImages || []).forEach((scene: any, index: number) => add(`scene${index}`, 'scene_image', scene?.scene_name || `Scene ${index + 1}`, scene, 300, 240));
  (props.videoScripts || []).forEach((video: any, index: number) => add(`video${index}`, 'video', video?.video_goal || `Video ${index + 1}`, video, 300, 220));
  (props.sellingPoints || []).forEach((point: any, index: number) => add(`sp${index}`, 'graphic', point?.title || `SP ${index + 1}`, point, 240, 200));
  add('ad', 'graphic', 'Ad Material', props.adMaterial, 260, 220);

  return { elements, connections: [], viewport: { x: 0, y: 0, scale: 1 } };
}

function CanvasFlowInner(props: CanvasFlowProps) {
  const projectId = props.projectId || 2;
  const nodeTypes = useMemo(() => ({ canvasElement: AssetNode }), []);
  const edgeTypes = useMemo(() => ({ editableRelation: EditableRelationEdge }), []);
  const [nodes, setNodes, onNodesChange] = useNodesState(emptyFlow.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(emptyFlow.edges);
  const [initialViewport, setInitialViewport] = useState(emptyFlow.viewport);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [selectionContext, setSelectionContext] = useState<SelectionContextItem[]>([]);
  const [selectedActionNode, setSelectedActionNode] = useState<Node | null>(null);
  const [actionInstruction, setActionInstruction] = useState('');
  const [actionTaskId, setActionTaskId] = useState<string | null>(null);
  const [actionProgress, setActionProgress] = useState('idle');
  const [actionError, setActionError] = useState<string | null>(null);
  const { getNodes, getViewport } = useReactFlow();
  const { saveCanvas, rememberSavedCanvas } = useCanvasPersistence(projectId);

  const onRelationLabelCommit = useCallback((edgeId: string, label: string) => {
    setEdges(current => {
      const nextEdges = current.map(edge => edge.id === edgeId
        ? { ...edge, label, data: { ...edge.data, label } }
        : edge);
      void saveCanvas({ nodes: getNodes() as typeof nodes, edges: nextEdges, viewport: getViewport() });
      return nextEdges;
    });
  }, [getNodes, getViewport, saveCanvas, setEdges]);

  const makeEditableRelationEdges = useCallback((flowEdges: Edge[]): typeof edges => flowEdges.map(edge => ({
    ...edge,
    type: 'editableRelation',
    data: {
      ...edge.data,
      label: typeof edge.label === 'string' ? edge.label : typeof edge.data?.label === 'string' ? edge.data.label : undefined,
      instruction: typeof edge.data?.instruction === 'string' ? edge.data.instruction : typeof edge.data?.metadata === 'object' && edge.data.metadata && 'instruction' in edge.data.metadata ? String(edge.data.metadata.instruction) : undefined,
      onLabelCommit: onRelationLabelCommit,
    },
  })) as typeof edges, [onRelationLabelCommit]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError(false);

    api.atelierCanvas.getState(projectId).then(data => {
      if (cancelled) return;
      const legacy: LegacyCanvasState = data?.elements?.length
        ? {
            elements: data.elements,
            connections: data.connections || [],
            viewport: data.viewport || { x: 0, y: 0, scale: 1 },
          }
        : buildFallbackState(props);
      const flow = legacyToFlowCanvas(legacy);
      setNodes(flow.nodes);
      setEdges(makeEditableRelationEdges(flow.edges));
      setInitialViewport(flow.viewport);
      rememberSavedCanvas({ nodes: flow.nodes, edges: makeEditableRelationEdges(flow.edges), viewport: flow.viewport });
    }).catch(() => {
      if (cancelled) return;
      const flow = legacyToFlowCanvas(buildFallbackState(props));
      setNodes(flow.nodes);
      setEdges(makeEditableRelationEdges(flow.edges));
      setInitialViewport(flow.viewport);
      rememberSavedCanvas({ nodes: flow.nodes, edges: makeEditableRelationEdges(flow.edges), viewport: flow.viewport });
      setLoadError(true);
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });

    return () => { cancelled = true; };
  }, [makeEditableRelationEdges, projectId]);

  //  on refresh nonce, re-fetch canvas state and merge new nodes
  const initialCanvasNonceRef = useRef(true);
  const canvasRefreshNonce = props.canvasRefreshNonce;
  useEffect(() => {
    if (initialCanvasNonceRef.current) {
      initialCanvasNonceRef.current = false;
      return;
    }
    if (!canvasRefreshNonce) return;
    let cancelled = false;
    api.atelierCanvas.getState(projectId).then(data => {
      if (cancelled || !data?.elements?.length) return;
      setNodes(current => {
        const existingIds = new Set(current.map(node => String(node.data?.legacy_id || node.id)));
        let next = current;
        for (const element of data.elements) {
          if (existingIds.has(String(element.id))) continue;
          next = upsertFlowCanvasNode(next, element) as typeof current;
        }
        return next;
      });
    }).catch(() => {});
    return () => { cancelled = true; };
  }, [canvasRefreshNonce, projectId, setNodes]);

  const onConnect = useCallback((connection: Connection) => {
    setEdges(current => {
      const nextEdges = makeEditableRelationEdges(addEdge(connection, current));
      void saveCanvas({ nodes: getNodes() as typeof nodes, edges: nextEdges, viewport: getViewport() });
      return nextEdges;
    });
  }, [getNodes, getViewport, makeEditableRelationEdges, saveCanvas, setEdges]);


  const noteDragStop = useCallback(() => {
void saveCanvas({ nodes: getNodes() as typeof nodes, edges, viewport: getViewport() });
  }, [edges, getNodes, getViewport, nodes, saveCanvas]);

  const noteMoveEnd = useCallback((_: unknown, viewport: Viewport) => {
void saveCanvas({ nodes, edges, viewport: viewport || getViewport() });
  }, [edges, getViewport, nodes, saveCanvas]);

  const noteSelectionChange = useCallback(({ nodes: selectedNodes }: { nodes: Node[] }) => {
    const nextContext = buildSelectionContext(selectedNodes as typeof nodes);
    setSelectionContext(nextContext);
    setSelectedActionNode(selectedNodes.length === 1 ? selectedNodes[0] : null);
  }, [nodes]);


  const applyCanvasActionResult = useCallback((result: any) => {
    const nextElement = result?.node;
    const nextEdge = result?.edge;
    if (!nextElement || !nextEdge) return;

    const parent = getNodes().find(node => node.id === nextEdge.source_id || node.data.legacy_id === nextEdge.source_id);
    const positionedElement = {
      ...nextElement,
      x: parent ? parent.position.x + Number(parent.data.width || 260) + 80 : Number(nextElement.x || 0),
      y: parent ? parent.position.y : Number(nextElement.y || 0),
    };
    const nextNodes = upsertFlowCanvasNode(getNodes() as typeof nodes, positionedElement);
    const relationType = nextEdge.relation_type || nextEdge.metadata?.relation_type || 'variant_of';
    const variantEdge = {
      ...nextEdge,
      label: nextEdge.label || relationType,
      relation_type: relationType,
      metadata: nextEdge.metadata || {},
    };
    const flowEdge = makeEditableRelationEdges(legacyToFlowCanvas({
      elements: [],
      connections: [variantEdge],
      viewport: { x: 0, y: 0, scale: 1 },
    }).edges)[0];
    const nextEdges = edges.some(edge => edge.id === flowEdge.id)
      ? edges.map(edge => edge.id === flowEdge.id ? flowEdge : edge)
      : [...edges, flowEdge];

    setNodes(nextNodes);
    setEdges(nextEdges);
    void saveCanvas({ nodes: nextNodes, edges: nextEdges, viewport: getViewport() });
  }, [edges, getNodes, getViewport, makeEditableRelationEdges, nodes, saveCanvas, setEdges, setNodes]);

  const runCanvasAction = useCallback(async () => {
    const instruction = actionInstruction.trim();
    if (!instruction || selectionContext.length === 0 || actionProgress === 'processing') return;

    setActionError(null);
    setActionProgress('starting');
    try {
      const started = await api.canvasActions.start({
        project_id: projectId,
        instruction,
        selection: selectionContext,
      });
      const taskId = String(started.task_id);
      setActionTaskId(taskId);
      setActionProgress('processing');

      const source = new EventSource(api.progress.streamUrl(taskId));
      source.addEventListener('progress', event => {
        try {
          const data = JSON.parse((event as MessageEvent).data);
          setActionProgress(`${data.step || 'progress'} ${data.percent || 0}%`);
        } catch {
          setActionProgress('progress');
        }
      });
      source.addEventListener('done', event => {
        source.close();
        try {
          const data = JSON.parse((event as MessageEvent).data);
          setActionProgress(`done ${data.percent || 100}%`);
        } catch {
          setActionProgress('done');
        }
      });
      source.addEventListener('error', () => {
        source.close();
      });

      for (let attempt = 0; attempt < 40; attempt += 1) {
        const latest = await api.canvasActions.poll(taskId);
        if (latest.status === 'complete') {
          source.close();
          applyCanvasActionResult(latest.result);
          setActionProgress('complete');
          return;
        }
        if (latest.status === 'error') {
          source.close();
          throw new Error(latest.error || 'canvas action failed');
        }
        await new Promise(resolve => window.setTimeout(resolve, 250));
      }
      source.close();
      throw new Error('canvas action timed out');
    } catch (error) {
      setActionProgress('error');
      setActionError(error instanceof Error ? error.message : 'canvas action failed');
    }
  }, [actionInstruction, actionProgress, applyCanvasActionResult, projectId, selectionContext]);

  const [imgActionBusy, setImgActionBusy] = useState<string | null>(null);
  const handleImageAction = useCallback(async (id: string) => {
    const node = selectedActionNode;
    if (!node) return;
    const url = (node.data?.url || node.data?.preview_url) as string | undefined;
    if (id === 'download') {
      if (url) window.open(url, '_blank');
      return;
    }
    if (id === 'delete') {
      const remaining = getNodes().filter((n) => n.id !== node.id) as typeof nodes;
      setNodes(remaining);
      setSelectedActionNode(null);
      void saveCanvas({ nodes: remaining, edges, viewport: getViewport() });
      return;
    }
    if (id === 'front' || id === 'back') {
      setNodes((current) => {
        const zs = current.map((n) => Number(n.zIndex ?? 0));
        const z = id === 'front' ? Math.max(0, ...zs) + 1 : Math.min(0, ...zs) - 1;
        return current.map((n) => (n.id === node.id ? { ...n, zIndex: z } : n));
      });
      return;
    }
    if (id === 'cutout') {
      if (!url) return;
      setImgActionBusy('cutout');
      try {
        await api.canvasImageActions.run({
          project_id: projectId,
          asset_id: String(node.data?.legacy_id || node.id),
          action: 'cutout',
          image_url: url,
        });
        const data = await api.atelierCanvas.getState(projectId);
        if (data?.elements?.length) {
          setNodes((current) => {
            const ids = new Set(current.map((n) => String(n.data?.legacy_id || n.id)));
            let next = current;
            for (const el of data.elements) {
              if (ids.has(String(el.id))) continue;
              next = upsertFlowCanvasNode(next, el) as typeof current;
            }
            return next;
          });
        }
      } catch {
        /* 抠图失败,忽略 */
      } finally {
        setImgActionBusy(null);
      }
    }
  }, [selectedActionNode, getNodes, setNodes, setSelectedActionNode, saveCanvas, edges, getViewport, projectId, nodes]);

  const selectedActionAnchor = selectedActionNode ? actionBarAnchor({
    x: selectedActionNode.position.x,
    y: selectedActionNode.position.y,
    width: Number(selectedActionNode.data?.width || 240),
    height: Number(selectedActionNode.data?.height || 160),
  }, getViewport()) : null;

  return (
    <div data-lovart-canvas-shell data-flow-canvas-shell className="flex h-full flex-col" style={{ background: 'var(--lo-bg-canvas)' }}>
      <div className="flex h-12 shrink-0 items-center justify-between border-b border-gray-200 bg-white px-4">
        <div className="flex min-w-0 items-center gap-3">
          <span className="text-sm font-semibold text-gray-900">MOYAG Canvas</span>
          {loading && <span className="text-xs text-gray-400">加载中</span>}
          {loadError && <span className="text-xs text-orange-500">使用本地默认画布</span>}
        </div>
        <span className="text-xs text-gray-400">React Flow</span>
      </div>

      <div className="flex min-h-0 flex-1 overflow-hidden">
        <div data-flow-canvas-stage className="relative min-w-0 flex-1 overflow-hidden">
          {false && (
          <div
            data-ai-companion
            data-selected-count={selectionContext.length}
            data-selected-node-ids={selectionContext.map(item => item.nodeId).join(',')}
            data-selected-asset-ids={selectionContext.map(item => item.assetId || '').filter(Boolean).join(',')}
            className="absolute right-3 top-3 z-40 w-64 rounded-xl border border-gray-200 bg-white/95 p-3 text-xs text-gray-700 shadow-lg backdrop-blur"
          >
            <div className="flex items-center justify-between">
              <span className="font-medium text-gray-900">AI Companion</span>
              <span data-ai-selected-count className="rounded bg-orange-50 px-2 py-0.5 text-orange-600">选中 {selectionContext.length}</span>
            </div>
            <div data-ai-selection-context className="mt-2 space-y-1 text-[10px] text-gray-500">
              {selectionContext.length === 0 ? (
                <div>选择画布节点后，我会把节点和素材上下文带入对话。</div>
              ) : selectionContext.map(item => (
                <div key={item.nodeId} data-ai-selection-item data-node-id={item.nodeId} data-asset-id={item.assetId || ''} className="truncate">
                  {item.label || item.nodeId} · {item.assetId || 'no-asset-id'}
                </div>
              ))}
            </div>
            {selectionContext.length === 1 && (
              <div className="mt-2 space-y-2">
                <input
                  data-ai-action-input
                  value={actionInstruction}
                  onChange={event => setActionInstruction(event.target.value)}
                  placeholder="例如：背景更暖，产品更突出"
                  className="w-full rounded-lg border border-gray-200 px-2 py-1 text-[11px] text-gray-700 outline-none focus:border-orange-300"
                />
                <button
                  data-ai-local-edit-trigger
                  data-ai-action-run
                  data-node-id={selectionContext[0].nodeId}
                  data-asset-id={selectionContext[0].assetId || ''}
                  data-task-id={actionTaskId || ''}
                  onClick={() => { void runCanvasAction(); }}
                  disabled={!actionInstruction.trim() || actionProgress === 'processing'}
                  className="w-full rounded-lg border border-gray-200 px-2 py-1 text-[11px] text-gray-600 hover:bg-gray-50 disabled:opacity-50"
                >
                  用所选素材局部修改
                </button>
              </div>
            )}
            <div data-ai-action-task-id={actionTaskId || ''} data-ai-action-progress={actionProgress} className="mt-2 text-[10px] text-gray-400">
              {actionError || actionProgress}
            </div>
          </div>
          )}
          {selectedActionAnchor && <ImageActionBar left={selectedActionAnchor.left} top={selectedActionAnchor.top} onAction={handleImageAction} busy={imgActionBusy} />}
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeDragStop={noteDragStop}
            onMoveEnd={noteMoveEnd}
            onSelectionChange={noteSelectionChange}
            defaultViewport={initialViewport}
            minZoom={0.15}
            maxZoom={3}
            panOnDrag
            zoomOnScroll
            zoomOnPinch
            zoomOnDoubleClick={false}
            selectionOnDrag
            multiSelectionKeyCode={['Meta', 'Control', 'Shift']}
            nodesDraggable
            nodesConnectable={true}
            elementsSelectable
            className="bg-[#f5f5f5]"
          >
            <Background gap={32} size={1} color="rgba(0,0,0,0.08)" />
            <Controls position="bottom-right" showInteractive={false} />
            <MiniMap position="bottom-left" pannable zoomable nodeStrokeWidth={2} />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}

export default function CanvasFlow(props: CanvasFlowProps) {
  return (
    <ReactFlowProvider>
      <CanvasFlowInner {...props} />
    </ReactFlowProvider>
  );
}
