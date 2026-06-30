import { memo } from 'react';
import { Handle, NodeResizer, Position, useReactFlow, type NodeProps } from '@xyflow/react';
import type { FlowCanvasNodeData } from '../../canvas/canvasTypes';

// 快速图形节点:用 SVG 画 矩形/椭圆/三角/菱形/星形/线/箭头,NodeResizer 拖角改大小。
// 形状种类与样式存在 data.metadata.{shape,fill,stroke}(可持久化)。

type ShapeKind = 'rect' | 'ellipse' | 'triangle' | 'diamond' | 'star' | 'line' | 'arrow';

function starPoints(w: number, h: number): string {
  const cx = w / 2;
  const cy = h / 2;
  const outer = Math.min(w, h) / 2 - 1;
  const inner = outer * 0.45;
  const pts: string[] = [];
  for (let i = 0; i < 10; i += 1) {
    const r = i % 2 === 0 ? outer : inner;
    const a = (Math.PI / 5) * i - Math.PI / 2;
    pts.push(`${(cx + r * Math.cos(a)).toFixed(1)},${(cy + r * Math.sin(a)).toFixed(1)}`);
  }
  return pts.join(' ');
}

function ShapeNode({ id, data, selected, width: nodeW, height: nodeH }: NodeProps) {
  const node = data as FlowCanvasNodeData;
  const meta = (node.metadata || {}) as { shape?: ShapeKind; fill?: string; stroke?: string; strokeWidth?: number; endCorner?: string };
  const shape: ShapeKind = meta.shape || 'rect';
  const w = Number(nodeW ?? node.width ?? 160);
  const h = Number(nodeH ?? node.height ?? 120);
  const fill = meta.fill || 'rgba(99,102,241,0.12)';
  const stroke = meta.stroke || '#6366f1';
  const sw = Number.isFinite(Number(meta.strokeWidth)) ? Number(meta.strokeWidth) : 2;
  const { setNodes } = useReactFlow();

  // 线/箭头:两端 = 包围盒一条对角线的两角。endCorner = 箭头(终点)所在角('tr' 默认,兼容旧节点),
  // 起点取其对角。据此让线沿拖拽方向、箭头朝拖拽终点(4 个方向都正确)。
  const endCorner = typeof meta.endCorner === 'string' ? meta.endCorner : 'tr';
  const cornerXY = (c: string) => ({ x: c[1] === 'r' ? w - sw : sw, y: c[0] === 'b' ? h - sw : sw });
  const oppCorner = (c: string) => (c[0] === 'b' ? 't' : 'b') + (c[1] === 'r' ? 'l' : 'r');
  const pA = cornerXY(oppCorner(endCorner)); // 起点
  const pB = cornerXY(endCorner);            // 终点(箭头处)
  const ang = Math.atan2(pB.y - pA.y, pB.x - pA.x);
  const headLen = Math.max(8, Math.min(18, Math.hypot(pB.x - pA.x, pB.y - pA.y) * 0.18));
  const hx1 = pB.x - headLen * Math.cos(ang - 0.45);
  const hy1 = pB.y - headLen * Math.sin(ang - 0.45);
  const hx2 = pB.x - headLen * Math.cos(ang + 0.45);
  const hy2 = pB.y - headLen * Math.sin(ang + 0.45);

  const commitSize = (width: number, height: number) => {
    setNodes((ns) => ns.map((n) => (n.id === id ? { ...n, data: { ...n.data, width, height } } : n)));
  };

  return (
    <>
      <NodeResizer
        isVisible={selected}
        minWidth={24}
        minHeight={24}
        keepAspectRatio={shape === 'star' || shape === 'triangle'}
        lineClassName="!border-orange-300"
        handleClassName="!h-2 !w-2 !rounded-sm !border-orange-400 !bg-white"
        onResize={(_e, p) => commitSize(p.width, p.height)}
      />
      <Handle type="target" position={Position.Left} className="!h-2 !w-2 !bg-gray-300 !opacity-0" />
      <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{ display: 'block', overflow: 'visible' }}>
        {shape === 'rect' && <rect x={sw} y={sw} width={Math.max(0, w - sw * 2)} height={Math.max(0, h - sw * 2)} rx={6} fill={fill} stroke={stroke} strokeWidth={sw} />}
        {shape === 'ellipse' && <ellipse cx={w / 2} cy={h / 2} rx={Math.max(0, w / 2 - sw)} ry={Math.max(0, h / 2 - sw)} fill={fill} stroke={stroke} strokeWidth={sw} />}
        {shape === 'triangle' && <polygon points={`${w / 2},${sw} ${w - sw},${h - sw} ${sw},${h - sw}`} fill={fill} stroke={stroke} strokeWidth={sw} strokeLinejoin="round" />}
        {shape === 'diamond' && <polygon points={`${w / 2},${sw} ${w - sw},${h / 2} ${w / 2},${h - sw} ${sw},${h / 2}`} fill={fill} stroke={stroke} strokeWidth={sw} strokeLinejoin="round" />}
        {shape === 'star' && <polygon points={starPoints(w, h)} fill={fill} stroke={stroke} strokeWidth={sw} strokeLinejoin="round" />}
        {shape === 'line' && <line x1={pA.x} y1={pA.y} x2={pB.x} y2={pB.y} stroke={stroke} strokeWidth={sw + 1} strokeLinecap="round" />}
        {shape === 'arrow' && (
          <g stroke={stroke} strokeWidth={sw + 1} fill="none" strokeLinecap="round" strokeLinejoin="round">
            <line x1={pA.x} y1={pA.y} x2={pB.x} y2={pB.y} />
            <polyline points={`${hx1.toFixed(1)},${hy1.toFixed(1)} ${pB.x},${pB.y} ${hx2.toFixed(1)},${hy2.toFixed(1)}`} />
          </g>
        )}
      </svg>
      <Handle type="source" position={Position.Right} className="!h-2 !w-2 !bg-gray-300 !opacity-0" />
    </>
  );
}

export default memo(ShapeNode);
