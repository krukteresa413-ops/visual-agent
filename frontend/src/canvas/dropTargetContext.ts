import { createContext, useContext } from 'react';

// 拖入高亮:当前被拖节点会归属到的「目标画板 id」(拖动中实时,由 CanvasFlow 计算并 Provider 下发)。
// 放在独立文件而非 CanvasFlow,避免 FrameNode ← CanvasFlow 循环依赖;经 React Context 跨 ReactFlow 边界
// 传给 FrameNode(同一 React 树)。非拖动/未命中为 null。
export const DropTargetContext = createContext<string | null>(null);

export function useIsDropTarget(frameId: string): boolean {
  return useContext(DropTargetContext) === frameId;
}
