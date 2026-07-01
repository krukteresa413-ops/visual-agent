import { memo, useEffect, useRef } from 'react';
import { NodeResizer, useReactFlow, type NodeProps } from '@xyflow/react';
import type { FlowCanvasNodeData } from '../../canvas/canvasTypes';
import { useIsDropTarget } from '../../canvas/dropTargetContext';

// 画板/Frame 节点(v1):带标题的可调大小容器框。
// 框体 pointer-events:none —— 永不挡住上面/里面的内容,点击穿透;
// 仅「标题条」可交互(选中/拖动/改名),拖标题移动整个框。
// 注:真·子元素归属(拖入自动 reparent)是后续增强,这版是视觉分组框。

function FrameNode({ id, data, selected, width: nodeW, height: nodeH }: NodeProps) {
  const node = data as FlowCanvasNodeData;
  const { setNodes } = useReactFlow();
  const isDropTarget = useIsDropTarget(id); // 拖动中:有节点会落进本画板时高亮
  const ref = useRef<HTMLSpanElement>(null);
  const w = Number(nodeW ?? node.width ?? 400);
  const h = Number(nodeH ?? node.height ?? 300);

  useEffect(() => {
    if (ref.current) ref.current.innerText = String(node.label || '画板');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const commit = () => {
    const text = ref.current?.innerText ?? '';
    setNodes((ns) => ns.map((n) => (n.id === id ? { ...n, data: { ...n.data, label: text } } : n)));
  };
  const commitSize = (width: number, height: number) => {
    setNodes((ns) => ns.map((n) => (n.id === id ? { ...n, data: { ...n.data, width, height } } : n)));
  };

  return (
    <>
      <NodeResizer
        isVisible={selected}
        minWidth={120}
        minHeight={90}
        lineClassName="!border-orange-300"
        handleClassName="!h-2 !w-2 !rounded-sm !border-orange-400 !bg-white"
        onResize={(_e, p) => commitSize(p.width, p.height)}
      />
      <div
        style={{ width: w, height: h, pointerEvents: 'none' }}
        className={`rounded-lg border-2 transition-colors ${isDropTarget ? 'border-orange-400 bg-orange-100/40' : selected ? 'border-orange-400' : 'border-gray-300'}`}
      />
      {/* 标题条:可选中/拖动/改名(pointer-events 恢复) */}
      <div className="pointer-events-auto absolute -top-7 left-0 flex items-center gap-1 rounded-md border border-gray-200 bg-white px-2 py-0.5 text-[12px] font-medium text-gray-600 shadow-sm">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
          <path d="M4 8.5h16M4 15.5h16M8.5 4v16M15.5 4v16" />
        </svg>
        <span
          ref={ref}
          contentEditable
          suppressContentEditableWarning
          spellCheck={false}
          onBlur={commit}
          onMouseDown={(e) => { if (document.activeElement === ref.current) e.stopPropagation(); }}
          className="nodrag outline-none"
          style={{ cursor: 'text', minWidth: 24 }}
        />
        {/* 一键「适应内容」:把画板缩到刚好包住里面的元素(派事件给 CanvasFlow 统一 commit) */}
        <button
          type="button"
          title="适应内容"
          onMouseDown={(e) => e.stopPropagation()}
          onClick={(e) => { e.stopPropagation(); window.dispatchEvent(new CustomEvent('moyag:fit-frame', { detail: { frameId: id } })); }}
          className="nodrag ml-0.5 grid size-5 place-items-center rounded text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-700"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 9V5a1 1 0 0 1 1-1h4" /><path d="M20 9V5a1 1 0 0 0-1-1h-4" /><path d="M4 15v4a1 1 0 0 0 1 1h4" /><path d="M20 15v4a1 1 0 0 1-1 1h-4" />
          </svg>
        </button>
      </div>
    </>
  );
}

export default memo(FrameNode);
