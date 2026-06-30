import { useRef, useState, type PointerEvent as ReactPointerEvent } from 'react';
import { useReactFlow } from '@xyflow/react';

// 拖拽创建覆盖层:pendingTool ∈ {text/frame/shape-*} 时盖在画布上(z-30,与画笔层同构)。
// 按住拖拽 = 拖出一个矩形(节点的包围盒),释放时把 起点/终点(flow 坐标)+是否真拖动 交给 onComplete;
// 拖动距离 < 阈值视为"点击",父组件据此落默认尺寸(保留点击=默认尺寸的兜底)。
// 必须有这层:否则在画布上拖动会触发 React Flow 自带的框选,而不是绘制。
// Esc 取消由父组件统一处理(pendingTool 清空 → 本层卸载,未建节点)。

type Pt = { x: number; y: number };

type Props = {
  onComplete: (start: Pt, end: Pt, dragged: boolean) => void;
};

const CLICK_THRESHOLD = 4; // 屏幕像素:小于此视为点击而非拖拽

export default function DragCreateLayer({ onComplete }: Props) {
  const { screenToFlowPosition } = useReactFlow();
  const ref = useRef<HTMLDivElement>(null);
  const drawing = useRef(false);
  const startScreen = useRef<Pt>({ x: 0, y: 0 });
  const startFlow = useRef<Pt>({ x: 0, y: 0 });
  const [box, setBox] = useState<{ left: number; top: number; w: number; h: number } | null>(null);

  const localPt = (e: ReactPointerEvent): Pt => {
    const rect = ref.current?.getBoundingClientRect();
    return { x: e.clientX - (rect?.left || 0), y: e.clientY - (rect?.top || 0) };
  };

  const down = (e: ReactPointerEvent) => {
    drawing.current = true;
    startScreen.current = localPt(e);
    startFlow.current = screenToFlowPosition({ x: e.clientX, y: e.clientY });
    try { (e.target as HTMLElement).setPointerCapture(e.pointerId); } catch { /* noop */ }
    setBox({ left: startScreen.current.x, top: startScreen.current.y, w: 0, h: 0 });
  };

  const move = (e: ReactPointerEvent) => {
    if (!drawing.current) return;
    const cur = localPt(e);
    setBox({
      left: Math.min(startScreen.current.x, cur.x),
      top: Math.min(startScreen.current.y, cur.y),
      w: Math.abs(cur.x - startScreen.current.x),
      h: Math.abs(cur.y - startScreen.current.y),
    });
  };

  const up = (e: ReactPointerEvent) => {
    if (!drawing.current) return;
    drawing.current = false;
    const cur = localPt(e);
    const dist = Math.hypot(cur.x - startScreen.current.x, cur.y - startScreen.current.y);
    const endFlow = screenToFlowPosition({ x: e.clientX, y: e.clientY });
    setBox(null);
    onComplete(startFlow.current, endFlow, dist >= CLICK_THRESHOLD);
  };

  return (
    <div
      ref={ref}
      className="absolute inset-0 z-30"
      style={{ cursor: 'crosshair', touchAction: 'none' }}
      onPointerDown={down}
      onPointerMove={move}
      onPointerUp={up}
    >
      {box && (box.w > 0 || box.h > 0) && (
        <div
          className="pointer-events-none absolute rounded-[2px] border border-dashed border-sky-500 bg-sky-400/10"
          style={{ left: box.left, top: box.top, width: box.w, height: box.h }}
        />
      )}
      <div className="pointer-events-none absolute left-1/2 top-3 -translate-x-1/2 rounded-full bg-gray-900/80 px-3 py-1 text-xs text-white">
        在画布上按住拖拽绘制 · Esc 取消
      </div>
    </div>
  );
}
