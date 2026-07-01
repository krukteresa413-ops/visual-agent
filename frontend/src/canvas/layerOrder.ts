// 图层顺序(z-order)的纯逻辑:置顶/置底/上移一层/下移一层。无 React/DOM 依赖,便于单测。
//
// 第一性原理:
//  - React Flow 的绘制层叠只认「顶层 node.zIndex」(未设视为 0),并列时按数组顺序兜底。
//    故「图层顺序」的本质 = 同层节点上的一个「全序」,用整数 zIndex 表达。
//  - 同层作用域 = 同一 parentId:顶层节点共享 undefined 父自成一组;某画板(frame)的子节点
//    自成一组。跨组不比较 z —— 契合 Figma「在所属容器内前后移动」的语义,也避开「子节点 z
//    压过别组」这类怪象。顶层节点是最常见场景,与旧的全局 max/min 行为等价 → 零回归。
//  - 为根治「整数并列 / 空洞导致上移一层没反应」的歧义:每次操作对该组做「稠密秩重排」——
//    按 (zIndex??0, 原数组序) 排出当前『底→顶』序列,移动目标后重新赋 0..k-1 的稠密 z。
//  - 已在边界(置顶时已在顶 / 置底时已在底 / 组内<=1 / 目标缺失)返回空 Map:调用方据此
//    不 commit、不污染撤销栈。

export type LayerOp = 'front' | 'back' | 'forward' | 'backward';

interface LayerNode {
  id: string;
  parentId?: string;
  zIndex?: number;
}

// 返回「需要写入的新 zIndex」映射(该同层组的全部节点 → 稠密秩 0..k-1)。
// 无变化(边界 / 组内<=1 / 目标缺失)返回空 Map。
export function reorderLayer<T extends LayerNode>(nodes: T[], targetId: string, op: LayerOp): Map<string, number> {
  const target = nodes.find((n) => n.id === targetId);
  if (!target) return new Map();

  const targetParent = target.parentId ?? undefined;
  // 同层组(含目标),带原数组下标以稳定兜底并列。
  const group = nodes
    .map((n, i) => ({ id: n.id, z: n.zIndex, i, parentId: n.parentId ?? undefined }))
    .filter((x) => x.parentId === targetParent);
  if (group.length <= 1) return new Map();

  // 当前『底→顶』序列:先按 zIndex 升序,并列再按原数组序。
  const order = [...group].sort((a, b) => (a.z ?? 0) - (b.z ?? 0) || a.i - b.i).map((x) => x.id);
  const pos = order.indexOf(targetId);
  const last = order.length - 1;
  const to =
    op === 'front' ? last :
    op === 'back' ? 0 :
    op === 'forward' ? pos + 1 :
    /* backward */ pos - 1;

  if (to === pos || to < 0 || to > last) return new Map(); // 已在边界:no-op

  order.splice(pos, 1);
  order.splice(to, 0, targetId);

  const result = new Map<string, number>();
  order.forEach((id, rank) => result.set(id, rank));
  return result;
}
