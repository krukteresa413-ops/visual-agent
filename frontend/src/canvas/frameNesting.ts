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

  // 命中画板:中心落在某 frame 绝对包围盒内;多个重叠取面积最小者(最内层)。
  let target: NestBox | null = null;
  for (const n of nodes) {
    if (n.type !== 'frame' || n.id === draggedId) continue;
    if (cx >= n.position.x && cx <= n.position.x + n.width && cy >= n.position.y && cy <= n.position.y + n.height) {
      if (!target || n.width * n.height < target.width * target.height) target = n;
    }
  }

  const current = dragged.parentId || null;
  const next = target ? target.id : null;
  if (next === current) return null; // 无变化

  if (target) return { parentId: target.id, position: { x: abs.x - target.position.x, y: abs.y - target.position.y } };
  return { parentId: null, position: abs }; // 脱离 → 绝对坐标
}
