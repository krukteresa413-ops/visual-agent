import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { FlowCanvasNodeData } from '../../canvas/canvasTypes';

function AssetNode({ data, selected }: NodeProps) {
  const node = data as FlowCanvasNodeData;
  const thumbnail = typeof node.thumbnail_url === 'string' ? node.thumbnail_url : undefined;
  const asset_ref = node.asset_ref;
  const metadata = node.metadata;
  const label = String(node.label || node.id || 'Untitled');
  const type = String(node.type || 'asset');

  return (
    <div
      data-flow-asset-node
      data-asset-ref={asset_ref ? 'true' : 'false'}
      data-metadata={metadata ? 'true' : 'false'}
      className={`overflow-hidden rounded-xl border bg-white shadow-sm transition-shadow ${selected ? 'border-orange-400 ring-2 ring-orange-300/50' : 'border-gray-200'}`}
      style={{ width: node.width, minHeight: node.height }}
    >
      <Handle type="target" position={Position.Left} className="!h-2 !w-2 !bg-gray-300" />
      <div className="flex h-8 items-center justify-between border-b border-gray-100 px-3">
        <div className="min-w-0 truncate text-[11px] font-medium text-gray-800">{label}</div>
        <span className="ml-2 shrink-0 rounded bg-gray-100 px-1.5 py-0.5 text-[9px] uppercase tracking-normal text-gray-500">{type}</span>
      </div>
      <div className="flex items-center justify-center bg-gray-50" style={{ minHeight: Math.max(48, node.height - 32) }}>
        {thumbnail ? (
          <img src={thumbnail} alt="" draggable={false} className="h-full w-full object-cover" />
        ) : (
          <div className="px-4 text-center text-xs text-gray-400">{label}</div>
        )}
      </div>
      <Handle type="source" position={Position.Right} className="!h-2 !w-2 !bg-gray-300" />
    </div>
  );
}

export default memo(AssetNode);
