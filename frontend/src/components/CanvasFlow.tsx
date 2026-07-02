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
import { flowToLegacyCanvas, legacyToFlowCanvas, upsertFlowCanvasNode } from '../canvas/canvasAdapters';
import { absolutePosition, fitFrameToChildren, frameUnderPoint, orderByParent, resolveContainment } from '../canvas/frameNesting';
import { getHelperLines } from '../canvas/helperLines';
import { reorderLayer, type LayerOp } from '../canvas/layerOrder';
import { DropTargetContext } from '../canvas/dropTargetContext';
import { useCanvasPersistence } from '../canvas/useCanvasPersistence';
import { useCanvasHistory } from '../canvas/useCanvasHistory';
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
import CanvasToolbarDock from './canvas/CanvasToolbarDock';
import GeneratorComposer, { type GenerateParams } from './canvas/GeneratorComposer';
import FontComposer, { type FontParams } from './canvas/FontComposer';
import HelperLinesOverlay from './canvas/HelperLinesOverlay';
import CanvasPropertyPanel, { type PropertyPanelKind } from './canvas/CanvasPropertyPanel';
import EditableRelationEdge from './canvas/EditableRelationEdge';
import { actionBarAnchor } from './canvas/actionBarAnchor';
import type CanvasViewLegacy from './CanvasViewLegacy';

type CanvasFlowProps = React.ComponentProps<typeof CanvasViewLegacy> & { canvasId?: number };

const emptyFlow: FlowCanvasState = {
  nodes: [],
  edges: [],
  viewport: { x: 0, y: 0, zoom: 1 },
};

// 选中后弹属性面板的节点类型(RF node.type);其余类型(image/generator/frame/mark)不弹。
const NODE_PANEL_KINDS = new Set(['text', 'shape', 'freedraw']);

// 对齐吸附阈值(屏幕像素)。转流坐标时按 SNAP_PX / zoom,保证任意缩放下手感恒定。
const SNAP_PX = 6;

// 工具栏「快速图形」下拉 action → ShapeNode 形状种类
const SHAPE_MAP: Record<string, string> = {
  'shape-rect': 'rect',
  'shape-ellipse': 'ellipse',
  'shape-line': 'line',
  'shape-arrow': 'arrow',
  'shape-polygon': 'polygon',
  'shape-star': 'star',
};

// 画板尺寸预设(flow 单位):选中即在视口中心落一个该尺寸的画板。
const FRAME_PRESETS: Record<string, { w: number; h: number; label: string }> = {
  'frame-1-1': { w: 1080, h: 1080, label: '方形画板' },
  'frame-9-16': { w: 1080, h: 1920, label: '竖屏画板' },
  'frame-16-9': { w: 1920, h: 1080, label: '横屏画板' },
  'frame-a4': { w: 794, h: 1123, label: 'A4 画板' },
  'frame-web': { w: 1440, h: 1024, label: '网页画板' },
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

// 聚焦某节点内的 contentEditable(文字节点)并把光标置末尾;用于「文字创建后 / 双击直接可输入」。
function focusContentEditable(nodeId: string) {
  const host = document.querySelector(`.react-flow__node[data-id="${nodeId}"] [contenteditable]`) as HTMLElement | null;
  if (!host) return;
  host.focus();
  const range = document.createRange();
  range.selectNodeContents(host);
  range.collapse(false);
  const sel = window.getSelection();
  sel?.removeAllRanges();
  sel?.addRange(range);
}

function CanvasFlowInner(props: CanvasFlowProps) {
  const projectId = props.projectId || 2;
  const canvasId = props.canvasId;  // Phase C: 未定=项目默认画布(后端 resolve)
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
  // AI 图/视频「撰写浮窗」:{kind} 为打开、null 为关闭(替代原先往画布丢生成节点);genBusy=生成中(令顶部进度提示不自动消失)。
  const [genComposer, setGenComposer] = useState<{ kind: 'image' | 'video' } | null>(null);
  const [genBusy, setGenBusy] = useState(false);
  // AI 字体生成器撰写浮窗开关(点工具栏 ai-text 打开;点「生成」才调后端,关闭零落地)。
  const [fontComposer, setFontComposer] = useState(false);
  const { getNodes, getEdges, getViewport, screenToFlowPosition, fitView } = useReactFlow();
  // 对齐吸附:拖拽中显示的参考线(绝对流坐标);拖拽结束清空。
  const [helperLines, setHelperLines] = useState<{ vertical?: number; horizontal?: number }>({});
  // 拖入高亮:拖动中被拖节点会归属到的目标画板 id(经 Context 下发给 FrameNode);非拖动/未命中为 null。
  const [dropTargetId, setDropTargetId] = useState<string | null>(null);
  const { saveCanvas, rememberSavedCanvas } = useCanvasPersistence(projectId, canvasId);

  // L0 编辑器地基:统一提交层 + 撤销/重做。所有「语义操作完成」点都走 commit(更新 state + 入撤销栈 + 持久化);
  // Undo/Redo 直接还原快照(绕过 commit,故撤销动作本身不会再被记进历史)。快照存 React Flow 运行时引用,
  // 配合不可变更新即可一步还原,且保留节点上的 onGenerate/onLabelCommit 等函数引用。
  type CanvasSnapshot = { nodes: typeof nodes; edges: typeof edges };
  const { reset: resetHistory, push: pushHistory, undo: undoHistory, redo: redoHistory, canUndo, canRedo } = useCanvasHistory<CanvasSnapshot>();

  const commit = useCallback((next: { nodes?: typeof nodes; edges?: typeof edges }) => {
    const nextNodes = next.nodes ?? (getNodes() as typeof nodes);
    const nextEdges = next.edges ?? (getEdges() as typeof edges);
    if (next.nodes) setNodes(nextNodes);
    if (next.edges) setEdges(nextEdges);
    pushHistory({ nodes: nextNodes, edges: nextEdges });
    void saveCanvas({ nodes: nextNodes, edges: nextEdges, viewport: getViewport() });
  }, [getNodes, getEdges, getViewport, pushHistory, saveCanvas, setNodes, setEdges]);

  const applySnapshot = useCallback((snap: CanvasSnapshot) => {
    setNodes(snap.nodes);
    setEdges(snap.edges);
    void saveCanvas({ nodes: snap.nodes, edges: snap.edges, viewport: getViewport() });
  }, [getViewport, saveCanvas, setNodes, setEdges]);

  const handleUndo = useCallback(() => { const s = undoHistory(); if (s) applySnapshot(s); }, [applySnapshot, undoHistory]);
  const handleRedo = useCallback(() => { const s = redoHistory(); if (s) applySnapshot(s); }, [applySnapshot, redoHistory]);

  // 删除选中:含被删画板的子节点 + 关联边一并清除,走 commit(可撤销 + 持久化)。
  const deleteSelected = useCallback(() => {
    const all = getNodes() as typeof nodes;
    const removed = new Set(all.filter((n) => n.selected).map((n) => n.id));
    if (removed.size === 0) return;
    // 连带删除挂在被删画板下的子节点(支持多层嵌套),据完整删除集再清掉悬空边
    let grew = true;
    while (grew) {
      grew = false;
      for (const n of all) {
        if (n.parentId && removed.has(n.parentId) && !removed.has(n.id)) { removed.add(n.id); grew = true; }
      }
    }
    const remaining = all.filter((n) => !removed.has(n.id));
    const remainingEdges = (getEdges() as typeof edges).filter((e) => !removed.has(e.source) && !removed.has(e.target));
    commit({ nodes: remaining, edges: remainingEdges });
    setSelectedActionNode(null);
  }, [commit, getNodes, getEdges]);

  // 复制/粘贴/再制:内部剪贴板存「绝对坐标的顶层 legacy 元素」;粘贴生成新 id、递增偏移并选中新节点。
  const clipboardRef = useRef<LegacyCanvasState['elements']>([]);
  const pasteCountRef = useRef(0);

  const copySelection = useCallback(() => {
    const all = getNodes() as typeof nodes;
    const sel = all.filter((n) => n.selected && n.type !== 'generator');
    if (!sel.length) return;
    clipboardRef.current = sel.map((n) => {
      const abs = absolutePosition(n, all);
      const el = flowToLegacyCanvas({ nodes: [n], edges: [], viewport: getViewport() }).elements[0];
      return { ...el, x: abs.x, y: abs.y, parentId: undefined };
    });
    pasteCountRef.current = 0;
  }, [getNodes, getViewport]);

  const pasteClipboard = useCallback(() => {
    const items = clipboardRef.current;
    if (!items.length) return;
    pasteCountRef.current += 1;
    const off = 24 * pasteCountRef.current;
    let next = getNodes() as typeof nodes;
    const newIds = new Set<string>();
    items.forEach((el, i) => {
      const type = String(el.type ?? 'node');
      const newId = `${type}_${Date.now()}_${i}_${Math.floor(Math.random() * 100000)}`;
      newIds.add(newId);
      next = upsertFlowCanvasNode(next, { ...el, id: newId, x: Number(el.x ?? 0) + off, y: Number(el.y ?? 0) + off } as never) as typeof nodes;
    });
    next = next.map((n) => ({ ...n, selected: newIds.has(n.id) }));
    commit({ nodes: next });
  }, [getNodes, commit]);

  const duplicateSelection = useCallback(() => {
    copySelection();
    pasteClipboard();
  }, [copySelection, pasteClipboard]);

  const onRelationLabelCommit = useCallback((edgeId: string, label: string) => {
    const nextEdges = (getEdges() as typeof edges).map(edge => edge.id === edgeId
      ? { ...edge, label, data: { ...edge.data, label } }
      : edge);
    commit({ edges: nextEdges });
  }, [commit, getEdges]);

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

    api.atelierCanvas.getState(projectId, canvasId).then(data => {
      if (cancelled) return;
      const legacy: LegacyCanvasState = data?.elements?.length
        ? {
            elements: data.elements,
            connections: data.connections || [],
            viewport: data.viewport || { x: 0, y: 0, scale: 1 },
          }
        : (canvasId
            // 已选定具体画布(非默认): 空即空白, 不拿生成结果回填(否则每张新画布都显示旧结果)
            ? { elements: [], connections: [], viewport: { x: 0, y: 0, scale: 1 } }
            : buildFallbackState(props));
      const flow = legacyToFlowCanvas(legacy);
      setNodes(flow.nodes);
      setEdges(makeEditableRelationEdges(flow.edges));
      setInitialViewport(flow.viewport);
      rememberSavedCanvas({ nodes: flow.nodes, edges: makeEditableRelationEdges(flow.edges), viewport: flow.viewport });
      resetHistory({ nodes: flow.nodes, edges: makeEditableRelationEdges(flow.edges) });
    }).catch(() => {
      if (cancelled) return;
      const flow = legacyToFlowCanvas(buildFallbackState(props));
      setNodes(flow.nodes);
      setEdges(makeEditableRelationEdges(flow.edges));
      setInitialViewport(flow.viewport);
      rememberSavedCanvas({ nodes: flow.nodes, edges: makeEditableRelationEdges(flow.edges), viewport: flow.viewport });
      resetHistory({ nodes: flow.nodes, edges: makeEditableRelationEdges(flow.edges) });
      setLoadError(true);
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });

    return () => { cancelled = true; };
  }, [makeEditableRelationEdges, projectId, canvasId, resetHistory]);

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
    api.atelierCanvas.getState(projectId, canvasId).then(data => {
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
  }, [canvasRefreshNonce, projectId, canvasId, setNodes]);

  const onConnect = useCallback((connection: Connection) => {
    const nextEdges = makeEditableRelationEdges(addEdge(connection, getEdges() as typeof edges));
    commit({ edges: nextEdges });
  }, [commit, getEdges, makeEditableRelationEdges]);


  // 对齐吸附核心:给定被拖拽节点 id 与它「新的相对坐标」,在其他节点(绝对坐标)里找对齐线。
  // 相对↔绝对换算在此处理(getHelperLines 只做纯几何);排除自身与自身子节点(拖画板不吸自己的子元素)。
  // 返回吸附后的相对坐标(未命中为 undefined)+ 参考线绝对坐标。
  const computeSnap = useCallback((id: string, relPos: { x: number; y: number }, distance: number): {
    position?: { x: number; y: number }; vertical?: number; horizontal?: number;
  } => {
    const all = getNodes() as typeof nodes;
    const moving = all.find((n) => n.id === id);
    if (!moving) return {};
    const parent = moving.parentId ? all.find((n) => n.id === moving.parentId) : undefined;
    const parentPos = parent ? parent.position : { x: 0, y: 0 };
    const sizeOf = (n: (typeof all)[number]) => ({
      w: Number((n.data as { width?: number })?.width ?? n.width ?? 0),
      h: Number((n.data as { height?: number })?.height ?? n.height ?? 0),
    });
    const mSize = sizeOf(moving);
    const dragged = { x: parentPos.x + relPos.x, y: parentPos.y + relPos.y, width: mSize.w, height: mSize.h };
    const others = all
      .filter((n) => n.id !== id && n.parentId !== id)
      .map((n) => {
        const abs = absolutePosition(n, all);
        const s = sizeOf(n);
        return { x: abs.x, y: abs.y, width: s.w, height: s.h };
      })
      .filter((r) => r.width > 0 && r.height > 0);
    const { snapX, snapY, vertical, horizontal } = getHelperLines(dragged, others, distance);
    const position = (snapX !== undefined || snapY !== undefined)
      ? { x: (snapX ?? dragged.x) - parentPos.x, y: (snapY ?? dragged.y) - parentPos.y }
      : undefined;
    return { position, vertical, horizontal };
  }, [getNodes]);

  // 包一层 onNodesChange:单节点拖拽时做对齐吸附(就地改写位置变更)+ 显示参考线;
  // 多选/缩放不吸附,释放时清参考线。最终落定位置由 noteDragStop 权威吸附并 commit,
  // 此处只负责拖拽中的实时手感与参考线。
  const handleNodesChange = useCallback<typeof onNodesChange>((changes) => {
    // 只认「拖拽手势」的位置变更(dragging 有明确 true/false);缩放 resize 的位置变更无 dragging,借此排除,避免误吸。
    const drag = changes.filter((c) => c.type === 'position' && !!c.position && (c.dragging === true || c.dragging === false));
    if (drag.length === 1) {
      const ch = drag[0];
      if (ch.type === 'position' && ch.position) {
        const distance = SNAP_PX / (getViewport().zoom || 1);
        const snap = computeSnap(ch.id, ch.position, distance);
        // true/false 两帧都吸附(保证落定位置=吸附后,不依赖 onNodesChange 与 onNodeDragStop 的先后);仅拖拽中显参考线。
        if (snap.position) ch.position = snap.position;
        if (ch.dragging) {
          setHelperLines({ vertical: snap.vertical, horizontal: snap.horizontal });
          // 拖入高亮:算被拖节点(吸附后)的绝对中心 → 命中最内层画板(与落定 reparent 同规则)。
          const all = getNodes() as typeof nodes;
          const moving = all.find((n) => n.id === ch.id);
          if (moving && moving.type !== 'frame') {
            const parent = moving.parentId ? all.find((n) => n.id === moving.parentId) : undefined;
            const ppos = parent ? parent.position : { x: 0, y: 0 };
            const mw = Number((moving.data as { width?: number })?.width ?? moving.width ?? 0);
            const mh = Number((moving.data as { height?: number })?.height ?? moving.height ?? 0);
            const cx = ppos.x + ch.position.x + mw / 2;
            const cy = ppos.y + ch.position.y + mh / 2;
            // 画板恒为顶层 → 其 position 即绝对;frameUnderPoint 只看 frame,故直接用原始 position。
            const boxes = all.map((n) => ({ id: n.id, type: String(n.type ?? ''), parentId: n.parentId, position: n.position, width: Number((n.data as { width?: number })?.width ?? n.width ?? 0), height: Number((n.data as { height?: number })?.height ?? n.height ?? 0) }));
            setDropTargetId(frameUnderPoint(cx, cy, boxes, ch.id));
          } else {
            setDropTargetId(null);
          }
        } else {
          setHelperLines((prev) => (prev.vertical === undefined && prev.horizontal === undefined ? prev : {}));
          setDropTargetId(null); // 拖动结束帧:清高亮
        }
      }
    } else {
      setHelperLines((prev) => (prev.vertical === undefined && prev.horizontal === undefined ? prev : {}));
      setDropTargetId(null);
    }
    onNodesChange(changes);
  }, [computeSnap, getViewport, onNodesChange, getNodes]);

  // 拖拽落定:先对被拖拽节点做一次权威吸附(保证持久化位置=吸附后),清参考线;再拖进画板自动归属
  // (绝对→相对父)、拖出自动脱离(相对→绝对),按「父在子前」重排(React Flow 约束),最后整图保存。
  const noteDragStop = useCallback((_e: MouseEvent | TouchEvent, node: Node) => {
    setHelperLines((prev) => (prev.vertical === undefined && prev.horizontal === undefined ? prev : {}));
    setDropTargetId(null); // 落定:清拖入高亮

    // 权威吸附:用落定的相对坐标算一次吸附,写回被拖拽节点,保证「持久化位置 = 吸附后位置」。
    // 仅单节点拖拽时吸附:多选整组拖动时,只吸「被抓的那个」会让它相对整组偏移、破坏组内相对布局,故跳过。
    const distance = SNAP_PX / (getViewport().zoom || 1);
    const selectedCount = (getNodes() as typeof nodes).filter((n) => n.selected).length;
    const snap = (node && selectedCount <= 1) ? computeSnap(node.id, node.position, distance) : {};
    const all = snap.position
      ? (getNodes() as typeof nodes).map((n) => (n.id === node.id ? { ...n, position: snap.position as { x: number; y: number } } : n))
      : (getNodes() as typeof nodes);
    const boxes = all.map((n) => ({
      id: n.id,
      type: String(n.type ?? ''),
      parentId: n.parentId,
      position: n.position,
      width: Number((n.data as { width?: number })?.width ?? n.width ?? 0),
      height: Number((n.data as { height?: number })?.height ?? n.height ?? 0),
    }));
    const change = node ? resolveContainment(node.id, boxes) : null;
    if (change) {
      const updated = all.map((n) => (n.id === node.id
        ? { ...n, parentId: change.parentId ?? undefined, position: change.position }
        : n));
      const ordered = orderByParent(updated) as typeof nodes;
      commit({ nodes: ordered });
      return;
    }
    commit({ nodes: all as typeof nodes });
  }, [commit, getNodes, computeSnap, getViewport]);

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

    commit({ nodes: nextNodes, edges: nextEdges });
    return true;
  }, [commit, edges, getNodes, makeEditableRelationEdges, nodes]);

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
        await api.generation.quickGenerate({ prompt: instruction.trim(), project_id: projectId, canvas_id: canvasId, agent_mode: 'video-gen' });
        let landed = false;
        for (let i = 0; i < 20; i += 1) {
          await new Promise((r) => window.setTimeout(r, 6000));
          const data = await api.atelierCanvas.getState(projectId, canvasId);
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

  // 文字节点失焦提交后:延一拍等 setNodes flush,再把内容改动入历史 + 持久化
  useEffect(() => {
    const handler = () => { window.setTimeout(() => commit({}), 0); };
    window.addEventListener('moyag:canvas-persist', handler);
    return () => window.removeEventListener('moyag:canvas-persist', handler);
  }, [commit]);

  // 画板「适应内容」:FrameNode 标题按钮派事件 → 按子节点包围盒 shrink-wrap(补偿子坐标视觉不动)→ commit。
  // 子 position 相对父、frame(顶层) position 即绝对,故 boxes 直接用原始 position(fitFrameToChildren 据此计算)。
  useEffect(() => {
    const handler = (e: Event) => {
      const frameId = (e as CustomEvent).detail?.frameId;
      if (!frameId) return;
      const all = getNodes() as typeof nodes;
      const boxes = all.map((n) => ({ id: n.id, type: String(n.type ?? ''), parentId: n.parentId, position: n.position, width: Number((n.data as { width?: number })?.width ?? n.width ?? 0), height: Number((n.data as { height?: number })?.height ?? n.height ?? 0) }));
      const fit = fitFrameToChildren(String(frameId), boxes);
      if (!fit) { setCanvasNotice({ kind: 'info', text: '空画板:先往画板里放点东西再适应内容' }); return; }
      const next = all.map((n) => {
        if (n.id === frameId) return { ...n, position: fit.position, width: fit.width, height: fit.height, data: { ...n.data, width: fit.width, height: fit.height } };
        const cu = fit.children.find((c) => c.id === n.id);
        return cu ? { ...n, position: cu.position } : n;
      }) as typeof nodes;
      commit({ nodes: next });
    };
    window.addEventListener('moyag:fit-frame', handler as EventListener);
    return () => window.removeEventListener('moyag:fit-frame', handler as EventListener);
  }, [getNodes, commit]);

  const confirmReedit = () => {
    const id = reeditNodeId;
    const text = reeditText.trim();
    if (!id || !text) return;
    setReeditNodeId(null);
    void reEdit(id, text);
  };

  // 提示自动消失(进行中的不消失,直到被结果替换)
  useEffect(() => {
    if (!canvasNotice || reeditBusy || genBusy) return;
    const t = window.setTimeout(() => setCanvasNotice(null), 6000);
    return () => window.clearTimeout(t);
  }, [canvasNotice, reeditBusy, genBusy]);

  // 图层顺序:置顶/置底/上移/下移。对选中节点(排除生成节点)按「同层稠密秩」重排,只改受影响节点的
  // zIndex,走 commit(可撤销 + 持久化)。多选保序:front/backward 从底到顶施加、back/forward 从顶到底
  // 施加,避免选区内互相抵消;单选(最常见)结果精确。空 Map(边界/无选中)则不 commit,不污染撤销栈。
  const applyLayerOp = useCallback((op: LayerOp) => {
    let cur = getNodes() as typeof nodes;
    let targets = cur.filter((n) => n.selected && n.type !== 'generator');
    if (!targets.length && selectedActionNode) targets = cur.filter((n) => n.id === selectedActionNode.id);
    if (!targets.length) return;
    const byZ = [...targets].sort((a, b) => Number(a.zIndex ?? 0) - Number(b.zIndex ?? 0));
    const seq = (op === 'front' || op === 'backward') ? byZ : [...byZ].reverse();
    let changed = false;
    for (const t of seq) {
      const zmap = reorderLayer(cur, t.id, op);
      if (zmap.size) {
        cur = cur.map((n) => (zmap.has(n.id) ? { ...n, zIndex: zmap.get(n.id)! } : n)) as typeof nodes;
        changed = true;
      }
    }
    if (changed) commit({ nodes: cur });
  }, [getNodes, selectedActionNode, commit]);

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
    if (id === 'to-chat') {
      // 把选中图/视频作为参考塞进右侧对话(以图生图 / 以图生视频),复用父级 onAddToChat。
      if (!url) return;
      const d = (node.data || {}) as { legacy_id?: string; label?: string; type?: string; metadata?: Record<string, unknown> };
      const nodeType = String(d.type || '');
      props.onAddToChat?.({
        id: String(d.legacy_id || node.id),
        label: String(d.label || (nodeType === 'video' ? '画布视频' : '画布图片')),
        image_url: url,
        type: nodeType || 'image',
        metadata: d.metadata || { source: 'canvas-action-bar' },
      });
      return;
    }
    if (id === 'delete') {
      const remaining = getNodes().filter((n) => n.id !== node.id) as typeof nodes;
      setSelectedActionNode(null);
      commit({ nodes: remaining });
      return;
    }
    if (id === 'front' || id === 'back' || id === 'forward' || id === 'backward') {
      applyLayerOp(id);
      return;
    }
    if (id === 'cutout') {
      if (!url) return;
      setImgActionBusy('cutout');
      try {
        await api.canvasImageActions.run({
          project_id: projectId,
          canvas_id: canvasId,
          asset_id: String(node.data?.legacy_id || node.id),
          action: 'cutout',
          image_url: url,
        });
        const data = await api.atelierCanvas.getState(projectId, canvasId);
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
  }, [selectedActionNode, getNodes, setNodes, setSelectedActionNode, commit, projectId, nodes, applyLayerOp, props.onAddToChat]);

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
      const snapNodes = getNodes() as typeof nodes;
      const snapEdges = getEdges() as typeof edges;
      pushHistory({ nodes: snapNodes, edges: snapEdges });
      void saveCanvas({ nodes: snapNodes, edges: snapEdges, viewport: getViewport() });
    }, 300);
  }, [pushHistory, saveCanvas, getNodes, getEdges, getViewport]);
  useEffect(() => () => { if (propSaveTimer.current) window.clearTimeout(propSaveTimer.current); }, []);

  // 把样式 patch 合并进指定节点的 data.metadata;节点已从 metadata 读样式,会即时重渲染。
  const updateNodeMeta = useCallback((nodeId: string, patch: Record<string, unknown>) => {
    setNodes((cur) => cur.map((n) => (n.id === nodeId
      ? { ...n, data: { ...n.data, metadata: { ...((n.data.metadata as Record<string, unknown>) || {}), ...patch } } }
      : n)));
    schedulePropSave();
  }, [setNodes, schedulePropSave]);

  const nextNodePos = () => { const n = getNodes().length; return { x: 80 + (n % 5) * 360, y: 80 + Math.floor(n / 5) * 320 }; };

  // 打开系统文件选择器:同一个隐藏 input,点前按需动态设 accept(图片/视频/两者)。
  const openImport = (accept: string) => {
    const input = toolFileRef.current;
    if (!input) return;
    input.accept = accept;
    input.value = '';
    input.click();
  };

  // 本地导入:按文件 MIME 分流 —— 图片走 /upload/image 落 image 节点、视频走 /upload/video 落 video 节点
  //(video 节点 = AssetNode 里 type==='video' + thumbnail_url → 渲染 <video controls>,可播放且持久)。
  const handleToolImportFile = async (file: File | undefined) => {
    if (!file) return;
    const isVideo = file.type.startsWith('video/');
    setCanvasNotice({ kind: 'info', text: isVideo ? '正在上传视频…' : '正在上传图片…' });
    try {
      const form = new FormData(); form.append('file', file);
      const res = (isVideo ? await api.upload.video(form) : await api.upload.image(form)) as { url?: string };
      const url = res?.url; if (!url) throw new Error('no url');
      const pos = nextNodePos();
      const tag = url.slice(-10);
      const el = isVideo
        ? { id: 'video_' + String(getNodes().length) + '_' + tag, type: 'video', label: file.name, x: pos.x, y: pos.y, width: 320, height: 240, thumbnail_url: url, asset_ref: { type: 'video', url }, metadata: { source: 'toolbar-import' } }
        : { id: 'image_' + String(getNodes().length) + '_' + tag, type: 'image', label: file.name, x: pos.x, y: pos.y, width: 280, height: 280, thumbnail_url: url, asset_ref: { type: 'image', url }, metadata: { source: 'toolbar-import' } };
      const next = upsertFlowCanvasNode(getNodes() as typeof nodes, el as never) as typeof nodes;
      commit({ nodes: next });
      setCanvasNotice({ kind: 'info', text: isVideo ? '视频已加入画布' : '图片已加入画布' });
    } catch { setCanvasNotice({ kind: 'warn', text: '上传失败,请重试' }); }
  };

  // AI 图/视频「撰写浮窗」的生成动作:点浮窗「生成」才调用。复用已验证的 quickGenerate → 轮询 getState diff 管线;
  // 拿到后端新元素后,把结果落到「当前视口中心」(而非屏幕外),沿用后端真实 id/asset_ref(继承下载/抠图/二次编辑/关系线)。
  // saveCanvas 是整张画布的权威覆盖写,故后端临时落下的同一元素不会重复。
  const runGenComposer = useCallback(async (kind: 'image' | 'video', params: GenerateParams) => {
    setGenComposer(null); // 撰写完即关浮窗让位,进度走顶部提示
    const isVideo = kind === 'video';
    const prompt = params.prompt.trim();
    if (!prompt) return;
    setGenBusy(true);
    setCanvasNotice({ kind: 'info', text: isVideo ? '正在生成视频(约 1-2 分钟),完成后自动加入画布…' : '正在生成图片…' });
    const before = new Set(getNodes().map((n) => String((n.data as { legacy_id?: string })?.legacy_id || n.id)));
    // 落点 = 当前视口中心(结果出现在用户正看的地方,而非按节点数排到屏幕外)
    const stageEl = document.querySelector('[data-flow-canvas-stage]') as HTMLElement | null;
    const rect = stageEl?.getBoundingClientRect();
    const center = rect
      ? screenToFlowPosition({ x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 })
      : { x: 200, y: 200 };
    const px = center.x - params.width / 2;
    const py = center.y - params.height / 2;
    try {
      await api.generation.quickGenerate({
        prompt,
        project_id: projectId,
        canvas_id: canvasId,
        agent_mode: isVideo ? 'video-gen' : 'image-gen',
        auto_model: true,
        brief: params.brief,
        ...(params.reference_image_url ? { reference_image_url: params.reference_image_url } : {}),
      });
      const rounds = isVideo ? 25 : 16;
      for (let i = 0; i < rounds; i += 1) {
        await new Promise((r) => window.setTimeout(r, isVideo ? 6000 : 3000));
        const data = await api.atelierCanvas.getState(projectId, canvasId);
        const fresh = (data?.elements || []).filter((el: { id: string }) => !before.has(String(el.id)));
        if (!fresh.length) continue;
        const [first, ...rest] = fresh;
        const positioned = { ...first, x: px, y: py, width: params.width, height: params.height };
        let next = upsertFlowCanvasNode(getNodes() as typeof nodes, positioned as never) as typeof nodes;
        rest.forEach((extra: { id: string }, idx: number) => {
          next = upsertFlowCanvasNode(next, { ...extra, x: px + (params.width + 40) * (idx + 1), y: py } as never) as typeof nodes;
        });
        commit({ nodes: next });
        setCanvasNotice({ kind: 'info', text: isVideo ? '新视频已生成并加入画布' : '已生成图片并加入画布' });
        return;
      }
      setCanvasNotice({ kind: 'warn', text: isVideo ? '视频仍在渲染,稍后会自动出现;也可手动刷新查看' : '生成超时,图像服务可能繁忙,请稍后重试' });
    } catch {
      setCanvasNotice({ kind: 'warn', text: isVideo ? '视频生成失败,请稍后重试' : '生成失败,请稍后重试' });
    } finally {
      setGenBusy(false);
    }
  }, [getNodes, projectId, commit, screenToFlowPosition]);

  // 点工具栏 AI图/AI视频 → 打开撰写浮窗(不再往画布丢常驻生成节点);关闭即零落地。
  const openGenComposer = useCallback((kind: 'image' | 'video') => {
    setPendingTool(null);
    setGenComposer({ kind });
  }, []);

  // AI 字体生成器:撰写浮窗点「生成」→ 调后端(同步执行~16s,响应不含图 URL)→ 查 history 按 task_id 取图 →
  // 落当前视口中心(sourced /uploads/generated/*.png,可持久)。尺寸固定 1024²(gpt-image-2 最小像素预算要求)。
  const runFontGen = useCallback(async (params: FontParams) => {
    setFontComposer(false);
    const text = params.text.trim();
    if (!text) return;
    setGenBusy(true);
    setCanvasNotice({ kind: 'info', text: '正在生成字体(约 15 秒)…' });
    const stageEl = document.querySelector('[data-flow-canvas-stage]') as HTMLElement | null;
    const rect = stageEl?.getBoundingClientRect();
    const center = rect
      ? screenToFlowPosition({ x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 })
      : { x: 200, y: 200 };
    const size = 340;
    try {
      const res = await api.font.generate({ text, style_name: params.style_name, width: 1024, height: 1024 }) as { task_id?: string; status?: string };
      const taskId = res?.task_id;
      // POST 已阻塞到完成,一般查一次 history 即得;仍留小轮询兜底(万一后端改真异步)。
      let item: { image_url?: string; status?: string; error_message?: string } | undefined;
      for (let i = 0; i < 6; i += 1) {
        const hist = await api.font.history({ page: 1, page_size: 20 }) as { items?: Array<{ task_id?: string; image_url?: string; status?: string; error_message?: string }> };
        item = (hist?.items || []).find((it) => it.task_id === taskId);
        if (item && (item.status === 'completed' || item.status === 'failed')) break;
        await new Promise((r) => window.setTimeout(r, 1500));
      }
      if (item?.status === 'completed' && item.image_url) {
        const id = `font_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
        const el = { id, type: 'image', label: `字体·${text.slice(0, 8)}`, x: center.x - size / 2, y: center.y - size / 2, width: size, height: size, thumbnail_url: item.image_url, asset_ref: { type: 'image', url: item.image_url }, metadata: { source: 'font-gen', font_text: text, font_style: params.style_name } };
        const next = upsertFlowCanvasNode(getNodes() as typeof nodes, el as never) as typeof nodes;
        commit({ nodes: next });
        setCanvasNotice({ kind: 'info', text: '字体已生成并加入画布' });
      } else {
        const err = String(item?.error_message || '');
        const quota = /quota|额度/.test(err);
        setCanvasNotice({ kind: 'warn', text: quota ? '字体生成失败:图片额度不足,请充值后重试' : '字体生成失败,请稍后重试' });
      }
    } catch {
      setCanvasNotice({ kind: 'warn', text: '字体生成失败,请稍后重试' });
    } finally {
      setGenBusy(false);
    }
  }, [getNodes, commit, screenToFlowPosition]);

  // 尺寸预设:在当前视口中心落一个预设尺寸的画板(走 commit,持久 + 可撤销);不经拖拽层。
  const dropPresetFrame = useCallback((action: string) => {
    const preset = FRAME_PRESETS[action];
    if (!preset) return;
    const stageEl = document.querySelector('[data-flow-canvas-stage]') as HTMLElement | null;
    const rect = stageEl?.getBoundingClientRect();
    const center = rect
      ? screenToFlowPosition({ x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 })
      : { x: 200, y: 200 };
    const id = `frame_${Date.now()}_${Math.floor(Math.random() * 10000)}`;
    const el = { id, type: 'frame', label: preset.label, x: center.x - preset.w / 2, y: center.y - preset.h / 2, width: preset.w, height: preset.h };
    const next = upsertFlowCanvasNode(getNodes() as typeof nodes, el as never) as typeof nodes;
    commit({ nodes: next });
    // 新画板常比视口大,缩放到它以便看全(小尺寸不放大过头 maxZoom:1)。
    window.setTimeout(() => fitView({ nodes: [{ id }], padding: 0.2, duration: 240, maxZoom: 1 }), 30);
  }, [getNodes, commit, screenToFlowPosition, fitView]);

  // 工具栏动作分发(action id 由 CanvasToolbar 的下拉/按钮给出)
  const handleTool = (action: string) => {
    if (action === 'select') { setPendingTool(null); setToolMode('select'); return; }
    if (action === 'move') { setPendingTool(null); setToolMode('move'); return; }
    if (action === 'import') { setPendingTool(null); openImport('image/*,video/*'); return; }
    if (action === 'upload-image') { setPendingTool(null); openImport('image/*'); return; }
    if (action === 'upload-video') { setPendingTool(null); openImport('video/*'); return; }
    if (action === 'ai-image') { openGenComposer('image'); return; }
    if (action === 'ai-video') { openGenComposer('video'); return; }
    if (action === 'ai-text') { setPendingTool(null); setFontComposer(true); return; }
    // 画笔:进入持续绘制模式(覆盖层),双击/换工具退出;模式与颜色/笔宽由属性面板呈现
    if (action === 'pen') { setPendingTool('pen'); return; }
    // 标记:点状批注,点击放置;文字/画板/图形:拖拽创建(覆盖层有自带提示,不再弹 toast)
    if (action === 'mark') {
      setPendingTool('mark');
      setCanvasNotice({ kind: 'info', text: '在画布上点击放置标记' });
      return;
    }
    if (FRAME_PRESETS[action]) { setPendingTool(null); dropPresetFrame(action); return; }
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
    const next = upsertFlowCanvasNode(getNodes() as typeof nodes, el as never) as typeof nodes;
    commit({ nodes: next });
    // 连续放置:保持标记工具可继续点放;按 Esc 或 V 退出
  }, [pendingTool, screenToFlowPosition, getNodes, commit]);

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
        ? { id, type: 'text', label: '', x, y, width: Math.max(48, dw), height: Math.max(28, dh), metadata: { fontSize: 18 } }
        : { id, type: 'text', label: '', x: start.x, y: start.y, width: 120, height: 40, metadata: { fontSize: 18 } };
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
    let next = upsertFlowCanvasNode(getNodes() as typeof nodes, el as never) as typeof nodes;
    if (tool === 'text') next = next.map((n) => ({ ...n, selected: n.id === id })) as typeof nodes;
    commit({ nodes: next });
    if (tool === 'text') {
      // 文字:创建后退出放置 + 选中 + 自动聚焦空框,直接输入(仿 Lovart);图形/画板仍连续放置
      setPendingTool(null);
      window.setTimeout(() => focusContentEditable(id), 30);
    }
  }, [pendingTool, getNodes, commit]);

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
    const next = upsertFlowCanvasNode(getNodes() as typeof nodes, el as never) as typeof nodes;
    commit({ nodes: next });
  }, [getNodes, commit]);

  // 适应视图 / 缩放到选区:有选中则缩放到选区,否则适应全部。命令式 fitView(不写 fitView 的 prop 字面量,
  // 以契合结构契约测试)。maxZoom 限制避免单个小节点被放到过大。
  const handleFit = useCallback(() => {
    const sel = (getNodes() as typeof nodes).filter((n) => n.selected);
    if (sel.length) fitView({ nodes: sel.map((n) => ({ id: n.id })), padding: 0.25, duration: 220, maxZoom: 1.5 });
    else fitView({ padding: 0.2, duration: 220 });
  }, [fitView, getNodes]);

  // L0:画布级键盘快捷键 — Undo/Redo、V/H 切选择/移动、Delete 删除选中、Esc 退出放置。
  // L1:Shift+1 适应全部 / Shift+2 缩放到选区(用 e.code 判数字键,避开 Shift 改字符的问题)。
  // 在 input/textarea/contentEditable 编辑时只放行 Undo/Redo,其余画布键不拦截(避免打字误删节点)。
  useEffect(() => {
    const isEditing = (t: EventTarget | null) => {
      const el = t as HTMLElement | null;
      return !!el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable);
    };
    const onKey = (e: KeyboardEvent) => {
      const meta = e.metaKey || e.ctrlKey;
      if (meta && (e.key === 'z' || e.key === 'Z')) { e.preventDefault(); if (e.shiftKey) handleRedo(); else handleUndo(); return; }
      if (meta && (e.key === 'y' || e.key === 'Y')) { e.preventDefault(); handleRedo(); return; }
      if (meta && (e.key === 'c' || e.key === 'C')) { if (isEditing(e.target)) return; e.preventDefault(); copySelection(); return; }
      if (meta && (e.key === 'v' || e.key === 'V')) { if (isEditing(e.target)) return; e.preventDefault(); pasteClipboard(); return; }
      if (meta && (e.key === 'd' || e.key === 'D')) { if (isEditing(e.target)) return; e.preventDefault(); duplicateSelection(); return; }
      // 图层顺序:Ctrl+] 上移 / Ctrl+[ 下移;加 Shift = 置顶 / 置底。用 e.code(物理键)避开 Shift 改字符。
      if (meta && e.code === 'BracketRight') { if (isEditing(e.target)) return; e.preventDefault(); applyLayerOp(e.shiftKey ? 'front' : 'forward'); return; }
      if (meta && e.code === 'BracketLeft') { if (isEditing(e.target)) return; e.preventDefault(); applyLayerOp(e.shiftKey ? 'back' : 'backward'); return; }
      if (e.key === 'Escape') { setPendingTool(null); return; }
      if (meta || isEditing(e.target)) return;
      if (e.shiftKey && e.code === 'Digit1') { e.preventDefault(); fitView({ padding: 0.2, duration: 220 }); return; }
      if (e.shiftKey && e.code === 'Digit2') { e.preventDefault(); const sel = (getNodes() as typeof nodes).filter((n) => n.selected); if (sel.length) fitView({ nodes: sel.map((n) => ({ id: n.id })), padding: 0.25, duration: 220, maxZoom: 1.5 }); return; }
      if (e.key === 'v' || e.key === 'V') { setPendingTool(null); setToolMode('select'); return; }
      if (e.key === 'h' || e.key === 'H') { setPendingTool(null); setToolMode('move'); return; }
      if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); deleteSelected(); return; }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [handleUndo, handleRedo, deleteSelected, copySelection, pasteClipboard, duplicateSelection, fitView, getNodes, applyLayerOp]);

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
  // 用「实时节点 + 绝对坐标」定位:子节点 position 是相对父的,直接用会让操作条错位。
  const selLive = selectedActionNode ? nodes.find((n) => n.id === selectedActionNode.id) ?? selectedActionNode : null;
  const selAbs = selLive ? absolutePosition(selLive, nodes) : null;
  const selectedActionAnchor = (selLive && selLive.type !== 'generator' && selAbs) ? actionBarAnchor({
    x: selAbs.x,
    y: selAbs.y,
    width: Number((selLive.data as { width?: number })?.width || 240),
    height: Number((selLive.data as { height?: number })?.height || 160),
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
        <div data-flow-canvas-stage data-canvas-tool-mode={pendingTool ? 'place' : toolMode} className="relative min-w-0 flex-1 overflow-hidden">
          {/* V/H/放置 的光标:覆盖 React Flow 内置 .react-flow__pane cursor(更高优先级,据 data-canvas-tool-mode) */}
          <style>{`[data-canvas-tool-mode="place"] .react-flow__pane{cursor:crosshair}[data-canvas-tool-mode="select"] .react-flow__pane{cursor:default}[data-canvas-tool-mode="move"] .react-flow__pane{cursor:grab}[data-canvas-tool-mode="move"] .react-flow__pane.dragging{cursor:grabbing}[data-text-placeholder]:focus:empty::before{content:attr(data-text-placeholder);color:#9ca3af;pointer-events:none}`}</style>
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
          <input ref={toolFileRef} type="file" accept="image/*,video/*" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (e.target) e.target.value = ''; void handleToolImportFile(f || undefined); }} />
          <DropTargetContext.Provider value={dropTargetId}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            onNodesChange={handleNodesChange}
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
            deleteKeyCode={null}
            nodesDraggable={toolMode !== 'move'}
            nodesConnectable={true}
            elementsSelectable
            className="bg-[#f5f5f5]"
          >
            <Background gap={32} size={1} color="rgba(0,0,0,0.08)" />
            <HelperLinesOverlay vertical={helperLines.vertical} horizontal={helperLines.horizontal} />
            <Controls position="bottom-right" showInteractive={false} />
            <MiniMap position="bottom-left" pannable zoomable nodeStrokeWidth={2} />
            <Panel position="top-left">
              <div data-canvas-history className="pointer-events-auto flex items-center gap-0.5 rounded-xl border border-black/10 bg-white px-1 py-1 shadow-[0_4px_16px_rgba(0,0,0,0.1)]">
                <button data-canvas-undo type="button" title="撤销 (Ctrl+Z)" disabled={!canUndo} onClick={handleUndo} className="grid size-8 place-items-center rounded-lg text-[#2F3640] transition-colors hover:bg-[#F1F3F5] disabled:cursor-not-allowed disabled:opacity-30">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M9 7L4 12l5 5" /><path d="M4 12h11a5 5 0 0 1 0 10h-1" /></svg>
                </button>
                <button data-canvas-redo type="button" title="重做 (Ctrl+Shift+Z)" disabled={!canRedo} onClick={handleRedo} className="grid size-8 place-items-center rounded-lg text-[#2F3640] transition-colors hover:bg-[#F1F3F5] disabled:cursor-not-allowed disabled:opacity-30">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M15 7l5 5-5 5" /><path d="M20 12H9a5 5 0 0 0 0 10h1" /></svg>
                </button>
                <span className="mx-0.5 h-5 w-px bg-black/10" />
                <button data-canvas-fit type="button" title="适应视图 (Shift+1) / 缩放到选区 (Shift+2)" onClick={handleFit} className="grid size-8 place-items-center rounded-lg text-[#2F3640] transition-colors hover:bg-[#F1F3F5]">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 9V5a1 1 0 0 1 1-1h4" /><path d="M20 9V5a1 1 0 0 0-1-1h-4" /><path d="M4 15v4a1 1 0 0 0 1 1h4" /><path d="M20 15v4a1 1 0 0 1-1 1h-4" /></svg>
                </button>
              </div>
            </Panel>
          </ReactFlow>
          </DropTargetContext.Provider>
          {/* 可自由拖动的底栏:渲染在 stage 覆盖层,不再用 React Flow Panel 固定居中(位置存 localStorage) */}
          <CanvasToolbarDock onTool={handleTool} />
          {/* AI 图/视频撰写浮窗:点「生成」才生成并落到视口中心,关闭即零落地 */}
          {genComposer && (
            <GeneratorComposer
              kind={genComposer.kind}
              onGenerate={(params) => { void runGenComposer(genComposer.kind, params); }}
              onClose={() => setGenComposer(null)}
            />
          )}
          {/* AI 字体生成器撰写浮窗:点「生成」才调后端并落视口中心,关闭零落地 */}
          {fontComposer && (
            <FontComposer
              onGenerate={(params) => { void runFontGen(params); }}
              onClose={() => setFontComposer(false)}
            />
          )}
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
