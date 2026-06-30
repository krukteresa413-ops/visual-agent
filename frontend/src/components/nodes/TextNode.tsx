import { memo, useEffect, useRef } from 'react';
import { useReactFlow, type NodeProps } from '@xyflow/react';
import type { FlowCanvasNodeData } from '../../canvas/canvasTypes';

// 文字节点:双击编辑(contentEditable,非受控以避免光标跳动),失焦提交到 data.label。
// 排版(字号/颜色/对齐)存 data.metadata,可持久化。

function TextNode({ id, data, selected }: NodeProps) {
  const node = data as FlowCanvasNodeData;
  const meta = (node.metadata || {}) as { fontSize?: number; color?: string; align?: 'left' | 'center' | 'right'; weight?: number; fontFamily?: string };
  const { setNodes } = useReactFlow();
  const ref = useRef<HTMLDivElement>(null);

  // 仅挂载时把初始文字写进 DOM;之后交给浏览器编辑,React 不再接管文本(防止重渲染清空输入)
  useEffect(() => {
    if (ref.current) ref.current.innerText = String(node.label || '');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const commit = () => {
    const text = ref.current?.innerText ?? '';
    setNodes((ns) => ns.map((n) => (n.id === id ? { ...n, data: { ...n.data, label: text } } : n)));
  };

  return (
    <div className={`rounded ${selected ? 'ring-1 ring-orange-300' : ''}`} style={{ minWidth: 48 }}>
      <div
        ref={ref}
        contentEditable
        suppressContentEditableWarning
        spellCheck={false}
        onBlur={commit}
        onMouseDown={(e) => { if (document.activeElement === ref.current) e.stopPropagation(); }}
        className="nodrag whitespace-pre-wrap break-words outline-none"
        style={{
          fontSize: Number(meta.fontSize || 18),
          color: meta.color || '#111827',
          textAlign: meta.align || 'left',
          fontWeight: meta.weight || 400,
          fontFamily: meta.fontFamily || 'Inter, system-ui, sans-serif',
          padding: '2px 4px',
          lineHeight: 1.4,
          cursor: 'text',
        }}
      />
    </div>
  );
}

export default memo(TextNode);
