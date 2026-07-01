import type { CSSProperties } from 'react';
import { useStore } from '@xyflow/react';

// 对齐吸附的参考线覆盖层:把「绝对流坐标」的参考线经视口变换画到屏幕上。
// 覆盖在画布之上,pointer-events:none 不挡交互。参考线坐标随缩放/平移实时跟随
// (用 useStore 订阅 transform;逐个取 primitive 值避免每次返回新对象触发重渲染循环)。

interface Props {
  vertical?: number;   // 竖直参考线的绝对流坐标 X
  horizontal?: number; // 水平参考线的绝对流坐标 Y
}

const OVERLAY_STYLE: CSSProperties = {
  position: 'absolute',
  top: 0,
  left: 0,
  pointerEvents: 'none',
  zIndex: 6,
};

export default function HelperLinesOverlay({ vertical, horizontal }: Props) {
  const tx = useStore((s) => s.transform[0]);
  const ty = useStore((s) => s.transform[1]);
  const zoom = useStore((s) => s.transform[2]);
  const width = useStore((s) => s.width);
  const height = useStore((s) => s.height);

  if (vertical === undefined && horizontal === undefined) return null;

  // 绝对流坐标 → 屏幕:screen = abs * zoom + translate
  const vx = vertical !== undefined ? vertical * zoom + tx : null;
  const hy = horizontal !== undefined ? horizontal * zoom + ty : null;

  return (
    <svg data-canvas-helper-lines width={width} height={height} style={OVERLAY_STYLE}>
      {vx !== null && (
        <line x1={vx} y1={0} x2={vx} y2={height} stroke="#ec4899" strokeWidth={1} shapeRendering="crispEdges" />
      )}
      {hy !== null && (
        <line x1={0} y1={hy} x2={width} y2={hy} stroke="#ec4899" strokeWidth={1} shapeRendering="crispEdges" />
      )}
    </svg>
  );
}
