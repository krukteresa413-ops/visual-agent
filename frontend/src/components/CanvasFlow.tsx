import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Background,
  Controls,
  MiniMap,
  Panel,
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
import GeneratorNode from './nodes/GeneratorNode';
import ShapeNode from './nodes/ShapeNode';
import TextNode from './nodes/TextNode';
import MarkNode from './nodes/MarkNode';
import FreedrawNode from './nodes/FreedrawNode';
import FrameNode from './nodes/FrameNode';
import FreedrawLayer from './canvas/FreedrawLayer';
import DragCreateLayer from './canvas/DragCreateLayer';
import { getStroke, getSvgPathFromStroke, strokeOptions } from '../canvas/freehand';
import ImageActionBar from './canvas/ImageActionBar';
import CanvasToolbar from './canvas/CanvasToolbar';
import CanvasPropertyPanel, { type PropertyPanelKind } from './canvas/CanvasPropertyPanel';
import EditableRelationEdge from './canvas/EditableRelationEdge';
import { actionBarAnchor } from './canvas/actionBarAnchor';
import type CanvasViewLegacy from './CanvasViewLegacy';

type CanvasFlowProps = React.ComponentProps<typeof CanvasViewLegacy>;

const emptyFlow: FlowCanvasState = {
  nodes: [],
  edges: [],
  viewport: { x: 0, y: 0, zoom: 1 },
};

// 选中后弹属性面板的节点类型(RF node.type);其余类型(image/generator/frame/mark)不弹。
const NODE_PANEL_KINDS = new Set(['text', 'shape', 'freedraw']);

// 工具栏「快速图形」下拉 action → ShapeNode 形状种类
const SHAPE_MAP: Record<string, string> = {
  'shape-rect': 'rect',
  'shape-ellipse': 'ellipse',
  'shape-line': 'line',
  'shape-arrow': 'arrow',
  'shape-polygon': 'diamond',
  'shape-star': 'star',
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
  const nodeTypes = useMemo(() => ({ canvasElement: AssetNode, generator: GeneratorNode, shape: ShapeNode, text: TextNode, mark: MarkNode, freedraw: FreedrawNode, frame: FrameNode }), []);
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
  // 图二:二次编辑改用画布内弹窗 + 失败/无新图的前端提示(toast)
  const [reeditNodeId, setReeditNodeId] = useState<string | null>(null);
  const [reeditText, setReeditText] = useState('');
  const [reeditBusy, setReeditBusy] = useState(false);
  const [canvasNotice, setCanvasNotice] = useState<{ kind: 'info' | 'warn'; text: string } | null>(null);
  const { getNodes, getEdges, getViewport, screenToFlowPosition } = useReactFlow();
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


  const applyCanvasActionResult = useCallback((result: any): boolean => {
    const nextElement = result?.node;
    const nextEdge = result?.edge;
    // 图二:complete 不等于出图。网关降级时 result 可能没有 node/edge -> 无新图
    if (!nextElement || !nextEdge) return false;

    const parent = getNodes().find(node => node.id === nextEdge.source_id || node.data.legacy_id === nextEdge.source_id);
    const positionedElement = {
      ...nextElement,
      x: parent ? parent.position.x + Number(parent.data.width || 260) + 80 : Number(nextElement.x || 0),
      y: parent ? parent.position.y : Number(nextElement.y || 0),
    };
    const nextNodes = upsertFlowCanvasNode(getNodes() as typeof nodes, positionedElement);
    const relationType = nextEdge.relation_type || nextEdge.metadata?.relation_type || 'variant_of';
    // 连线标签凝练改动次数:以源图为起点的第几次修改
    const editCount = parent ? edges.filter((e) => e.source === parent.id).length + 1 : 1;
    const editLabel = `第${editCount}次修改`;
    const variantEdge = {
      ...nextEdge,
      label: editLabel,
      relation_type: relationType,
      metadata: { ...(nextEdge.metadata || {}), edit_index: editCount },
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
    return true;
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

  // 二次编辑:对指定节点用修改指令做 img2img,产出新图并连「第N次修改」线(复用 applyCanvasActionResult)
  const reEdit = useCallback(async (nodeId: string, instruction: string) => {
    const node = getNodes().find((n) => n.id === nodeId);
    if (!node || !instruction.trim()) return;
    // 图二:视频的二次编辑 = 按新指令走异步视频管线重出一段,并轮询画布把新视频并入
    if (String((node.data as { type?: string })?.type) === 'video') {
      setReeditBusy(true);
      setActionProgress('processing');
      setCanvasNotice({ kind: 'info', text: '正在按新指令重新生成视频(约 1-2 分钟),完成后自动加入画布…' });
      try {
        const before = new Set(getNodes().map((n) => String((n.data as { legacy_id?: string })?.legacy_id || n.id)));
        await api.generation.quickGenerate({ prompt: instruction.trim(), project_id: projectId, agent_mode: 'video-gen' });
        let landed = false;
        for (let i = 0; i < 20; i += 1) {
          await new Promise((r) => window.setTimeout(r, 6000));
          const data = await api.atelierCanvas.getState(projectId);
          const fresh = (data?.elements || []).filter((el: { id: string }) => !before.has(String(el.id)));
          if (fresh.length) {
            setNodes((current) => { let next = current; for (const el of fresh) next = upsertFlowCanvasNode(next, el) as typeof current; return next; });
            setActionProgress('complete');
            setCanvasNotice({ kind: 'info', text: '新视频已生成并加入画布' });
            landed = true;
            break;
          }
        }
        if (!landed) setCanvasNotice({ kind: 'warn', text: '视频仍在渲染,稍后会自动出现;也可手动刷新查看' });
      } catch {
        setActionProgress('error');
        setCanvasNotice({ kind: 'warn', text: '视频生成失败,请稍后重试' });
      } finally {
        setReeditBusy(false);
      }
      return;
    }
    const selection = buildSelectionContext([node] as typeof nodes);
    setActionProgress('processing');
    setReeditBusy(true);
    setCanvasNotice({ kind: 'info', text: '正在二次编辑,生成新图中…' });
    try {
      const started = await api.canvasActions.start({ project_id: projectId, instruction: instruction.trim(), selection });
      const taskId = String(started.task_id);
      for (let i = 0; i < 80; i += 1) {
        const latest = await api.canvasActions.poll(taskId);
        if (latest.status === 'complete') {
          // 图二:complete 后要确认确实产出了新图;没出图给前端提示
          const applied = applyCanvasActionResult(latest.result);
          if (applied) {
            setActionProgress('complete');
            setCanvasNotice({ kind: 'info', text: '已生成新图,并连上「修改」关系线' });
          } else {
            setActionProgress('error');
            setCanvasNotice({ kind: 'warn', text: '图像服务暂时不稳定,本次没能生成新图,请稍后重试' });
          }
          return;
        }
        if (latest.status === 'error') {
          setActionProgress('error');
          setCanvasNotice({ kind: 'warn', text: '图像服务暂时不稳定,本次没能生成新图,请稍后重试' });
          return;
        }
        await new Promise((r) => window.setTimeout(r, 500));
      }
      setActionProgress('error');
      setCanvasNotice({ kind: 'warn', text: '生成超时,图像服务可能繁忙,请稍后重试' });
    } catch {
      setActionProgress('error');
      setCanvasNotice({ kind: 'warn', text: '图像服务暂时不稳定,本次没能生成新图,请稍后重试' });
    } finally {
      setReeditBusy(false);
    }
  }, [getNodes, projectId, applyCanvasActionResult, setNodes]);

  // 图二:✎ 编辑 -> 打开画布内弹窗(替代原生 window.prompt)
  useEffect(() => {
    const handler = (e: Event) => {
      const nodeId = (e as CustomEvent).detail?.nodeId;
      if (!nodeId) return;
      setReeditText('');
      setReeditNodeId(String(nodeId));
    };
    window.addEventListener('moyag:reedit', handler as EventListener);
    return () => window.removeEventListener('moyag:reedit', handler as EventListener);
  }, []);

  const confirmReedit = () => {
    const id = reeditNodeId;
    const text = reeditText.trim();
    if (!id || !text) return;
    setReeditNodeId(null);
    void reEdit(id, text);
  };

  // 提示自动消失(进行中的不消失,直到被结果替换)
  useEffect(() => {
    if (!canvasNotice || reeditBusy) return;
    const t = window.setTimeout(() => setCanvasNotice(null), 6000);
    return () => window.clearTimeout(t);
  }, [canvasNotice, reeditBusy]);

  const [imgActionBusy, setImgActionBusy] = useState<string | null>(null);
  const handleImageAction = useCallback(async (id: string) => {
    const node = selectedActionNode;
    if (!node) return;
    // 图二:画布节点把图存在 thumbnail_url / asset_ref.url(AssetNode 即用此渲染),
    // 旧代码只读 url/preview_url -> 永远 undefined -> 下载/抠图点了没反应。健壮取值。
    const assetRef = node.data?.asset_ref as { url?: string } | undefined;
    const url = (node.data?.thumbnail_url || node.data?.url || node.data?.preview_url || assetRef?.url) as string | undefined;
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

  // 图二 / Phase A:画布底部工具栏 — 选择/上传图已接;AI图/AI视频改为画布内「生成节点」(GeneratorNode)
  const [toolMode, setToolMode] = useState<string>('select');
  // 文字/标记/图形:进入「放置」模式,下一次点画布落节点
  const [pendingTool, setPendingTool] = useState<string | null>(null);
  const toolFileRef = useRef<HTMLInputElement | null>(null);

  // 画笔「下一笔」的颜色/笔宽(自由绘把笔宽烤进几何,必须画前设;由属性面板控制)
  const [penColor, setPenColor] = useState('#111827');
  const [penSize, setPenSize] = useState(6);

  // 属性面板改 metadata 走高频 onChange(取色器/滑块);保存按 300ms 防抖,避免刷爆后端
  // (saveCanvas 按 JSON 去重但不做时间防抖)。
  const propSaveTimer = useRef<number | null>(null);
  const schedulePropSave = useCallback(() => {
    if (propSaveTimer.current) window.clearTimeout(propSaveTimer.current);
    propSaveTimer.current = window.setTimeout(() => {
      void saveCanvas({ nodes: getNodes() as typeof nodes, edges: getEdges() as typeof edges, viewport: getViewport() });
    }, 300);
  }, [saveCanvas, getNodes, getEdges, getViewport]);
  useEffect(() => () => { if (propSaveTimer.current) window.clearTimeout(propSaveTimer.current); }, []);

  // 把样式 patch 合并进指定节点的 data.metadata;节点已从 metadata 读样式,会即时重渲染。
  const updateNodeMeta = useCallback((nodeId: string, patch: Record<string, unknown>) => {
    setNodes((cur) => cur.map((n) => (n.id === nodeId
      ? { ...n, data: { ...n.data, metadata: { ...((n.data.metadata as Record<string, unknown>) || {}), ...patch } } }
      : n)));
    schedulePropSave();
  }, [setNodes, schedulePropSave]);

  const nextNodePos = () => { const n = getNodes().length; return { x: 80 + (n % 5) * 360, y: 80 + Math.floor(n / 5) * 320 }; };

  const handleToolUploadFile = async (file: File | undefined) => {
    if (!file) return;
    setCanvasNotice({ kind: 'info', text: '正在上传图片…' });
    try {
      const form = new FormData(); form.append('file', file);
      const res = await api.upload.image(form) as { url?: string };
      const url = res?.url; if (!url) throw new Error('no url');
      const pos = nextNodePos();
      const el = { id: 'upload_' + String(getNodes().length) + '_' + url.slice(-10), type: 'image', label: file.name, x: pos.x, y: pos.y, width: 280, height: 280, thumbnail_url: url, asset_ref: { type: 'image', url }, metadata: { source: 'toolbar-upload' } };
      setNodes((cur) => { const next = upsertFlowCanvasNode(cur, el as never) as typeof cur; void saveCanvas({ nodes: next, edges, viewport: getViewport() }); return next; });
      setCanvasNotice({ kind: 'info', text: '图片已加入画布' });
    } catch { setCanvasNotice({ kind: 'warn', text: '上传失败,请重试' }); }
  };

  // Phase A:画布内「AI 图/视频生成节点」的生成动作(由节点通过 data.onGenerate 调用)。
  // 复用已验证的 quickGenerate → 轮询 getState diff 管线;拿到后端新元素后,把该「生成节点」
  // 就地替换成标准图片/视频节点(沿用后端真实 id/asset_ref,从而继承下载/抠图/二次编辑/关系线);
  // saveCanvas 是整张画布的权威覆盖写,因此后端临时落下的同一元素不会重复。
  const onGeneratorRun = useCallback(async (
    nodeId: string,
    params: { prompt: string; reference_image_url?: string; width: number; height: number; ratio: string; brief: Record<string, unknown> },
  ) => {
    const startNode = getNodes().find((n) => n.id === nodeId);
    if (!startNode) return;
    const kind = (startNode.data as { kind?: string })?.kind === 'video' ? 'video' : 'image';
    const prompt = params.prompt.trim();
    if (!prompt) return;

    setNodes((cur) => cur.map((n) => (n.id === nodeId ? { ...n, data: { ...n.data, status: 'generating' as const, error: undefined } } : n)));
    const before = new Set(getNodes().map((n) => String((n.data as { legacy_id?: string })?.legacy_id || n.id)));
    const fail = (text: string) => setNodes((cur) => cur.map((n) => (n.id === nodeId ? { ...n, data: { ...n.data, status: 'error' as const, error: text } } : n)));

    try {
      await api.generation.quickGenerate({
        prompt,
        project_id: projectId,
        agent_mode: kind === 'video' ? 'video-gen' : 'image-gen',
        auto_model: true,
        brief: params.brief,
        ...(params.reference_image_url ? { reference_image_url: params.reference_image_url } : {}),
      });
      const rounds = kind === 'video' ? 25 : 16;
      for (let i = 0; i < rounds; i += 1) {
        await new Promise((r) => window.setTimeout(r, kind === 'video' ? 6000 : 3000));
        const data = await api.atelierCanvas.getState(projectId);
        const fresh = (data?.elements || []).filter((el: { id: string }) => !before.has(String(el.id)));
        if (!fresh.length) continue;
        const gen = getNodes().find((n) => n.id === nodeId);
        const px = gen ? gen.position.x : startNode.position.x;
        const py = gen ? gen.position.y : startNode.position.y;
        const [first, ...rest] = fresh;
        const positioned = { ...first, x: px, y: py, width: params.width, height: params.height };
        setNodes((cur) => {
          let next = cur.filter((n) => n.id !== nodeId);
          next = upsertFlowCanvasNode(next, positioned as never) as typeof cur;
          rest.forEach((extra: { id: string }, idx: number) => {
            next = upsertFlowCanvasNode(next, { ...extra, x: px + (params.width + 40) * (idx + 1), y: py } as never) as typeof cur;
          });
          void saveCanvas({ nodes: next, edges: getEdges() as typeof edges, viewport: getViewport() });
          return next;
        });
        return;
      }
      fail(kind === 'video' ? '视频仍在渲染,请稍后重试或刷新画布' : '生成超时,图像服务可能繁忙,请稍后重试');
    } catch {
      fail(kind === 'video' ? '视频生成失败,请稍后重试' : '生成失败,请稍后重试');
    }
  }, [getNodes, getEdges, getViewport, projectId, saveCanvas, setNodes]);

  const dropGenerator = (kind: 'image' | 'video') => {
    const pos = nextNodePos();
    const width = kind === 'video' ? 360 : 300;
    const height = kind === 'video' ? 203 : 300;
    const id = `gen_${kind}_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
    const node = { id, type: 'generator', position: pos, width, data: { kind, status: 'idle', width, height, onGenerate: onGeneratorRun } };
    setNodes((cur) => [...cur, node as never]);
    setCanvasNotice({ kind: 'info', text: kind === 'video' ? '已添加视频生成器,填入描述后点「生成」' : '已添加图片生成器,填入描述后点「生成」' });
  };

  // 工具栏动作分发(action id 由 CanvasToolbar 的下拉/按钮给出)
  const handleTool = (action: string) => {
    if (action === 'select') { setPendingTool(null); setToolMode('select'); return; }
    if (action === 'move') { setPendingTool(null); setToolMode('move'); return; }
    if (action === 'upload-image') { setPendingTool(null); toolFileRef.current?.click(); return; }
    if (action === 'upload-video') { setCanvasNotice({ kind: 'info', text: '上传视频即将上线' }); return; }
    if (action === 'ai-image') { setPendingTool(null); dropGenerator('image'); return; }
    if (action === 'ai-video') { setPendingTool(null); dropGenerator('video'); return; }
    // 画笔:进入持续绘制模式(覆盖层),双击/换工具退出;模式与颜色/笔宽由属性面板呈现
    if (action === 'pen') { setPendingTool('pen'); return; }
    // 标记:点状批注,点击放置;文字/画板/图形:拖拽创建(覆盖层有自带提示,不再弹 toast)
    if (action === 'mark') {
      setPendingTool('mark');
      setCanvasNotice({ kind: 'info', text: '在画布上点击放置标记' });
      return;
    }
    if (action === 'text' || action === 'frame' || action.startsWith('shape-')) {
      setPendingTool(action);
      return;
    }
    setCanvasNotice({ kind: 'info', text: '该工具即将上线' });
  };

  // 标记/图钉是点状批注(无尺寸),保留点击放置;图形/文字/画板走拖拽层,画笔走画笔层。
  const onPaneClick = useCallback((e: React.MouseEvent) => {
    if (pendingTool !== 'mark') return;
    const pos = screenToFlowPosition({ x: e.clientX, y: e.clientY });
    const id = `mark_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
    const el = { id, type: 'mark', label: '批注', x: pos.x, y: pos.y, width: 160, height: 32 };
    setNodes((cur) => {
      const next = upsertFlowCanvasNode(cur, el as never) as typeof cur;
      void saveCanvas({ nodes: next, edges: getEdges() as typeof edges, viewport: getViewport() });
      return next;
    });
    setPendingTool(null);
  }, [pendingTool, screenToFlowPosition, setNodes, saveCanvas, getEdges, getViewport]);

  // 拖拽创建:图形/文字/画板。拖出的矩形 = 节点包围盒;拖动过小(dragged=false)落默认尺寸兜底。
  // 线/箭头记录拖拽终点所在角(metadata.endCorner: tl/tr/bl/br),供 ShapeNode 定线向与箭头朝向。
  const onDragCreateComplete = useCallback((start: { x: number; y: number }, end: { x: number; y: number }, dragged: boolean) => {
    const tool = pendingTool;
    if (!tool) return;
    const x = Math.min(start.x, end.x);
    const y = Math.min(start.y, end.y);
    const dw = Math.round(Math.abs(end.x - start.x));
    const dh = Math.round(Math.abs(end.y - start.y));
    const id = `${tool}_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
    let el: Record<string, unknown>;
    if (tool === 'text') {
      el = dragged
        ? { id, type: 'text', label: '文字', x, y, width: Math.max(48, dw), height: Math.max(28, dh), metadata: { fontSize: 18 } }
        : { id, type: 'text', label: '文字', x: start.x, y: start.y, width: 120, height: 40, metadata: { fontSize: 18 } };
    } else if (tool === 'frame') {
      el = dragged
        ? { id, type: 'frame', label: '画板', x, y, width: Math.max(120, dw), height: Math.max(90, dh) }
        : { id, type: 'frame', label: '画板', x: start.x, y: start.y, width: 400, height: 300 };
    } else {
      const shape = SHAPE_MAP[tool] || 'rect';
      const isLine = shape === 'line' || shape === 'arrow';
      const meta: Record<string, unknown> = { shape };
      if (isLine && dragged) meta.endCorner = (end.y - start.y >= 0 ? 'b' : 't') + (end.x - start.x >= 0 ? 'r' : 'l');
      el = dragged
        ? { id, type: 'shape', label: '', x, y, width: Math.max(12, dw), height: Math.max(12, dh), metadata: meta }
        : { id, type: 'shape', label: '', x: start.x, y: start.y, width: 160, height: isLine ? 100 : 120, metadata: meta };
    }
    setNodes((cur) => {
      const next = upsertFlowCanvasNode(cur, el as never) as typeof cur;
      void saveCanvas({ nodes: next, edges: getEdges() as typeof edges, viewport: getViewport() });
      return next;
    });
    setPendingTool(null);
  }, [pendingTool, setNodes, saveCanvas, getEdges, getViewport]);

  // 画笔落定:把 flow 采样点 → 包围盒定位 + perfect-freehand 轮廓 → FreedrawNode
  const onFreedrawComplete = useCallback((flowPts: Array<{ x: number; y: number }>, color: string, baseSize: number) => {
    if (flowPts.length < 2) return;
    const xs = flowPts.map((p) => p.x);
    const ys = flowPts.map((p) => p.y);
    const minX = Math.min(...xs);
    const minY = Math.min(...ys);
    const maxX = Math.max(...xs);
    const maxY = Math.max(...ys);
    const pad = baseSize * 2;
    const rel = flowPts.map((p) => [p.x - minX + pad, p.y - minY + pad]);
    const path = getSvgPathFromStroke(getStroke(rel, strokeOptions(baseSize)));
    const width = maxX - minX + pad * 2;
    const height = maxY - minY + pad * 2;
    const id = `freedraw_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
    const el = { id, type: 'freedraw', label: '', x: minX - pad, y: minY - pad, width, height, metadata: { path, color } };
    setNodes((cur) => {
      const next = upsertFlowCanvasNode(cur, el as never) as typeof cur;
      void saveCanvas({ nodes: next, edges: getEdges() as typeof edges, viewport: getViewport() });
      return next;
    });
  }, [setNodes, saveCanvas, getEdges, getViewport]);

  // Esc 退出任意「放置/画笔」模式
  useEffect(() => {
    if (!pendingTool) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setPendingTool(null); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [pendingTool]);

  // 选中单个 文字/图形/自由绘 节点时弹属性面板;实时从 nodes 取该节点
  // (selectedActionNode 是选中那刻的快照,改样式后会过时,故按 id 取最新)。
  const selectedId = selectedActionNode?.id ?? null;
  const liveSelected = useMemo(
    () => (selectedId ? nodes.find((n) => n.id === selectedId) ?? null : null),
    [nodes, selectedId],
  );
  const showPenPanel = pendingTool === 'pen';
  const selectedPanelKind: PropertyPanelKind | null = !showPenPanel && liveSelected && NODE_PANEL_KINDS.has(String(liveSelected.type))
    ? (String(liveSelected.type) as PropertyPanelKind)
    : null;

  // 生成节点(type==='generator')是表单卡片,不应弹出图片操作条(下载/抠图/二次编辑)。
  const selectedActionAnchor = (selectedActionNode && selectedActionNode.type !== 'generator') ? actionBarAnchor({
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
          {/* 图二:画布内二次编辑弹窗(替代浏览器原生 prompt) */}
          {reeditNodeId && (
            <div className="absolute inset-0 z-50 grid place-items-center bg-black/40 p-4" onClick={() => setReeditNodeId(null)}>
              <div className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-5 shadow-2xl" onClick={(e) => e.stopPropagation()}>
                <div className="mb-1 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-gray-900">✎ 二次编辑</h3>
                  <button onClick={() => setReeditNodeId(null)} className="text-gray-400 transition-colors hover:text-gray-700">✕</button>
                </div>
                <p className="mb-3 text-xs text-gray-500">描述你想怎么改这张图,例如「换成男性模特」「背景换成夜景」。</p>
                <textarea
                  autoFocus
                  value={reeditText}
                  onChange={(e) => setReeditText(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); confirmReedit(); } }}
                  rows={3}
                  placeholder="描述修改需求…(Ctrl/⌘+Enter 提交)"
                  className="w-full resize-none rounded-xl border border-gray-200 px-3 py-2 text-sm text-gray-800 outline-none focus:border-purple-400"
                />
                <div className="mt-3 flex justify-end gap-2">
                  <button onClick={() => setReeditNodeId(null)} className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs text-gray-600 transition-colors hover:bg-gray-50">取消</button>
                  <button onClick={confirmReedit} disabled={!reeditText.trim()} className="rounded-lg bg-purple-600 px-4 py-1.5 text-xs font-medium text-white transition-colors hover:bg-purple-500 disabled:opacity-50">确定</button>
                </div>
              </div>
            </div>
          )}
          {/* 图二:画布内置提示(生成中 / 失败 / 无新图) */}
          {canvasNotice && (
            <div className={`pointer-events-none absolute left-1/2 top-4 z-40 -translate-x-1/2 rounded-full border px-4 py-2 text-xs shadow-lg ${canvasNotice.kind === 'warn' ? 'border-amber-200 bg-amber-50 text-amber-700' : 'border-transparent bg-gray-900/90 text-white'}`}>
              <span className="inline-flex items-center gap-2">
                {reeditBusy && <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-white/40 border-t-white" />}
                {canvasNotice.kind === 'warn' ? '⚠ ' : ''}{canvasNotice.text}
              </span>
            </div>
          )}
          {/* 属性面板:画笔(画前设色/笔宽)或选中节点(就地改 metadata 样式)。顶部居中浮条。 */}
          {(showPenPanel || selectedPanelKind) && (
            <div className="pointer-events-none absolute left-1/2 top-3 z-40 -translate-x-1/2">
              {showPenPanel ? (
                <CanvasPropertyPanel
                  kind="pen"
                  values={{ color: penColor, size: penSize }}
                  onChange={(p) => { if (typeof p.color === 'string') setPenColor(p.color); if (typeof p.size === 'number') setPenSize(p.size); }}
                  onExitPen={() => setPendingTool(null)}
                />
              ) : liveSelected && selectedPanelKind ? (
                <CanvasPropertyPanel
                  kind={selectedPanelKind}
                  values={(liveSelected.data.metadata as Record<string, unknown>) || {}}
                  onChange={(p) => updateNodeMeta(liveSelected.id, p)}
                />
              ) : null}
            </div>
          )}
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
          {selectedActionAnchor && <ImageActionBar left={selectedActionAnchor.left} top={selectedActionAnchor.top} onAction={handleImageAction} busy={imgActionBusy} elementType={String((selectedActionNode?.data as { type?: string })?.type || '')} />}
          <input ref={toolFileRef} type="file" accept="image/*" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (e.target) e.target.value = ''; void handleToolUploadFile(f || undefined); }} />
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
            onPaneClick={onPaneClick}
            defaultViewport={initialViewport}
            minZoom={0.15}
            maxZoom={3}
            panOnDrag={toolMode === 'move' ? true : [1, 2]}
            zoomOnScroll
            zoomOnPinch
            zoomOnDoubleClick={false}
            selectionOnDrag={toolMode !== 'move'}
            multiSelectionKeyCode={['Meta', 'Control', 'Shift']}
            nodesDraggable={toolMode !== 'move'}
            nodesConnectable={true}
            elementsSelectable
            className={`bg-[#f5f5f5] ${pendingTool ? 'cursor-crosshair' : toolMode === 'move' ? 'cursor-grab' : ''}`}
          >
            <Background gap={32} size={1} color="rgba(0,0,0,0.08)" />
            <Controls position="bottom-right" showInteractive={false} />
            <MiniMap position="bottom-left" pannable zoomable nodeStrokeWidth={2} />
            <Panel position="bottom-center">
              <CanvasToolbar onTool={handleTool} />
            </Panel>
          </ReactFlow>
          {pendingTool === 'pen' && (
            <FreedrawLayer color={penColor} size={penSize} onComplete={onFreedrawComplete} onExit={() => setPendingTool(null)} />
          )}
          {/* 图形/文字/画板:拖拽创建(标记走点击,画笔走画笔层) */}
          {pendingTool && pendingTool !== 'pen' && pendingTool !== 'mark' && (
            <DragCreateLayer onComplete={onDragCreateComplete} />
          )}
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
