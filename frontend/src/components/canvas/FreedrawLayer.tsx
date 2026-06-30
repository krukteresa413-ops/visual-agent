import { useRef, useState, type PointerEvent as ReactPointerEvent } from 'react';
import { useReactFlow } from '@xyflow/react';
import { getStroke, getSvgPathFromStroke, strokeOptions } from '../../canvas/freehand';

// 画笔覆盖层:pendingTool==='pen' 时盖在画布上,捕获指针绘制。
// 实时预览用屏幕坐标(跟手),落定时把采样点转 flow 坐标交给 onComplete 建 FreedrawNode。
// 笔宽(size)以 flow 单位为准,由属性面板控制,预览按当前 zoom 放大,保证所见即所得。

type Props = {
  color: string;
  size: number;
  onComplete: (flowPts: Array<{ x: number; y: number }>, color: string, size: number) => void;
  onExit: () => void;
};

export default function FreedrawLayer({ color, size, onComplete, onExit }: Props) {
  const { screenToFlowPosition, getZoom } = useReactFlow();
  const ref = useRef<HTMLDivElement>(null);
  const drawing = useRef(false);
  const screenPts = useRef<number[][]>([]);
  const flowPts = useRef<Array<{ x: number; y: number }>>([]);
  const zoomRef = useRef(1);
  const [preview, setPreview] = useState('');

  const addPoint = (e: ReactPointerEvent) => {
    const rect = ref.current?.getBoundingClientRect();
    if (!rect) return;
    screenPts.current.push([e.clientX - rect.left, e.clientY - rect.top, e.pressure || 0.5]);
    flowPts.current.push(screenToFlowPosition({ x: e.clientX, y: e.clientY }));
    setPreview(getSvgPathFromStroke(getStroke(screenPts.current, strokeOptions(size * zoomRef.current))));
  };

  const down = (e: ReactPointerEvent) => {
    drawing.current = true;
    zoomRef.current = getZoom();
    screenPts.current = [];
    flowPts.current = [];
    try { (e.target as HTMLElement).setPointerCapture(e.pointerId); } catch { /* noop */ }
    addPoint(e);
  };
  const move = (e: ReactPointerEvent) => { if (drawing.current) addPoint(e); };
  const up = () => {
    if (!drawing.current) return;
    drawing.current = false;
    if (flowPts.current.length > 1) onComplete(flowPts.current, color, size);
    setPreview('');
    screenPts.current = [];
    flowPts.current = [];
  };

  return (
    <div
      ref={ref}
      className="absolute inset-0 z-30"
      style={{ cursor: 'crosshair', touchAction: 'none' }}
      onPointerDown={down}
      onPointerMove={move}
      onPointerUp={up}
      onPointerLeave={up}
      onDoubleClick={onExit}
    >
      {preview && (
        <svg className="pointer-events-none absolute inset-0 h-full w-full">
          <path d={preview} fill={color} />
        </svg>
      )}
    </div>
  );
}
