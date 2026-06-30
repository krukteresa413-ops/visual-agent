import { memo, useRef, useState, type ChangeEvent } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { api } from '../../api/client';

// Phase A / Lovart 对齐:画布内 AI 图 / 视频「生成节点」。
// 表单布局 1:1 对齐 Lovart 的 Image/Video Generator:
//   头部(图标+标题+输出分辨率) · 参考图 · prompt「今天我们要创作什么」· 选项链片+模型+积分 · 生成。
// 临时输入卡片:生成完成后由 CanvasFlow 把本节点就地替换成标准图片/视频节点(AssetNode)。
// 生成动作由 CanvasFlow 通过 data.onGenerate 注入(它持有 api/projectId/setNodes)。

type GenKind = 'image' | 'video';
type GenStatus = 'idle' | 'generating' | 'error';

interface GenerateParams {
  prompt: string;
  reference_image_url?: string;
  width: number;
  height: number;
  ratio: string;
  brief: Record<string, unknown>;
}

interface GeneratorNodeData {
  kind?: GenKind;
  status?: GenStatus;
  error?: string;
  width?: number;
  onGenerate?: (id: string, params: GenerateParams) => void;
}

// 图片比例:决定输出分辨率标签 + 结果节点画布尺寸 + brief.aspect_ratio。
const IMG_RATIOS: Array<{ id: string; dim: string; w: number; h: number }> = [
  { id: '1:1', dim: '1024 × 1024', w: 320, h: 320 },
  { id: '3:4', dim: '768 × 1024', w: 300, h: 400 },
  { id: '16:9', dim: '1280 × 720', w: 384, h: 216 },
];
const VIDEO = { dim: '1920 × 1080', w: 360, h: 203 };

const HeadImage = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E8830C" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4.5" width="18" height="15" rx="2.5" /><circle cx="8.5" cy="9.5" r="1.5" /><path d="M3 16l5-4 4 3 3-2 6 5" />
  </svg>
);
const HeadVideo = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#377ADD" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="5" width="18" height="14" rx="2.5" /><path d="M10 9.5l5 2.5-5 2.5z" fill="#377ADD" stroke="none" />
  </svg>
);

function GeneratorNode({ id, data, selected }: NodeProps) {
  const node = data as GeneratorNodeData;
  const kind: GenKind = node.kind === 'video' ? 'video' : 'image';
  const isVideo = kind === 'video';
  const status: GenStatus = node.status || 'idle';
  const generating = status === 'generating';

  const [prompt, setPrompt] = useState('');
  const [refUrl, setRefUrl] = useState<string | undefined>(undefined);
  const [refBusy, setRefBusy] = useState(false);
  const [ratioId, setRatioId] = useState(IMG_RATIOS[0].id);
  const [vtab, setVtab] = useState('视频');
  const fileRef = useRef<HTMLInputElement | null>(null);

  const width = Number(node.width || (isVideo ? VIDEO.w : 300));
  const credits = isVideo ? 90 : 15;
  const chosen = IMG_RATIOS.find((r) => r.id === ratioId) || IMG_RATIOS[0];
  const dim = isVideo ? VIDEO.dim : chosen.dim;

  const pickRef = () => { if (!generating) fileRef.current?.click(); };

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
    if (!text || generating) return;
    const size = isVideo ? VIDEO : { w: chosen.w, h: chosen.h };
    node.onGenerate?.(id, {
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

  const chip = 'rounded-md bg-gray-100 px-1.5 py-0.5 text-gray-500';

  return (
    <div
      data-flow-generator-node
      data-gen-kind={kind}
      data-gen-status={status}
      className={`overflow-hidden rounded-xl border bg-white shadow-sm transition-shadow ${selected ? 'border-orange-400 ring-2 ring-orange-300/50' : 'border-gray-200'}`}
      style={{ width }}
    >
      <Handle type="target" position={Position.Left} className="!h-2 !w-2 !bg-gray-300" />

      {/* 头部:图标 + 标题 + 输出分辨率 */}
      <div className="flex h-9 items-center justify-between border-b border-gray-100 px-3">
        <div className="flex min-w-0 items-center gap-1.5 truncate text-[12px] font-semibold text-gray-800">
          {isVideo ? HeadVideo : HeadImage}
          {isVideo ? 'Video Generator' : 'Image Generator'}
        </div>
        <span className="ml-2 shrink-0 text-[11px] tabular-nums text-gray-400">{dim}</span>
      </div>

      <div className="relative space-y-2 p-3">
        {/* 视频:素材类型 tab */}
        {isVideo && (
          <div className="flex items-center gap-0.5">
            {['视频', '图片', '音频'].map((t) => (
              <button
                key={t}
                type="button"
                onMouseDown={(e) => e.stopPropagation()}
                onClick={() => setVtab(t)}
                className={`nodrag rounded-md px-2.5 py-1 text-[11px] transition-colors ${vtab === t ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
              >
                {t}
              </button>
            ))}
          </div>
        )}

        {/* 参考图槽 */}
        <button
          type="button"
          onMouseDown={(e) => e.stopPropagation()}
          onClick={pickRef}
          className="nodrag flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-gray-300 py-2 text-[11px] text-gray-500 transition-colors hover:border-orange-300 hover:text-orange-500"
        >
          {refBusy ? (
            <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-gray-300 border-t-orange-400" />
          ) : refUrl ? (
            <>
              <img src={refUrl} alt="" className="h-5 w-5 rounded object-cover" />
              <span className="truncate">{isVideo ? '参考图/视频已添加 · 点击更换' : '参考图已添加 · 点击更换'}</span>
            </>
          ) : (
            <>＋ {isVideo ? '参考图/视频(可选)' : '添加参考图'}</>
          )}
        </button>
        <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={onRefFile} />

        {/* prompt */}
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onMouseDown={(e) => e.stopPropagation()}
          onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); submit(); } }}
          rows={2}
          disabled={generating}
          placeholder="今天我们要创作什么"
          className="nodrag w-full resize-none rounded-lg border border-gray-200 px-2.5 py-1.5 text-[12px] text-gray-800 outline-none focus:border-orange-400 disabled:bg-gray-50"
        />

        {/* 选项行:比例/规格链片 + 模型 + 积分 */}
        <div className="flex flex-wrap items-center gap-1 text-[10px]">
          {isVideo ? (
            <span className={chip}>Auto · 5s · 720p</span>
          ) : (
            IMG_RATIOS.map((r) => (
              <button
                key={r.id}
                type="button"
                onMouseDown={(e) => e.stopPropagation()}
                onClick={() => setRatioId(r.id)}
                className={`nodrag rounded-md px-1.5 py-0.5 transition-colors ${ratioId === r.id ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
              >
                {r.id}
              </button>
            ))
          )}
          <span className={chip}>{isVideo ? 'Seedance' : 'GPT Image'}</span>
          <span className="ml-auto rounded-md bg-amber-50 px-1.5 py-0.5 font-medium text-amber-600">⚡{credits}</span>
        </div>

        {status === 'error' && node.error && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-2 py-1 text-[10px] text-amber-700">⚠ {node.error}</div>
        )}

        {/* 生成 */}
        <button
          type="button"
          onMouseDown={(e) => e.stopPropagation()}
          onClick={submit}
          disabled={generating || !prompt.trim()}
          className="nodrag flex w-full items-center justify-center gap-1.5 rounded-lg bg-gradient-to-r from-orange-500 to-rose-500 px-3 py-1.5 text-[12px] font-medium text-white transition-opacity disabled:opacity-50"
        >
          {generating ? '生成中…' : (
            <>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 19V5M5 12l7-7 7 7" /></svg>
              生成
            </>
          )}
        </button>

        {generating && (
          <div className="absolute inset-0 z-10 grid place-items-center rounded-b-xl bg-white/70 backdrop-blur-[1px]">
            <div className="flex flex-col items-center gap-2 text-[11px] text-gray-600">
              <span className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500" />
              {isVideo ? '生成视频中(约 1-2 分钟)…' : '生成图片中…'}
            </div>
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Right} className="!h-2 !w-2 !bg-gray-300" />
    </div>
  );
}

export default memo(GeneratorNode);
