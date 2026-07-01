import { useCallback, useEffect, useRef, useState, type CSSProperties, type PointerEvent as ReactPointerEvent } from 'react';
import CanvasToolbar from './CanvasToolbar';

// 可自由拖动的底栏「坞」:包住 CanvasToolbar,抓工具栏非按钮区域即可拖动整条底栏。
// 位置夹在画布(父容器 = stage)内,存 localStorage 跨会话记忆;默认底部居中。
// 点在按钮/输入上不触发拖动,保证工具栏点击/下拉正常。

const LS_KEY = 'moyag:canvas-toolbar-pos';

function loadPos(): { x: number; y: number } | null {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return null;
    const p = JSON.parse(raw);
    if (typeof p?.x === 'number' && typeof p?.y === 'number') return p;
  } catch { /* ignore */ }
  return null;
}

interface Props { onTool: (action: string) => void; }

export default function CanvasToolbarDock({ onTool }: Props) {
  const [pos, setPos] = useState<{ x: number; y: number } | null>(() => loadPos());
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const grabOffset = useRef<{ dx: number; dy: number } | null>(null); // 指针相对 wrap 左上角的偏移

  // 把 (x,y) 夹进父容器可视范围,避免底栏被拖出画布够不着。
  const clamp = useCallback((x: number, y: number) => {
    const wrap = wrapRef.current;
    const parent = wrap?.parentElement;
    if (!wrap || !parent) return { x, y };
    const maxX = Math.max(0, parent.clientWidth - wrap.offsetWidth);
    const maxY = Math.max(0, parent.clientHeight - wrap.offsetHeight);
    return { x: Math.max(0, Math.min(x, maxX)), y: Math.max(0, Math.min(y, maxY)) };
  }, []);

  const onPointerDown = useCallback((e: ReactPointerEvent<HTMLDivElement>) => {
    // 点在按钮/输入等交互元素上时不拖动,让工具栏正常点击/开下拉。
    if ((e.target as HTMLElement).closest('button, input, textarea, a, select')) return;
    const wrap = wrapRef.current;
    const parent = wrap?.parentElement;
    if (!wrap || !parent) return;
    const wrapRect = wrap.getBoundingClientRect();
    const parentRect = parent.getBoundingClientRect();
    grabOffset.current = { dx: e.clientX - wrapRect.left, dy: e.clientY - wrapRect.top };
    // 仍是默认(居中)时,先把当前位置固化成绝对坐标,后续按 left/top 走。
    if (!pos) setPos(clamp(wrapRect.left - parentRect.left, wrapRect.top - parentRect.top));
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    e.preventDefault();
  }, [pos, clamp]);

  const onPointerMove = useCallback((e: ReactPointerEvent<HTMLDivElement>) => {
    if (!grabOffset.current) return;
    const parent = wrapRef.current?.parentElement;
    if (!parent) return;
    const parentRect = parent.getBoundingClientRect();
    const x = e.clientX - parentRect.left - grabOffset.current.dx;
    const y = e.clientY - parentRect.top - grabOffset.current.dy;
    setPos(clamp(x, y));
  }, [clamp]);

  const endDrag = useCallback((e: ReactPointerEvent<HTMLDivElement>) => {
    if (!grabOffset.current) return;
    grabOffset.current = null;
    try { (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId); } catch { /* ignore */ }
    setPos((p) => { if (p) { try { localStorage.setItem(LS_KEY, JSON.stringify(p)); } catch { /* ignore */ } } return p; });
  }, []);

  // 窗口尺寸变化后重新夹紧,避免底栏跑到画布外。
  useEffect(() => {
    const onResize = () => setPos((p) => (p ? clamp(p.x, p.y) : p));
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [clamp]);

  const style: CSSProperties = pos
    ? { position: 'absolute', left: pos.x, top: pos.y, zIndex: 5 }
    : { position: 'absolute', left: '50%', bottom: 16, transform: 'translateX(-50%)', zIndex: 5 };

  return (
    <div
      ref={wrapRef}
      data-canvas-toolbar-dock
      style={style}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
      className="cursor-grab touch-none active:cursor-grabbing"
      title="拖动可移动工具栏"
    >
      <CanvasToolbar onTool={onTool} />
    </div>
  );
}
