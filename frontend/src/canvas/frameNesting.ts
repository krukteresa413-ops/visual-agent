// 画板容器(frame)的父子嵌套纯逻辑:拓扑排序 + 拖入归属/拖出脱离判定 + 绝对坐标。
// 抽成纯函数以便单测;CanvasFlow 只负责把 React Flow 节点适配成这里的轻量形状再编排。
//
// 约束(v1):画板恒为顶层(resolveContainment 不把 frame 归属到别处),故嵌套只有 1 层,
// 子的绝对坐标 = 父绝对坐标 + 子相对坐标。

export interface NestBox {
  id: string;
  type?: string;
  parentId?: string;
  position: { x: number; y: number };
  width: number;
  height: number;
}

// 父在子前的稳定排序(React Flow 要求父节点在数组中排在子节点之前,否则报 "parent not found")。
// 任意嵌套深度都正确;父缺失按根处理;有环用 visiting 集兜底防死循环。
export function orderByParent<T extends { id: string; parentId?: string }>(items: T[]): T[] {
  // 按数组下标追踪(而非 id):保留重复 id 的多个元素;父解析取首个同 id 的下标。
  const firstIndexById = new Map<string, number>();
  items.forEach((it, i) => { if (!firstIndexById.has(it.id)) firstIndexById.set(it.id, i); });
  const emitted = items.map(() => false);
  const visiting = items.map(() => false);
  const out: T[] = [];
  const visit = (i: number) => {
    if (emitted[i] || visiting[i]) return;
    visiting[i] = true;
    const parentId = items[i].parentId;
    const parentIndex = parentId !== undefined ? firstIndexById.get(parentId) : undefined;
    if (parentIndex !== undefined && parentIndex !== i) visit(parentIndex);
    visiting[i] = false;
    if (!emitted[i]) {
      emitted[i] = true;
      out.push(items[i]);
    }
  };
  items.forEach((_, i) => visit(i));
  return out;
}

// 节点的绝对坐标(1 层:父恒为顶层,故父坐标即绝对)。
export function absolutePosition(
  node: { parentId?: string; position: { x: number; y: number } },
  nodes: Array<{ id: string; position: { x: number; y: number } }>,
): { x: number; y: number } {
  if (!node.parentId) return node.position;
  const parent = nodes.find((n) => n.id === node.parentId);
  return parent ? { x: parent.position.x + node.position.x, y: parent.position.y + node.position.y } : node.position;
}

// 给定绝对点 (cx,cy),返回中心落入的「最内层」(面积最小)画板 id;无则 null。excludeId 排除自身(拖画板时)。
// 供 resolveContainment(落定 reparent) 与「拖动中高亮」共用同一套命中规则,保证"高亮的框=松手会归属的框"。
export function frameUnderPoint(cx: number, cy: number, boxes: NestBox[], excludeId?: string): string | null {
  let target: NestBox | null = null;
  for (const n of boxes) {
    if (n.type !== 'frame' || n.id === excludeId) continue;
    if (cx >= n.position.x && cx <= n.position.x + n.width && cy >= n.position.y && cy <= n.position.y + n.height) {
      if (!target || n.width * n.height < target.width * target.height) target = n;
    }
  }
  return target ? target.id : null;
}

// 给定被拖拽节点,算它落定后该归属哪个画板(或脱离)。返回 null 表示无需变化。
// 返回 { parentId: string|null, position }:归属时 position 为相对父坐标;脱离时为绝对坐标。
export function resolveContainment(
  draggedId: string,
  nodes: NestBox[],
): { parentId: string | null; position: { x: number; y: number } } | null {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const dragged = byId.get(draggedId);
  if (!dragged || dragged.type === 'frame') return null; // 画板本身不被归属

  const draggedParent = dragged.parentId ? byId.get(dragged.parentId) : undefined;
  const abs = draggedParent
    ? { x: draggedParent.position.x + dragged.position.x, y: draggedParent.position.y + dragged.position.y }
    : dragged.position;
  const cx = abs.x + dragged.width / 2;
  const cy = abs.y + dragged.height / 2;

  const nextId = frameUnderPoint(cx, cy, nodes, draggedId); // 命中最内层画板(与拖动高亮同规则)
  const current = dragged.parentId || null;
  if (nextId === current) return null; // 无变化

  if (nextId) {
    const target = byId.get(nextId)!;
    return { parentId: nextId, position: { x: abs.x - target.position.x, y: abs.y - target.position.y } };
  }
  return { parentId: null, position: abs }; // 脱离 → 绝对坐标
}

// 一键「适应内容」:按子节点包围盒 shrink-wrap 画板(四周留 padding),并补偿子节点相对坐标使其视觉不动。
// 画板恒为顶层(position 即绝对);子 position 相对父。无子节点返回 null(不改)。
// 返回:画板新的绝对 position + 尺寸,以及每个子节点的新相对 position。
export function fitFrameToChildren(
  frameId: string,
  boxes: NestBox[],
  padding = 24,
): { position: { x: number; y: number }; width: number; height: number; children: Array<{ id: string; position: { x: number; y: number } }> } | null {
  const frame = boxes.find((b) => b.id === frameId);
  if (!frame) return null;
  const children = boxes.filter((b) => b.parentId === frameId);
  if (!children.length) return null;

  // 子坐标相对父,直接在相对系里求包围盒。
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const c of children) {
    minX = Math.min(minX, c.position.x);
    minY = Math.min(minY, c.position.y);
    maxX = Math.max(maxX, c.position.x + c.width);
    maxY = Math.max(maxY, c.position.y + c.height);
  }

  // 新画板绝对左上 = 父绝对 + (包围盒左上) - padding。
  const newX = frame.position.x + minX - padding;
  const newY = frame.position.y + minY - padding;
  const width = (maxX - minX) + padding * 2;
  const height = (maxY - minY) + padding * 2;

  // 子新相对 = 子绝对 - 新父绝对 = 旧相对 + (父绝对 - 新父绝对);保证视觉位置不变。
  const dx = frame.position.x - newX;
  const dy = frame.position.y - newY;
  const updatedChildren = children.map((c) => ({ id: c.id, position: { x: c.position.x + dx, y: c.position.y + dy } }));

  return { position: { x: newX, y: newY }, width, height, children: updatedChildren };
}
