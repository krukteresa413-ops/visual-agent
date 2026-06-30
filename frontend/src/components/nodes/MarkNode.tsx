import { memo, useEffect, useRef } from 'react';
import { useReactFlow, type NodeProps } from '@xyflow/react';
import type { FlowCanvasNodeData } from '../../canvas/canvasTypes';

// 标记/图钉节点:画布上落一个可写批注的图钉。双击批注文字编辑,失焦提交到 data.label。

function MarkNode({ id, data, selected }: NodeProps) {
  const node = data as FlowCanvasNodeData;
  const { setNodes } = useReactFlow();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) ref.current.innerText = String(node.label || '批注');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const commit = () => {
    const text = ref.current?.innerText ?? '';
    setNodes((ns) => ns.map((n) => (n.id === id ? { ...n, data: { ...n.data, label: text } } : n)));
  };

  return (
    <div className="flex items-center gap-1.5">
      <span className={`grid size-7 shrink-0 place-items-center rounded-full text-white shadow-md ${selected ? 'ring-2 ring-orange-300' : ''}`} style={{ background: '#f97316' }}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 21s6.5-5.2 6.5-10.5a6.5 6.5 0 1 0-13 0C5.5 15.8 12 21 12 21z" /><circle cx="12" cy="10.5" r="2.2" />
        </svg>
      </span>
      <div
        ref={ref}
        contentEditable
        suppressContentEditableWarning
        spellCheck={false}
        onBlur={commit}
        onMouseDown={(e) => { if (document.activeElement === ref.current) e.stopPropagation(); }}
        className="nodrag max-w-[200px] whitespace-pre-wrap break-words rounded-md border border-gray-200 bg-white px-2 py-1 text-[12px] text-gray-800 shadow-sm outline-none focus:border-orange-300"
        style={{ cursor: 'text' }}
      />
    </div>
  );
}

export default memo(MarkNode);
