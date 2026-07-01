import { useEffect, useRef, useState } from 'react';

// AI 字体生成器「撰写浮窗」:输入文字 + 选/填风格 → 点「生成」调后端(DataEyes 出书法字体艺术图)→ 落画布视口中心。
// 与 GeneratorComposer 同构:非模态、不压暗遮罩、点浮窗外/Esc 关闭、不点「生成」零落地。

export interface FontParams {
  text: string;
  style_name?: string;
}

const STYLE_PRESETS = ['书法', '优雅宋体', '现代黑体', '手写体', '艺术字', '毛笔字'];

const HeadFont = (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 6h14M12 6v13M9 19h6" />
  </svg>
);

interface Props {
  onGenerate: (params: FontParams) => void;
  onClose: () => void;
}

export default function FontComposer({ onGenerate, onClose }: Props) {
  const [text, setText] = useState('');
  const [style, setStyle] = useState('');
  const rootRef = useRef<HTMLDivElement | null>(null);

  // 非模态:点浮窗外(mousedown)或 Esc 关闭;不铺遮罩,画布保持全亮可交互。
  useEffect(() => {
    const onDown = (e: MouseEvent) => { if (rootRef.current && !rootRef.current.contains(e.target as Node)) onClose(); };
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('mousedown', onDown);
    window.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('mousedown', onDown); window.removeEventListener('keydown', onKey); };
  }, [onClose]);

  const submit = () => {
    const t = text.trim();
    if (!t) return;
    onGenerate({ text: t, style_name: style.trim() || undefined });
  };

  return (
    <div
      ref={rootRef}
      data-font-composer
      className="absolute bottom-28 left-1/2 z-50 w-[360px] max-w-[92vw] -translate-x-1/2 overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-2xl"
    >
      <div className="flex h-11 items-center justify-between border-b border-gray-100 px-4">
        <div className="flex min-w-0 items-center gap-2 truncate text-[13px] font-semibold text-gray-800">
          {HeadFont}
          AI 字体生成器
          <span className="ml-1 shrink-0 text-[11px] font-normal text-gray-400">1024 × 1024</span>
        </div>
        <button type="button" onClick={onClose} className="text-gray-400 transition-colors hover:text-gray-700">✕</button>
      </div>

      <div className="space-y-2.5 p-4">
        {/* 文字 */}
        <textarea
          autoFocus
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); submit(); } }}
          rows={2}
          placeholder="输入要生成的文字，如「福气」「新年快乐」(Ctrl/⌘+Enter 生成)"
          className="w-full resize-none rounded-lg border border-gray-200 px-3 py-2 text-[13px] text-gray-800 outline-none focus:border-purple-400"
        />

        {/* 风格:自由输入 + 快捷预设 */}
        <input
          value={style}
          onChange={(e) => setStyle(e.target.value)}
          placeholder="字体风格(可选)，如 书法 / 优雅宋体"
          className="w-full rounded-lg border border-gray-200 px-3 py-2 text-[13px] text-gray-800 outline-none focus:border-purple-400"
        />
        <div className="flex flex-wrap items-center gap-1">
          {STYLE_PRESETS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setStyle((cur) => (cur === s ? '' : s))}
              className={`rounded-md px-2 py-0.5 text-[11px] transition-colors ${style === s ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
            >
              {s}
            </button>
          ))}
        </div>

        {/* 生成 */}
        <button
          type="button"
          onClick={submit}
          disabled={!text.trim()}
          className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-gradient-to-r from-violet-500 to-fuchsia-500 px-3 py-2 text-[13px] font-medium text-white transition-opacity disabled:opacity-50"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 19V5M5 12l7-7 7 7" /></svg>
          生成字体
        </button>
        <p className="text-center text-[10px] text-gray-400">约 15 秒出图 · 不点「生成」不消耗、画布零落地</p>
      </div>
    </div>
  );
}
