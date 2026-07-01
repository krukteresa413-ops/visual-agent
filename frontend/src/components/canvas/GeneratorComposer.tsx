import { useEffect, useRef, useState, type ChangeEvent } from 'react';
import { api } from '../../api/client';

// AI 图 / 视频「撰写浮窗」:替代原先「往画布丢生成节点」的做法 —— 点工具栏 AI图/AI视频弹出本浮窗
// 让用户撰写;点「生成」才真正生成并把结果落到视口中心,关闭即零落地(不生成、不在画布留任何东西)。
// 表单沿用原 GeneratorNode 的字段(参考图 · prompt · 比例/规格 · 模型 · 积分)。

export type GenKind = 'image' | 'video';

export interface GenerateParams {
  prompt: string;
  reference_image_url?: string;
  width: number;
  height: number;
  ratio: string;
  brief: Record<string, unknown>;
}

// 图片比例:决定输出分辨率标签 + 结果节点画布尺寸 + brief.aspect_ratio。
const IMG_RATIOS: Array<{ id: string; dim: string; w: number; h: number }> = [
  { id: '1:1', dim: '1024 × 1024', w: 320, h: 320 },
  { id: '3:4', dim: '768 × 1024', w: 300, h: 400 },
  { id: '16:9', dim: '1280 × 720', w: 384, h: 216 },
];
const VIDEO = { dim: '1920 × 1080', w: 360, h: 203 };

const HeadImage = (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#E8830C" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4.5" width="18" height="15" rx="2.5" /><circle cx="8.5" cy="9.5" r="1.5" /><path d="M3 16l5-4 4 3 3-2 6 5" />
  </svg>
);
const HeadVideo = (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#377ADD" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="5" width="18" height="14" rx="2.5" /><path d="M10 9.5l5 2.5-5 2.5z" fill="#377ADD" stroke="none" />
  </svg>
);

interface Props {
  kind: GenKind;
  onGenerate: (params: GenerateParams) => void;
  onClose: () => void;
}

export default function GeneratorComposer({ kind, onGenerate, onClose }: Props) {
  const isVideo = kind === 'video';
  const [prompt, setPrompt] = useState('');
  const [refUrl, setRefUrl] = useState<string | undefined>(undefined);
  const [refBusy, setRefBusy] = useState(false);
  const [ratioId, setRatioId] = useState(IMG_RATIOS[0].id);
  const [vtab, setVtab] = useState('视频');
  const fileRef = useRef<HTMLInputElement | null>(null);
  const rootRef = useRef<HTMLDivElement | null>(null);

  // 非模态:点浮窗外(mousedown)或按 Esc 关闭。不铺全屏遮罩,画布保持全亮、可交互(仿「模型偏好」浮层)。
  useEffect(() => {
    const onDown = (e: MouseEvent) => { if (rootRef.current && !rootRef.current.contains(e.target as Node)) onClose(); };
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('mousedown', onDown);
    window.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('mousedown', onDown); window.removeEventListener('keydown', onKey); };
  }, [onClose]);

  const credits = isVideo ? 90 : 15;
  const chosen = IMG_RATIOS.find((r) => r.id === ratioId) || IMG_RATIOS[0];
  const dim = isVideo ? VIDEO.dim : chosen.dim;
  const chip = 'rounded-md bg-gray-100 px-1.5 py-0.5 text-gray-500';

  const onRefFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (e.target) e.target.value = '';
    if (!file) return;
    setRefBusy(true);
    try {
      const form = new FormData();
      form.append('file', file);
      const res = (await api.upload.image(form)) as { url?: string };
      if (res?.url) setRefUrl(res.url);
    } catch {
      /* 上传失败,静默;可重试 */
    } finally {
      setRefBusy(false);
    }
  };

  const submit = () => {
    const text = prompt.trim();
    if (!text) return;
    const size = isVideo ? VIDEO : { w: chosen.w, h: chosen.h };
    onGenerate({
      prompt: text,
      reference_image_url: refUrl,
      width: size.w,
      height: size.h,
      ratio: isVideo ? '16:9' : ratioId,
      brief: {
        aspect_ratio: isVideo ? '16:9' : ratioId,
        ...(isVideo ? { duration_seconds: 5, resolution: '720p' } : { count: 1 }),
      },
    });
  };

  return (
    <div
      ref={rootRef}
      data-gen-composer
      data-gen-kind={kind}
      className="absolute bottom-28 left-1/2 z-50 w-[360px] max-w-[92vw] -translate-x-1/2 overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-2xl"
    >
      {/* 头部:图标 + 标题 + 输出分辨率 + 关闭 */}
        <div className="flex h-11 items-center justify-between border-b border-gray-100 px-4">
          <div className="flex min-w-0 items-center gap-2 truncate text-[13px] font-semibold text-gray-800">
            {isVideo ? HeadVideo : HeadImage}
            {isVideo ? 'AI 视频生成' : 'AI 图片生成'}
            <span className="ml-1 shrink-0 text-[11px] tabular-nums font-normal text-gray-400">{dim}</span>
          </div>
          <button type="button" onClick={onClose} className="text-gray-400 transition-colors hover:text-gray-700">✕</button>
        </div>

        <div className="space-y-2.5 p-4">
          {/* 视频:素材类型 tab */}
          {isVideo && (
            <div className="flex items-center gap-1">
              {['视频', '图片', '音频'].map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setVtab(t)}
                  className={`rounded-md px-2.5 py-1 text-[11px] transition-colors ${vtab === t ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
                >
                  {t}
                </button>
              ))}
            </div>
          )}

          {/* 参考图槽 */}
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-gray-300 py-2.5 text-[12px] text-gray-500 transition-colors hover:border-orange-300 hover:text-orange-500"
          >
            {refBusy ? (
              <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-gray-300 border-t-orange-400" />
            ) : refUrl ? (
              <>
                <img src={refUrl} alt="" className="h-5 w-5 rounded object-cover" />
                <span className="truncate">{isVideo ? '参考图/视频已添加 · 点击更换' : '参考图已添加 · 点击更换'}</span>
              </>
            ) : (
              <>＋ {isVideo ? '参考图/视频(可选)' : '添加参考图(可选)'}</>
            )}
          </button>
          <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={onRefFile} />

          {/* prompt */}
          <textarea
            autoFocus
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); submit(); } }}
            rows={3}
            placeholder="今天我们要创作什么(Ctrl/⌘+Enter 生成)"
            className="w-full resize-none rounded-lg border border-gray-200 px-3 py-2 text-[13px] text-gray-800 outline-none focus:border-orange-400"
          />

          {/* 选项行:比例/规格链片 + 模型 + 积分 */}
          <div className="flex flex-wrap items-center gap-1 text-[11px]">
            {isVideo ? (
              <span className={chip}>Auto · 5s · 720p</span>
            ) : (
              IMG_RATIOS.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => setRatioId(r.id)}
                  className={`rounded-md px-2 py-0.5 transition-colors ${ratioId === r.id ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
                >
                  {r.id}
                </button>
              ))
            )}
            <span className={chip}>{isVideo ? 'Seedance' : 'GPT Image'}</span>
            <span className="ml-auto rounded-md bg-amber-50 px-1.5 py-0.5 font-medium text-amber-600">⚡{credits}</span>
          </div>

          {/* 生成 */}
          <button
            type="button"
            onClick={submit}
            disabled={!prompt.trim()}
            className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-gradient-to-r from-orange-500 to-rose-500 px-3 py-2 text-[13px] font-medium text-white transition-opacity disabled:opacity-50"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 19V5M5 12l7-7 7 7" /></svg>
            生成
          </button>
          <p className="text-center text-[10px] text-gray-400">不点「生成」不会消耗积分,也不会在画布留下任何东西</p>
        </div>
      </div>
  );
}
