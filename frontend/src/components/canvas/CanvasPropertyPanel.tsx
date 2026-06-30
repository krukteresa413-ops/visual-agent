import { useId, type ReactNode } from 'react';

// 画布属性面板:顶部居中浮条。两类场景,触发方式本质不同:
//  - 工具激活(画笔):设「下一笔」的颜色+笔宽。自由绘把笔宽烤进路径几何,必须画前设。
//  - 选中节点(文字/图形/自由绘):就地改该节点 metadata 里的样式,节点已从 metadata 读样式。
// 取色用原生 <input type=color>(全色域,零依赖)+ 预设色;完整 HSV/不透明度面板留作后续。

export type PropertyPanelKind = 'pen' | 'text' | 'shape' | 'freedraw';

interface Props {
  kind: PropertyPanelKind;
  values: Record<string, unknown>;
  onChange: (patch: Record<string, unknown>) => void;
  onExitPen?: () => void;
}

const PRESETS = ['#111827', '#ffffff', '#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899'];
const FONTS = [
  { v: 'Inter, system-ui, sans-serif', label: 'Inter' },
  { v: 'system-ui, sans-serif', label: '系统' },
  { v: 'Georgia, serif', label: '衬线' },
  { v: 'ui-monospace, monospace', label: '等宽' },
];
const WEIGHTS = [
  { v: 400, label: 'Regular' },
  { v: 500, label: 'Medium' },
  { v: 600, label: 'Semibold' },
  { v: 700, label: 'Bold' },
];

const SELECT_CLS = 'cursor-pointer rounded-md border border-gray-200 bg-white px-2 py-1 text-[12px] text-gray-700 outline-none hover:border-gray-300';

// 把任意 css 颜色(#rgb / #rrggbb / rgb() / rgba())转成原生 <input type=color> 需要的 #rrggbb;失败回退深灰。
function toHex(c: unknown): string {
  if (typeof c !== 'string') return '#111827';
  if (/^#[0-9a-f]{6}$/i.test(c)) return c.toLowerCase();
  if (/^#[0-9a-f]{3}$/i.test(c)) return ('#' + c.slice(1).split('').map((x) => x + x).join('')).toLowerCase();
  const m = c.match(/rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i);
  if (m) return '#' + [m[1], m[2], m[3]].map((n) => Number(n).toString(16).padStart(2, '0')).join('');
  return '#111827';
}

function Divider() {
  return <span className="mx-1 h-6 w-px bg-black/10" />;
}

function ColorButton({ value, onChange, title }: { value: string; onChange: (c: string) => void; title?: string }) {
  const id = useId();
  return (
    <label htmlFor={id} title={title || '颜色'} className="relative grid size-7 cursor-pointer place-items-center rounded-full ring-1 ring-black/10" style={{ background: value }}>
      <input id={id} type="color" value={toHex(value)} onChange={(e) => onChange(e.target.value)} onMouseDown={(e) => e.stopPropagation()} className="absolute inset-0 cursor-pointer opacity-0" />
    </label>
  );
}

function Presets({ onPick }: { onPick: (c: string) => void }) {
  return (
    <div className="flex items-center gap-1">
      {PRESETS.map((c) => (
        <button
          key={c}
          type="button"
          title={c}
          onMouseDown={(e) => e.stopPropagation()}
          onClick={() => onPick(c)}
          className="size-5 rounded-full ring-1 ring-black/10 transition-transform hover:scale-110"
          style={{ background: c }}
        />
      ))}
    </div>
  );
}

function Slider({ label, value, min, max, onChange }: { label: string; value: number; min: number; max: number; onChange: (n: number) => void }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[11px] text-gray-500">{label}</span>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        onMouseDown={(e) => e.stopPropagation()}
        className="h-1 w-24 cursor-pointer accent-gray-900"
      />
      <span className="w-7 text-right text-[11px] tabular-nums text-gray-700">{value}</span>
    </div>
  );
}

function Labeled({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-[11px] text-gray-500">{label}</span>
      {children}
    </div>
  );
}

function Align({ value, onChange }: { value: string; onChange: (a: 'left' | 'center' | 'right') => void }) {
  const opt = (a: 'left' | 'center' | 'right', d: string) => (
    <button
      type="button"
      onMouseDown={(e) => e.stopPropagation()}
      onClick={() => onChange(a)}
      className={`grid size-7 place-items-center rounded-md transition-colors ${value === a ? 'bg-gray-900 text-white' : 'text-gray-500 hover:bg-gray-100'}`}
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
        <path d={d} />
      </svg>
    </button>
  );
  return (
    <div className="flex items-center gap-0.5">
      {opt('left', 'M4 6h16M4 12h10M4 18h13')}
      {opt('center', 'M4 6h16M7 12h10M5 18h14')}
      {opt('right', 'M4 6h16M10 12h10M7 18h13')}
    </div>
  );
}

export default function CanvasPropertyPanel({ kind, values, onChange, onExitPen }: Props) {
  const str = (k: string, d: string) => (typeof values[k] === 'string' ? String(values[k]) : d);
  const num = (k: string, d: number) => (Number.isFinite(Number(values[k])) ? Number(values[k]) : d);

  return (
    <div
      onMouseDown={(e) => e.stopPropagation()}
      className="pointer-events-auto flex items-center gap-1.5 rounded-2xl border border-black/10 bg-white px-2.5 py-1.5 shadow-[0_8px_24px_rgba(0,0,0,0.12)]"
    >
      {kind === 'pen' && (
        <>
          <span className="pl-1 text-[12px] font-medium text-gray-700">画笔</span>
          <ColorButton value={str('color', '#111827')} onChange={(c) => onChange({ color: c })} />
          <Presets onPick={(c) => onChange({ color: c })} />
          <Divider />
          <Slider label="笔宽" value={num('size', 6)} min={1} max={40} onChange={(n) => onChange({ size: n })} />
          <Divider />
          <span className="text-[11px] text-gray-400">拖动绘制 · 双击退出</span>
          <button type="button" onClick={onExitPen} className="rounded-md px-2 py-1 text-[12px] text-gray-600 hover:bg-gray-100">完成</button>
        </>
      )}

      {kind === 'text' && (
        <>
          <ColorButton value={str('color', '#111827')} onChange={(c) => onChange({ color: c })} title="文字颜色" />
          <Divider />
          <select value={str('fontFamily', FONTS[0].v)} onChange={(e) => onChange({ fontFamily: e.target.value })} onMouseDown={(e) => e.stopPropagation()} className={SELECT_CLS}>
            {FONTS.map((f) => <option key={f.v} value={f.v}>{f.label}</option>)}
          </select>
          <select value={String(num('weight', 400))} onChange={(e) => onChange({ weight: Number(e.target.value) })} onMouseDown={(e) => e.stopPropagation()} className={SELECT_CLS}>
            {WEIGHTS.map((w) => <option key={w.v} value={w.v}>{w.label}</option>)}
          </select>
          <Divider />
          <Slider label="字号" value={num('fontSize', 18)} min={8} max={160} onChange={(n) => onChange({ fontSize: n })} />
          <Divider />
          <Align value={str('align', 'left')} onChange={(a) => onChange({ align: a })} />
        </>
      )}

      {kind === 'shape' && (
        <>
          <Labeled label="填充"><ColorButton value={str('fill', 'rgba(99,102,241,0.12)')} onChange={(c) => onChange({ fill: c })} title="填充" /></Labeled>
          <Divider />
          <Labeled label="描边"><ColorButton value={str('stroke', '#6366f1')} onChange={(c) => onChange({ stroke: c })} title="描边" /></Labeled>
          <Divider />
          <Slider label="描边宽" value={num('strokeWidth', 2)} min={0} max={16} onChange={(n) => onChange({ strokeWidth: n })} />
        </>
      )}

      {kind === 'freedraw' && (
        <>
          <span className="pl-1 text-[12px] font-medium text-gray-700">填色</span>
          <ColorButton value={str('color', '#111827')} onChange={(c) => onChange({ color: c })} />
          <Presets onPick={(c) => onChange({ color: c })} />
        </>
      )}
    </div>
  );
}
