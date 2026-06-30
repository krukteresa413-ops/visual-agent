// 通用撤销/重做历史栈(past / present / future 模型)。纯函数,无 React 依赖,便于单测。
// 用法:画布每个「语义操作完成」点把整张快照 record 进来;Ctrl+Z 取 past 顶、Ctrl+Y 取 future 顶。
// 设计要点:
//  - present 恒有值(初始化即给),所以还原时不必判空。
//  - record 会清空 future(产生新分叉),并按 limit 丢弃最旧的快照。
//  - 与当前 present「引用相等」的快照不记录(React Flow 不可变更新下,引用相等≈无变化),避免重复入栈。

export interface History<T> {
  past: T[];
  present: T;
  future: T[];
  limit: number;
}

export function createHistory<T>(initial: T, limit = 50): History<T> {
  return { past: [], present: initial, future: [], limit: Math.max(1, limit) };
}

// 记录新快照:present 进 past、snapshot 成为新 present、清空 future。超过 limit 丢最旧。
export function record<T>(h: History<T>, snapshot: T): History<T> {
  if (snapshot === h.present) return h;
  const past = [...h.past, h.present];
  const overflow = past.length - h.limit;
  return {
    past: overflow > 0 ? past.slice(overflow) : past,
    present: snapshot,
    future: [],
    limit: h.limit,
  };
}

export function canUndo<T>(h: History<T>): boolean {
  return h.past.length > 0;
}

export function canRedo<T>(h: History<T>): boolean {
  return h.future.length > 0;
}

// 撤销:present 进 future、past 顶成为新 present。无历史时原样返回(幂等)。
export function undo<T>(h: History<T>): History<T> {
  if (h.past.length === 0) return h;
  const present = h.past[h.past.length - 1];
  return {
    past: h.past.slice(0, -1),
    present,
    future: [h.present, ...h.future],
    limit: h.limit,
  };
}

// 重做:present 进 past、future 顶成为新 present。无可重做时原样返回(幂等)。
export function redo<T>(h: History<T>): History<T> {
  if (h.future.length === 0) return h;
  const present = h.future[0];
  return {
    past: [...h.past, h.present],
    present,
    future: h.future.slice(1),
    limit: h.limit,
  };
}
