import { useCallback, useRef, useState } from 'react';
import { canRedo, canUndo, createHistory, record, redo as doRedo, undo as doUndo, type History } from './history';

// React 封装:历史栈存在 ref(避免闭包陈旧 + 不必要重渲染),用一个 version state 驱动
// canUndo/canRedo 的刷新(让 undo/redo 按钮的禁用态及时更新)。
// reset:画布加载完成后设初始快照。push:语义操作完成时记录。undo/redo:返回要还原的快照(或 null)。
export function useCanvasHistory<T>(limit = 50) {
  const ref = useRef<History<T> | null>(null);
  const [, bump] = useState(0);
  const refresh = useCallback(() => bump((v) => v + 1), []);

  const reset = useCallback((initial: T) => {
    ref.current = createHistory(initial, limit);
    refresh();
  }, [limit, refresh]);

  const push = useCallback((snapshot: T) => {
    ref.current = ref.current ? record(ref.current, snapshot) : createHistory(snapshot, limit);
    refresh();
  }, [limit, refresh]);

  const undo = useCallback((): T | null => {
    const h = ref.current;
    if (!h || !canUndo(h)) return null;
    ref.current = doUndo(h);
    refresh();
    return ref.current.present;
  }, [refresh]);

  const redo = useCallback((): T | null => {
    const h = ref.current;
    if (!h || !canRedo(h)) return null;
    ref.current = doRedo(h);
    refresh();
    return ref.current.present;
  }, [refresh]);

  return {
    reset,
    push,
    undo,
    redo,
    canUndo: ref.current ? canUndo(ref.current) : false,
    canRedo: ref.current ? canRedo(ref.current) : false,
  };
}
