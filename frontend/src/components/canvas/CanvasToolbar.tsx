import { useEffect, useRef, useState, type FC, type ReactNode } from 'react';

// 画布底栏工具栏 —— 1:1 对齐 Lovart(实地探查):
// [选择 · 标记 · 上传 · 画板 · 图形 · 画笔 · 文字] | [AI图 · AI视频 · AI文字]
// 选择/上传/图形 有上弹下拉; 激活态=深色实心圆角方块; AI 组带角标 ✦。
// onTool 收到具体动作 id(select/move/upload-image/...);父组件据此执行。

type IconProps = { className?: string };
function svg(children: ReactNode): FC<IconProps> {
  return function Icon({ className }: IconProps) {
    return (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className={className}>
        {children}
      </svg>
    );
  };
}

const IcCursor = svg(<path d="M5 3l5.6 14 2.2-6.1 6-2.1z" />);
const IcHand = svg(<path d="M8 13V6a1.5 1.5 0 0 1 3 0v5m0-1.5a1.5 1.5 0 0 1 3 0V12m0-1a1.5 1.5 0 0 1 3 0v4a5 5 0 0 1-5 5h-1a5 5 0 0 1-4.3-2.5L4.5 16s-.7-1.2.6-1.9 2.4 1 2.4 1z" />);
const IcTarget = svg(<><circle cx="12" cy="12" r="7.5" /><circle cx="12" cy="12" r="2.3" fill="currentColor" stroke="none" /></>);
const IcUpload = svg(<><rect x="3" y="5" width="12.5" height="12.5" rx="2" /><circle cx="7.2" cy="9.2" r="1.2" /><path d="M3 14.5l3-2.4 2.7 1.9" /><path d="M18.5 20.5v-7.4" /><path d="M15.6 16l2.9-2.9 2.9 2.9" /></>);
const IcFrame = svg(<path d="M4 8.5h16M4 15.5h16M8.5 4v16M15.5 4v16" />);
const IcSquare = svg(<rect x="5" y="5" width="14" height="14" rx="3" />);
const IcPen = svg(<><path d="M4 20l4-1L19 8l-3-3L5 16z" /><path d="M14.5 6.5l3 3" /></>);
const IcText = svg(<><path d="M5 6h14" /><path d="M12 6v13" /><path d="M9 19h6" /></>);
const IcImage = svg(<><rect x="3.5" y="4.5" width="15" height="14" rx="2" /><circle cx="8" cy="9" r="1.3" /><path d="M4 15l4-3 4 2.5 2.5-1.8L18.5 15" /></>);
const IcPlayFrame = svg(<><rect x="3.5" y="5" width="15" height="14" rx="2.6" /><path d="M9.6 9.6l4.4 2.4-4.4 2.4z" fill="currentColor" stroke="none" /></>);
const IcTextBox = svg(<><rect x="3.5" y="4.5" width="15" height="15" rx="2.6" /><path d="M6.6 8.6h8.8M11 8.6v6.8" /></>);

const IcRect = svg(<rect x="5" y="6.5" width="14" height="11" rx="1.5" />);
const IcLine = svg(<path d="M5 19L19 5" />);
const IcArrow = svg(<><path d="M6 18L18 6" /><path d="M10.5 6H18v7.5" /></>);
const IcEllipse = svg(<ellipse cx="12" cy="12" rx="8" ry="6" />);
const IcPolygon = svg(<path d="M12 4l7 5.1-2.7 8.4H7.7L5 9.1z" />);
const IcStar = svg(<path d="M12 4.2l2.3 5.2 5.6.5-4.2 3.7 1.3 5.5L12 16.4l-5 2.4 1.3-5.5L4.1 9.9l5.6-.5z" />);

const Sparkle: FC = () => (
  <svg width="9" height="9" viewBox="0 0 24 24" fill="currentColor" className="absolute -right-0.5 -top-0.5 text-orange-500" aria-hidden>
    <path d="M12 2l2.2 6.5L21 11l-6.8 2.5L12 20l-2.2-6.5L3 11l6.8-2.5z" />
  </svg>
);

type MenuItem = { action: string; label: string; key?: string; Icon: FC<IconProps> };
type Tool = { id: string; title: string; Icon: FC<IconProps>; ai?: boolean; menu?: MenuItem[] };

const SELECT_MENU: MenuItem[] = [
  { action: 'select', label: '选择', key: 'V', Icon: IcCursor },
  { action: 'move', label: '移动', key: 'H', Icon: IcHand },
];
const UPLOAD_MENU: MenuItem[] = [
  { action: 'upload-image', label: '上传图片', Icon: IcImage },
  { action: 'upload-video', label: '上传视频', Icon: IcPlayFrame },
];
const SHAPE_MENU: MenuItem[] = [
  { action: 'shape-rect', label: '矩形', key: 'R', Icon: IcRect },
  { action: 'shape-line', label: '线条', key: 'L', Icon: IcLine },
  { action: 'shape-arrow', label: '箭头', Icon: IcArrow },
  { action: 'shape-ellipse', label: '椭圆', key: 'O', Icon: IcEllipse },
  { action: 'shape-polygon', label: '多边形', Icon: IcPolygon },
  { action: 'shape-star', label: '星形', Icon: IcStar },
];

const LEFT: Tool[] = [
  { id: 'select', title: '选择 / 移动', Icon: IcCursor, menu: SELECT_MENU },
  { id: 'mark', title: '标记 / 图钉 (M)', Icon: IcTarget },
  { id: 'upload', title: '上传图片 / 视频', Icon: IcUpload, menu: UPLOAD_MENU },
  { id: 'frame', title: '智能画板 (F)', Icon: IcFrame },
  { id: 'shape', title: '快速图形', Icon: IcSquare, menu: SHAPE_MENU },
  { id: 'pen', title: '画笔 (P)', Icon: IcPen },
  { id: 'text', title: '文字 (T)', Icon: IcText },
];
const AI: Tool[] = [
  { id: 'ai-image', title: 'AI 生成图片', Icon: IcImage, ai: true },
  { id: 'ai-video', title: 'AI 生成视频 (S)', Icon: IcPlayFrame, ai: true },
  { id: 'ai-text', title: 'AI 字体生成器', Icon: IcTextBox, ai: true },
];

interface Props { onTool: (action: string) => void; }

export default function CanvasToolbar({ onTool }: Props) {
  const [open, setOpen] = useState<string | null>(null);
  const [active, setActive] = useState<string>('select');
  const rootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(null);
    };
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, [open]);

  const pick = (toolId: string, action: string) => {
    setActive(toolId);
    setOpen(null);
    onTool(action);
  };

  const clickTool = (t: Tool) => {
    if (t.menu) { setOpen((cur) => (cur === t.id ? null : t.id)); return; }
    pick(t.id, t.id);
  };

  const renderTool = (t: Tool) => (
    <div key={t.id} className="relative">
      {t.menu && open === t.id && (
        <div
          className={`absolute bottom-full left-1/2 mb-2 -translate-x-1/2 rounded-xl border border-black/10 bg-white p-1.5 shadow-[0_8px_24px_rgba(0,0,0,0.14)] ${t.id === 'shape' ? 'grid w-[224px] grid-cols-2 gap-0.5' : 'min-w-[176px]'}`}
        >
          {t.menu.map((it) => (
            <button
              key={it.action}
              type="button"
              onMouseDown={(e) => e.stopPropagation()}
              onClick={() => pick(t.id, it.action)}
              className="flex w-full items-center gap-2.5 whitespace-nowrap rounded-lg px-2.5 py-2 text-left text-[13px] text-gray-800 transition-colors hover:bg-gray-100"
            >
              <it.Icon className="shrink-0 text-gray-500" />
              <span>{it.label}</span>
              {it.key && <span className="ml-auto text-[11px] text-gray-400">{it.key}</span>}
            </button>
          ))}
        </div>
      )}
      <button
        type="button"
        title={t.title}
        data-canvas-tool={t.id}
        onClick={() => clickTool(t)}
        className={`relative grid size-10 place-items-center rounded-[10px] transition-colors ${
          active === t.id ? 'bg-gray-900 text-white' : 'text-[#2F3640] hover:bg-[#F1F3F5]'
        }`}
      >
        <t.Icon />
        {t.ai && <Sparkle />}
      </button>
    </div>
  );

  return (
    <div
      ref={rootRef}
      data-canvas-bottom-toolbar
      className="pointer-events-auto flex items-center gap-1 rounded-2xl border border-black/10 bg-white px-2 py-1.5 shadow-[0_8px_24px_rgba(0,0,0,0.12)]"
    >
      {LEFT.map(renderTool)}
      <span className="mx-1.5 h-6 w-px bg-black/10" />
      {AI.map(renderTool)}
    </div>
  );
}
