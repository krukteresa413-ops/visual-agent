import { memo } from 'react';
import type { NodeProps } from '@xyflow/react';
import type { FlowCanvasNodeData } from '../../canvas/canvasTypes';

// 自由绘节点:渲染 perfect-freehand 生成的填充 path(存在 data.metadata.path)。
function FreedrawNode({ data, selected }: NodeProps) {
  const node = data as FlowCanvasNodeData;
  const meta = (node.metadata || {}) as { path?: string; color?: string };
  const w = Number(node.width || 10);
  const h = Number(node.height || 10);
  return (
    <div className={selected ? 'rounded ring-1 ring-orange-300' : ''}>
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{ display: 'block', overflow: 'visible' }}>
        <path d={meta.path || ''} fill={meta.color || '#111827'} />
      </svg>
    </div>
  );
}

export default memo(FreedrawNode);
