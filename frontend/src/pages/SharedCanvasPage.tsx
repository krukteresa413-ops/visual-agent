/**
 * SharedCanvasPage — 真·分享的免登录只读查看页(路由 /share/:token)。
 *
 * 拉取冻结快照(api.share.get),用与编辑器同一套 legacyToFlowCanvas + 节点组件
 * 渲染成只读 React Flow(禁拖拽/连线/选择,允许平移缩放查看)。不在 RequireAuth 内,
 * 任何持链者可看;只暴露画布视觉快照,不触碰租户其它数据。
 */
import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ReactFlow, ReactFlowProvider, Background, Controls } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { api } from '../api/client';
import { legacyToFlowCanvas } from '../canvas/canvasAdapters';
import type { LegacyCanvasState } from '../canvas/canvasTypes';
import AssetNode from '../components/nodes/AssetNode';
import ShapeNode from '../components/nodes/ShapeNode';
import TextNode from '../components/nodes/TextNode';
import MarkNode from '../components/nodes/MarkNode';
import FreedrawNode from '../components/nodes/FreedrawNode';
import FrameNode from '../components/nodes/FrameNode';

// 与 CanvasFlow 同套节点类型(不含 generator——生成节点不持久化,不会出现在快照里)
const nodeTypes = {
  canvasElement: AssetNode,
  shape: ShapeNode,
  text: TextNode,
  mark: MarkNode,
  freedraw: FreedrawNode,
  frame: FrameNode,
};

export default function SharedCanvasPage() {
  const { token } = useParams<{ token: string }>();
  const { data, isLoading, isError } = useQuery({
    queryKey: ['share', token],
    queryFn: () => api.share.get(token as string),
    enabled: !!token,
    retry: false,
  });

  const flow = useMemo(() => {
    if (!data?.canvas) return null;
    return legacyToFlowCanvas(data.canvas as unknown as LegacyCanvasState);
  }, [data]);

  if (isLoading) {
    return <div className="grid h-screen place-items-center bg-white text-gray-400">加载分享内容…</div>;
  }
  if (isError || !data || !flow) {
    return (
      <div className="grid h-screen place-items-center bg-white">
        <div className="text-center">
          <div className="text-4xl">🔗</div>
          <p className="mt-3 text-sm text-gray-500">链接无效或已失效</p>
        </div>
      </div>
    );
  }

  const empty = flow.nodes.length === 0;
  return (
    <div className="shared-canvas-viewer flex h-screen w-screen flex-col bg-white">
      <div className="flex shrink-0 items-center justify-between border-b border-gray-200 px-4 py-2.5">
        <div className="flex min-w-0 items-center gap-2">
          <img
            src="/logo-wordmark.png"
            alt="MOYAG"
            className="h-5 w-auto"
            onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
          />
          <span className="truncate text-sm font-semibold text-gray-800">{data.title || '画布分享'}</span>
        </div>
        <span className="shrink-0 rounded-full bg-gray-100 px-2.5 py-0.5 text-[11px] text-gray-500">只读快照</span>
      </div>
      <div className="relative flex-1">
        {empty ? (
          <div className="grid h-full place-items-center text-sm text-gray-400">此画布暂无内容</div>
        ) : (
          <ReactFlowProvider>
            <ReactFlow
              nodes={flow.nodes}
              edges={flow.edges}
              nodeTypes={nodeTypes}
              nodesDraggable={false}
              nodesConnectable={false}
              elementsSelectable={false}
              panOnScroll
              zoomOnScroll
              minZoom={0.1}
              fitView
              proOptions={{ hideAttribution: true }}
            >
              <Background />
              <Controls showInteractive={false} />
            </ReactFlow>
          </ReactFlowProvider>
        )}
      </div>
      {/* 只读页隐藏连线锚点与编辑按钮 */}
      <style>{`.shared-canvas-viewer .react-flow__handle{opacity:0 !important;pointer-events:none !important}.shared-canvas-viewer [title="二次编辑"]{display:none !important}`}</style>
    </div>
  );
}
