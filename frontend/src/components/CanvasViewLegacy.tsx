import { useState, useRef, useCallback, useEffect } from 'react';
import ContextMenu from './ContextMenu';
import FontGeneratorPanel from './FontGeneratorPanel';
import ScoreCard from './ScoreCard';
import { api } from '../api/client';

// ── Types ──────────────────────────────────────────────────────

interface CanvasChatAsset {
  id: string;
  label: string;
  image_url?: string;
  type?: string;
  metadata?: Record<string, any>;
}

interface CanvasViewProps {
  mainImage?: any;
  whiteBg?: any;
  sceneImages?: any[];
  sellingPoints?: any[];
  videoScripts?: any[];
  adMaterial?: any;
  brief?: any;
  projectId?: number; isLight?: boolean;
  generationTaskId?: string | null;
  qualityReport?: any;
  onAddToChat?: (asset: CanvasChatAsset) => void;
  onEditPrompt?: (prompt: string) => void;
  canvasRefreshNonce?: number;
}

interface CanvasElement {
  id: string; type: string; label: string;
  x: number; y: number; width: number; height: number;
  rotation?: number; zIndex?: number; hidden?: boolean; locked?: boolean;
  editableLayers?: Array<Record<string, any>>;
  thumbnail_url?: string; asset_ref?: Record<string, any>;
  metadata?: Record<string, any>;
}

interface CanvasConnection {
  id: string; source_id: string; target_id: string; label?: string; relation_type?: string;
}

interface ViewportState { x: number; y: number; scale: number; }

interface TimelineEntry {
  id: number; prompt: string; timestamp: string;
  asset_type: string; thumbnail_url?: string;
  model_used?: string; generation_seconds?: number;
}

interface AssetItem {
  id: string; type: string; label: string;
  url?: string; preview_url?: string; text_preview?: string;
  created_at?: string; metadata?: Record<string, any>;
}

// ── Helpers ────────────────────────────────────────────────────

function buildDefaultElements(props: CanvasViewProps): CanvasElement[] {
  const els: CanvasElement[] = [];
  let col = 0;
  const add = (id: string, type: string, label: string, data: any, w = 320, h = 400) => {
    if (!data) return;
    els.push({
      id, type, label,
      x: 60 + col * 370, y: 60,
      width: w, height: h,
      thumbnail_url: data?.url || data?.preview_url,
      metadata: data,
      asset_ref: { asset_type: type },
    });
    col++;
  };

  add('kv01', 'key_visual', 'KV_01_Main', props.mainImage);
  if (props.whiteBg) add('whitebg', 'white_bg', 'White BG', props.whiteBg, 280, 350);
  (props.sceneImages || []).forEach((s: any, i: number) =>
    add(`scene${i}`, 'scene_image', s?.scene_name || `Scene ${i + 1}`, s, 300, 240));
  (props.videoScripts || []).forEach((v: any, i: number) =>
    add(`video${i}`, 'video', v?.video_goal || `Video ${i + 1}`, v, 300, 220));
  // 卖点/广告素材是文案方案而非图片，仅当它确实带图时才上画布；否则不建空占位卡。
  (props.sellingPoints || []).forEach((sp: any, i: number) => {
    if (!sp?.url && !sp?.thumbnail_url) return;
    add(`sp${i}`, 'graphic', sp?.title || `SP ${i + 1}`, sp, 240, 200);
  });
  if (props.adMaterial?.url || props.adMaterial?.thumbnail_url) {
    add('ad', 'graphic', 'Ad Material', props.adMaterial, 260, 220);
  }
  return els;
}


function mergeGeneratedElements(existing: CanvasElement[], generated: CanvasElement[]): CanvasElement[] {
  const existingUrls = new Set(existing.map(el => el.thumbnail_url).filter(Boolean));
  let nextX = existing.reduce((max, el) => Math.max(max, el.x + el.width + 80), 60);
  const additions = generated
    .filter(el => el.thumbnail_url && !existingUrls.has(el.thumbnail_url))
    .map((el, idx) => ({
      ...el,
      id: `${el.id}_${Date.now()}_${idx}`,
      x: nextX + idx * 370,
      y: 60,
    }));
  return additions.length ? [...existing, ...additions] : existing;
}

function buildDefaultConnections(_elements: CanvasElement[]): CanvasConnection[] {
  // 不再自动用 'next' 串联相邻节点；连线只在用户显式创建关系时产生。
  return [];
}

// ── SVG Connection Lines ───────────────────────────────────────

function ConnectionLines({
  elements, connections, onLabelChange,
}: {
  elements: CanvasElement[]; connections: CanvasConnection[]; viewport: ViewportState; onLabelChange?: (connectionId: string, label: string) => void;
}) {
  const elMap = new Map(elements.map(e => [e.id, e]));
  return (
    <svg className="absolute inset-0 pointer-events-none" style={{ width: '100%', height: '100%', overflow: 'visible' }}>
      {connections.map(conn => {
        const src = elMap.get(conn.source_id);
        const tgt = elMap.get(conn.target_id);
        if (!src || !tgt) return null;
        const x1 = src.x + src.width / 2;
        const y1 = src.y + src.height;
        const x2 = tgt.x + tgt.width / 2;
        const y2 = tgt.y;
        const mx = (x1 + x2) / 2;
        const d = `M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`;
        return (
          <g key={conn.id}>
            <path d={d} fill="none" stroke="rgba(156,163,175,0.35)" strokeWidth={2} />
            {(conn.label || conn.relation_type) && (
              <foreignObject x={mx - 120} y={(y1 + y2) / 2 - 18} width={240} height={32} className="pointer-events-auto">
                <input
                  data-editable-relation-edge
                  data-relation-label-input
                  value={conn.label || conn.relation_type || ''}
                  onChange={(event) => onLabelChange?.(conn.id, event.target.value)}
                  title={conn.label || conn.relation_type || ''}
                  className="w-full rounded-full border border-orange-200 bg-white/95 px-2 py-1 text-center text-[10px] text-orange-700 shadow-sm outline-none focus:border-orange-400"
                />
              </foreignObject>
            )}
          </g>
        );
      })}
    </svg>
  );
}

// ── Element Card ────────────────────────────────────────────────

function ElementCard({
  el, isSelected, onClick, onDelete, qualityScore, isCompareA, isCompareB,
}: {
  el: CanvasElement; isSelected: boolean;
  onClick: () => void; onDelete?: () => void; scale: number;
  qualityScore?: number; isCompareA?: boolean; isCompareB?: boolean;
}) {
  const hasImage = !!el.thumbnail_url;
  const meta = el.metadata || {};

  const previewTextValue = (() => {
    if (el.type === 'key_visual' || el.type === 'main_image')
      return meta?.goal || meta?.prompt?.slice(0, 60) || '';
    if (el.type === 'scene_image')
      return meta?.scene_narrative?.slice(0, 60) || meta?.prompt?.slice(0, 60) || '';
    if (el.type === 'video')
      return `${meta?.duration_seconds || '?'}s · ${meta?.pacing || ''}`;
    if (el.type === 'graphic')
      return meta?.title || meta?.description?.slice(0, 60) || '';
    if (el.type === 'font_generation')
      return meta?.style_description?.slice(0, 60) || '自定义字体';
    return '';
  })();

  const statusBadge = meta?.status === 'complete' ? '✓' :
    meta?.status === 'in_progress' ? '⋯' : '';

  return (
    <div
      onClick={(e) => { e.stopPropagation(); onClick(); }}
      className={`absolute cursor-pointer rounded-2xl overflow-hidden transition-all duration-300 bg-white
        ${isSelected
          ? 'ring-2 ring-orange-400 shadow-xl shadow-orange-200/50 scale-[1.02] z-30'
          : 'shadow-sm shadow-black/5 hover:shadow-md hover:shadow-black/10 border border-gray-100 z-10'}`}
      style={{
        left: el.x, top: el.y, width: el.width, height: el.height,
      }}
    >
      {isSelected && (
        <LovartImageActionBar onModify={() => {}} onDelete={() => onDelete?.()} />
      )}

      {/* Visual thumbnail */}
      <div className="relative w-full bg-gray-100 flex items-center justify-center overflow-hidden"
        style={{ height: el.height - 56 }}>
        {hasImage && el.type === 'video' ? (
          <video src={el.thumbnail_url} controls className="w-full h-full object-cover bg-black" />
        ) : hasImage ? (
          <img src={el.thumbnail_url} alt={el.label}
            className="w-full h-full object-cover" />
        ) : (
          <div className="flex flex-col items-center gap-2 text-gray-400">
            <span className="text-3xl">
              {el.type === 'key_visual' ? '🖼️' : el.type === 'video' ? '🎬' :
               el.type === 'scene_image' ? '🌄' : el.type === 'graphic' ? '图形' : 
               el.type === 'font_generation' ? '🔤' : el.type === 'video' ? '视频' : '文档'}
            </span>
            <span className="text-xs">{el.type}</span>
          </div>
        )}

        {/* Top-left tag */}
        {meta?.direction && (
          <span className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded-md bg-white/90 text-[11px] text-gray-500 font-medium shadow-sm">
            {meta.direction}
          </span>
        )}

        {/* Quality score */}
        {qualityScore != null && (
          <span className="absolute top-2.5 right-2.5 px-2 py-0.5 rounded-md text-[11px] font-bold bg-orange-100 text-orange-600">
            {qualityScore.toFixed(0)}分
          </span>
        )}

        {/* Compare badges */}
        {isCompareA && (
          <span className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded-md text-[11px] font-bold bg-orange-500 text-white shadow-sm">对比A</span>
        )}
        {isCompareB && (
          <span className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded-md text-[11px] font-bold bg-purple-500 text-white shadow-sm">对比B</span>
        )}

        {/* Status */}
        {statusBadge && (
          <span className={`absolute top-2.5 right-2.5 px-2 py-0.5 rounded-md text-[11px] font-bold ${
            statusBadge === '✓' ? 'bg-green-100 text-green-600' : 'bg-yellow-100 text-yellow-600'}`}>
            {statusBadge === '✓' ? '已完成' : '进行中'}
          </span>
        )}
      </div>

      {/* Label */}
      <div className="h-14 px-3.5 flex items-center bg-white border-t border-gray-100">
        <div className="min-w-0">
          <p className="text-[13px] font-semibold text-gray-800 truncate">{el.label}</p>
          {previewTextValue && (
            <p className="text-[11px] text-gray-400 truncate mt-0.5">{previewTextValue}</p>
          )}
        </div>
      </div>
    </div>
  );
}

function LovartImageActionBar({ onModify, onDelete }: { onModify: () => void; onDelete: () => void }) {
  const actions = ['变体', '扩图', '擦除', '换背景', '导出'];
  return (
    <div
      data-lovart-image-action-bar
      className="absolute -top-12 left-1/2 z-40 flex -translate-x-1/2 items-center gap-1 rounded-[14px] border px-1.5 py-1 shadow-xl"
      style={{
        background: 'var(--lo-bg-float)',
        borderColor: 'var(--lo-border-neutral-l1)',
        boxShadow: 'var(--lo-shadow-elevation-300)',
      }}
      onClick={(event) => event.stopPropagation()}
    >
      {actions.map(action => (
        <button
          key={action}
          className="h-8 rounded-lg px-2 text-[11px] transition-colors hover:bg-black/[0.06]"
          style={{ color: 'var(--lo-text-secondary)' }}
          title={action}
        >
          {action}
        </button>
      ))}
      <div className="mx-1 h-4 w-px bg-black/[0.07]" />
      <button onClick={onModify} className="h-8 rounded-lg px-2 text-[11px] text-blue-500 hover:bg-blue-50" title="自然语言修改">AI</button>
      <button onClick={onDelete} className="h-8 rounded-lg px-2 text-[11px] text-red-500 hover:bg-red-50" title="删除">删</button>
    </div>
  );
}

// ── Timeline Bar (process story + real history from API) ─────────────────────

interface HistoryRecord {
  id: number;
  project_id: number;
  brief_id: number | null;
  model_used: string;
  generation_seconds: number;
  created_at: string;
  prompt?: string;
}

type TraceEventKind = 'Signal' | 'Interpretation' | 'Attempt' | 'Action' | 'Artifact';

type TimelineProgressEvent = {
  step?: string;
  percent?: number;
  status?: string;
  message?: string;
  type?: string;
};

type AiTraceEvent = {
  id: string;
  kind: TraceEventKind;
  title: string;
  detail: string;
  percent: number;
};

const AI_TRACE_EVENT_TYPES: Record<TraceEventKind, { label: string; icon: string; className: string }> = {
  Signal: { label: '识别', icon: '✓', className: 'text-blue-600 bg-blue-50 border-blue-100' },
  Interpretation: { label: '判断', icon: '→', className: 'text-violet-600 bg-violet-50 border-violet-100' },
  Attempt: { label: '尝试', icon: '●', className: 'text-orange-600 bg-orange-50 border-orange-100' },
  Action: { label: '动作', icon: '↳', className: 'text-emerald-600 bg-emerald-50 border-emerald-100' },
  Artifact: { label: '结果', icon: '◆', className: 'text-gray-700 bg-gray-50 border-gray-200' },
};

function buildTraceEventFromProgress(event: TimelineProgressEvent): AiTraceEvent {
  const step = event.step || '生成过程';
  const message = event.message || '正在形成视觉方案';
  const percent = event.percent ?? 0;

  if (step.includes('分析')) {
    return { id: `${step}-${percent}`, kind: 'Signal', title: '识别输入信号', detail: message, percent };
  }
  if (step.includes('策略')) {
    return { id: `${step}-${percent}`, kind: 'Interpretation', title: '形成创意判断', detail: message, percent };
  }
  if (step.includes('主图') || step.includes('白底') || step.includes('场景') || step.includes('卖点') || step.includes('视频')) {
    return { id: `${step}-${percent}`, kind: 'Attempt', title: `尝试${step.replace('生成', '')}`, detail: message, percent };
  }
  if (step.includes('渲染') || step.includes('排版')) {
    return { id: `${step}-${percent}`, kind: 'Action', title: step, detail: message, percent };
  }
  if (step.includes('完成') || event.status === 'done') {
    return { id: `${step}-${percent}`, kind: 'Artifact', title: '写入画布结果', detail: message, percent: 100 };
  }
  return { id: `${step}-${percent}`, kind: 'Action', title: step, detail: message, percent };
}

function defaultTraceEvents(latest?: HistoryRecord): AiTraceEvent[] {
  if (latest) {
    return [
      { id: 'history-signal', kind: 'Signal', title: '读取最近生成记录', detail: `找到 #${latest.id} 的生成结果`, percent: 100 },
      { id: 'history-artifact', kind: 'Artifact', title: '可回看画布结果', detail: `耗时 ${latest.generation_seconds || 0}s · ${latest.model_used || 'AI生成'}`, percent: 100 },
    ];
  }
  return [
    { id: 'empty-signal', kind: 'Signal', title: '等待输入信号', detail: '上传资料或输入产品描述后开始识别', percent: 0 },
    { id: 'empty-attempt', kind: 'Attempt', title: '准备生成假设', detail: 'AI 会把识别内容转成创作尝试', percent: 0 },
    { id: 'empty-artifact', kind: 'Artifact', title: '等待画布结果', detail: '生成中的图片、文案和布局会逐步落到画布', percent: 0 },
  ];
}

function TimelineBar({ projectId, generationTaskId, onRestore, onEditPrompt, refreshTrigger }: {
  projectId?: number;
  generationTaskId?: string | null;
  onRestore?: (record: HistoryRecord) => void;
  onEditPrompt?: (prompt: string) => void;
  refreshTrigger?: number;
}) {
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [timelineProgress, setTimelineProgress] = useState<TimelineProgressEvent | null>(null);
  const [traceEvents, setTraceEvents] = useState<AiTraceEvent[]>([]);
  const latest = records[0];
  const isRealtime = Boolean(generationTaskId && timelineProgress && timelineProgress.status !== 'done');
  const progressPercent = isRealtime ? (timelineProgress?.percent ?? 0) : latest ? 100 : 0;
  const visibleTraceEvents = (traceEvents.length ? traceEvents : defaultTraceEvents(latest)).slice(-5);

  const fetchHistory = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const resp = await fetch(`/api/v1/projects/${projectId}/history`);
      if (!resp.ok) return;
      const data = await resp.json();
      setRecords(Array.isArray(data.records) ? data.records : []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory, refreshTrigger]);

  useEffect(() => {
    if (!generationTaskId) {
      setTimelineProgress(null);
      setTraceEvents([]);
      return;
    }

    const ctrl = new AbortController();
    const initialEvent = { step: '分析需求', percent: 1, status: 'thinking', message: '正在形成视觉方案' };
    setTimelineProgress(initialEvent);
    setTraceEvents([buildTraceEventFromProgress(initialEvent)]);

    fetch(api.progress.streamUrl(generationTaskId), { signal: ctrl.signal })
      .then(async (response) => {
        if (!response.ok || !response.body) return;
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            try {
              const data = JSON.parse(line.slice(6)) as TimelineProgressEvent;
              if (data.type === 'heartbeat') continue;
              const nextTrace = buildTraceEventFromProgress(data);
              setTimelineProgress(data);
              setTraceEvents((prev) => {
                if (prev[prev.length - 1]?.id === nextTrace.id) return prev;
                return [...prev, nextTrace].slice(-12);
              });
            } catch {
              // ignore malformed SSE chunk
            }
          }
        }
      })
      .catch(() => {
        if (!ctrl.signal.aborted) {
          const fallback = { step: '分析需求', percent: 1, status: 'generating', message: '正在形成视觉方案' };
          setTimelineProgress((prev) => prev || fallback);
          setTraceEvents((prev) => prev.length ? prev : [buildTraceEventFromProgress(fallback)]);
        }
      });

    return () => ctrl.abort();
  }, [generationTaskId]);

  return (
    <div
      data-ai-trace-panel="true"
      data-prompt-history-panel="true"
      data-process-timeline="true"
      data-trace-progress={progressPercent}
      className="relative -top-1 border-t border-gray-200 bg-white/95 backdrop-blur-xl"
    >
      <div className="flex items-center gap-4 px-3 py-1.5">
        <div className="w-[210px] flex-shrink-0">
          <div className="flex items-center justify-between gap-2">
            <p className="text-[11px] font-medium text-gray-800">Prompt历史</p>
            <span className="text-[10px] tabular-nums text-orange-500">{progressPercent}%</span>
          </div>
          <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-gray-100">
            <div
              className="h-full rounded-full bg-gradient-to-r from-orange-400 to-orange-500 transition-all duration-500"
              style={{ width: `${Math.max(3, Math.min(progressPercent, 100))}%` }}
            />
          </div>
          <p className="mt-1 truncate text-[9px] text-gray-400">
            {isRealtime ? '正在形成视觉方案' : loading ? '同步历史...' : latest ? `最近结果 #${latest.id}` : '等待首次 Prompt'}
          </p>
        </div>

        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-center justify-between">
            <span className="text-[10px] font-medium text-gray-500">历史输入 / 二次修改</span>
            {latest && !isRealtime && (
              <button
                onClick={() => onRestore?.(latest)}
                className="text-[10px] text-gray-500 transition-colors hover:text-orange-500"
                title={`查看最近一次生成 #${latest.id}`}
              >
                查看 #{latest.id}
              </button>
            )}
          </div>
          <div className="flex gap-2 overflow-x-auto pb-0.5 scrollbar-thin" style={{ scrollbarWidth: 'thin' }}>
            {records.filter((record) => record.prompt?.trim()).slice(0, 6).map((record) => (
              <div
                key={`prompt-${record.id}`}
                data-prompt-history-item="true"
                title={record.prompt}
                className="flex h-9 min-w-[220px] max-w-[280px] items-center gap-2 rounded-lg border border-orange-100 bg-orange-50/60 px-2 shadow-sm"
              >
                <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full border border-orange-200 bg-white text-[10px] text-orange-500">P</span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[10px] font-medium leading-3 text-gray-800">Prompt #{record.id}</span>
                  <span className="block truncate text-[9px] leading-3 text-gray-500">{record.prompt}</span>
                </span>
                <button
                  onClick={() => record.prompt && onEditPrompt?.(record.prompt)}
                  className="flex-shrink-0 rounded-md border border-orange-200 bg-white px-1.5 py-0.5 text-[9px] text-orange-600 hover:bg-orange-100"
                  title="二次修改这个 Prompt"
                >
                  二次修改
                </button>
              </div>
            ))}
            {records.filter((record) => record.prompt?.trim()).length === 0 && visibleTraceEvents.map((event) => {
              const type = AI_TRACE_EVENT_TYPES[event.kind];
              return (
                <div
                  key={event.id}
                  data-trace-event-kind={event.kind}
                  title={event.detail}
                  className="flex h-9 min-w-[190px] max-w-[240px] items-center gap-2 rounded-lg border border-gray-200 bg-white px-2 shadow-sm"
                >
                  <span className={`flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full border text-[10px] ${type.className}`}>{type.icon}</span>
                  <span className="min-w-0">
                    <span className="block truncate text-[10px] font-medium leading-3 text-gray-800">
                      {type.label} · {event.title}
                    </span>
                    <span className="block truncate text-[9px] leading-3 text-gray-400">{event.detail}</span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Asset Library Panel ─────────────────────────────────────────

const ASSET_ROW_HEIGHT = 116;
const ASSET_COLUMNS = 2;
const ASSET_OVERSCAN_ROWS = 3;


function AssetLibraryPanel({
  projectId, onAddToCanvas, isLight, onClose,
}: {
  projectId: number; onAddToCanvas?: (item: AssetItem) => void; isLight?: boolean; onClose?: () => void;
}) {
  const [items, setItems] = useState<AssetItem[]>([]);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [assetScrollTop, setAssetScrollTop] = useState(0);

  const fetchAssets = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const params: Record<string, unknown> = {};
      if (search) params.search = search;
      if (typeFilter) params.type = typeFilter;
      const data = await api.atelierCanvas.getAssets(projectId, params);
      setItems(data.items || []);
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, [projectId, search, typeFilter]);

  useEffect(() => { fetchAssets(); }, [fetchAssets]);

  const totalAssetRows = Math.ceil(items.length / ASSET_COLUMNS);
  const startAssetRow = Math.max(0, Math.floor(assetScrollTop / ASSET_ROW_HEIGHT) - ASSET_OVERSCAN_ROWS);
  const visibleAssetRows = 8 + ASSET_OVERSCAN_ROWS * 2;
  const endAssetRow = Math.min(totalAssetRows, startAssetRow + visibleAssetRows);
  const visibleAssetItems = items.slice(startAssetRow * ASSET_COLUMNS, endAssetRow * ASSET_COLUMNS);
  const assetOffsetTop = startAssetRow * ASSET_ROW_HEIGHT;

  return (
    <div data-asset-library-overlay className="w-72 h-full bg-white flex flex-col border border-gray-200 shadow-2xl rounded-l-2xl overflow-hidden">
      {/* Header + Search */}
      <div className="p-3 space-y-2 border-b border-white/5">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-medium text-gray-400">素材库</h3>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-gray-700">{items.length} 项</span>
            {onClose && (
              <button onClick={onClose} className="text-xs text-gray-500 hover:text-gray-800" title="关闭素材库">✕</button>
            )}
          </div>
        </div>
        <input value={search} onChange={e => setSearch(e.target.value)}
          placeholder="搜索素材..." className={`w-full rounded px-2 py-1 text-xs ${isLight ? 'bg-white border border-gray-300 text-gray-700 placeholder-gray-400' : 'bg-white/5 border border-white/10 text-gray-300 placeholder-gray-600'}`} />
        <div className="flex gap-1">
          {['', 'images', 'videos', 'graphics', 'docs'].map(t => (
            <button key={t} onClick={() => setTypeFilter(t)}
              className={`px-2 py-0.5 rounded text-[10px] transition-colors
                ${typeFilter === t ? 'bg-orange-50 text-orange-600' : 'bg-gray-50 text-gray-500 hover:text-gray-700'}`}>
              {({'':'全部','images':'图片','videos':'视频','graphics':'图形','docs':'文档'} as any)[t] || t}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      <div
        className="flex-1 overflow-y-auto p-2"
        onScroll={(e) => setAssetScrollTop(e.currentTarget.scrollTop)}
      >
        {loading ? (
          <div className="text-center text-gray-700 text-xs py-8">加载中...</div>
        ) : (
          <div className="relative" style={{ height: totalAssetRows * ASSET_ROW_HEIGHT }}>
            <div
              className="grid grid-cols-2 gap-2 absolute left-0 right-0 top-0"
              style={{ transform: `translateY(${assetOffsetTop}px)` }}
            >
              {visibleAssetItems.map(item => (
                <div key={item.id}
                  onClick={() => onAddToCanvas?.(item)}
                  className={`group cursor-pointer rounded-lg overflow-hidden transition-all ${isLight ? 'bg-gray-100 hover:bg-gray-200 border border-gray-200 hover:border-cyan-500/50' : 'bg-white/5 hover:bg-white/10 border border-white/5 hover:border-cyan-500/30'}`}>
                  <div className="h-16 bg-black/30 flex items-center justify-center">
                    {item.url && item.type === 'video' ? (
                      <video src={item.url} className="w-full h-full object-cover opacity-70" muted />
                    ) : item.url ? (
                      <img loading="lazy" src={item.url} alt="" className="w-full h-full object-cover opacity-70" />
                    ) : (
                      <span className="text-sm text-gray-700">
                        {item.type === 'image' ? '🖼️' : item.type === 'video' ? '🎬' : item.type === 'graphic' ? '📊' : '📄'}
                      </span>
                    )}
                  </div>
                  <div className="p-1.5">
                    <p className="text-[10px] text-gray-400 truncate">{item.label}</p>
                    {item.text_preview && (
                      <p className="text-[9px] text-gray-700 truncate mt-0.5">{item.text_preview.slice(0, 40)}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function LovartCanvasTopBar({
  scale, elementCount, saveStatus, onZoomIn, onZoomOut, onReset, onToggleCompare, compareMode, onOpenFont,
}: {
  scale: number; elementCount: number; saveStatus: string; compareMode: boolean;
  onZoomIn: () => void; onZoomOut: () => void; onReset: () => void; onToggleCompare: () => void; onOpenFont: () => void;
}) {
  return (
    <div
      data-lovart-canvas-topbar
      className="h-12 shrink-0 border-b px-3 flex items-center justify-between"
      style={{ background: 'var(--lo-bg-float)', borderColor: 'var(--lo-border-neutral-l1)', color: 'var(--lo-text-default)' }}
    >
      <div className="flex items-center gap-2 min-w-0">
        <div className="h-6 w-6 rounded-lg bg-blue-500" aria-label="canvas logo" />
        <span className="text-sm font-medium truncate">MOYAG Canvas</span>
        <span className="text-[11px]" style={{ color: 'var(--lo-text-tertiary)' }}>{elementCount} elements</span>
      </div>
      <div className="flex items-center gap-1">
        <button onClick={onZoomOut} className="h-8 w-8 rounded-lg text-sm hover:bg-black/[0.06]" title="缩小">-</button>
        <button onClick={onReset} className="h-8 min-w-[50px] rounded-lg px-2 text-xs tabular-nums hover:bg-black/[0.06]" title="重置缩放">{Math.round(scale * 100)}%</button>
        <button onClick={onZoomIn} className="h-8 w-8 rounded-lg text-sm hover:bg-black/[0.06]" title="放大">+</button>
        <div className="mx-1 h-4 w-px bg-black/[0.07]" />
        <button onClick={onToggleCompare} className={`h-8 rounded-lg px-2 text-xs hover:bg-black/[0.06] ${compareMode ? 'text-blue-500' : ''}`}>比较</button>
        <button onClick={onOpenFont} className="h-8 rounded-lg px-2 text-xs hover:bg-black/[0.06]">字体</button>
      </div>
      <div className="text-[11px]" style={{ color: 'var(--lo-text-tertiary)' }}>{saveStatus === 'saving' ? '保存中...' : saveStatus === 'error' ? '保存失败' : '已保存'}</div>
    </div>
  );
}

function LovartCanvasToolbar() {
  return null;
}

// ── Main CanvasView ─────────────────────────────────────────────

export default function CanvasView({
  mainImage, whiteBg, sceneImages, sellingPoints, videoScripts, adMaterial, brief, projectId, isLight, generationTaskId, qualityReport, onAddToChat, onEditPrompt,
}: CanvasViewProps) {
  // Canvas state
  const [elements, setElements] = useState<CanvasElement[]>([]);
  const [connections, setConnections] = useState<CanvasConnection[]>([]);
  const [viewport, setViewport] = useState<ViewportState>({ x: 0, y: 0, scale: 1 });
  const [selectedEl, setSelectedEl] = useState<CanvasElement | null>(null);

  // Interaction state
  const [dragging, setDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [draggingElId, setDraggingElId] = useState<string | null>(null);
  const [dragElOffset, setDragElOffset] = useState({ x: 0, y: 0 });
  const [contextMenu, setContextMenu] = useState<{elId:string;x:number;y:number}|null>(null);
  const [saveStatus, setSaveStatus] = useState<'saved'|'saving'|'error'>('saved');
  const containerRef = useRef<HTMLDivElement>(null);

  // Timeline state
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);

  // Detail panel state
  const [modifyInput, setModifyInput] = useState('');
  const [modifying, setModifying] = useState(false);
  const [imageActionRunning, setImageActionRunning] = useState<string | null>(null);
  const [imageActionError, setImageActionError] = useState<string | null>(null);

  const pid = projectId || 2;

  const getVersionRootId = (el: CanvasElement) => String(el.metadata?.parent_asset_id || el.asset_ref?.parent_asset_id || el.id);
  const getVersionNumber = (el: CanvasElement) => Number(el.metadata?.version || el.asset_ref?.version || 1);
  const getVersionChain = (el: CanvasElement) => {
    const rootId = getVersionRootId(el);
    return elements
      .filter(item => item.id === rootId || item.metadata?.parent_asset_id === rootId || item.asset_ref?.parent_asset_id === rootId)
      .sort((a, b) => getVersionNumber(a) - getVersionNumber(b));
  };
  const getPreviousVersion = (el: CanvasElement) => {
    const chain = getVersionChain(el);
    const currentIndex = chain.findIndex(item => item.id === el.id);
    return currentIndex > 0 ? chain[currentIndex - 1] : null;
  };
  const getCanvasElementImageUrl = (el: CanvasElement) => el.thumbnail_url || el.asset_ref?.url || el.metadata?.url;

  // Quality check states
  const [qualityScores, setQualityScores] = useState<Record<string, number>>({});
  const [compareMode, setCompareMode] = useState(false);
  const [compareA, setCompareA] = useState<string | null>(null);
  const [compareB, setCompareB] = useState<string | null>(null);
  const [compareResult, setCompareResult] = useState<any>(null);
  const [, setCompareLoading] = useState(false);  // P0-1: legacy toolbar removed, keep setter for compare flow

  // Font generator panel state
  const [fontPanelOpen, setFontPanelOpen] = useState(false);
  const [assetLibraryOpen, setAssetLibraryOpen] = useState(false);

  // ── Load quality scores ──────────────────────────────────────
  const loadQualityScores = useCallback(async (els: CanvasElement[]) => {
    const paths = els.map(e => e.thumbnail_url).filter(Boolean) as string[];
    if (!paths.length) return;
    try {
      const resp = await fetch('/api/v1/aesthetic/rank', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_paths: paths.map(p => p.startsWith('/static/') ? `/opt/visual-agent${p}` : p),
          brief: brief || {},
        }),
      });
      const data = await resp.json();
      const scores: Record<string, number> = {};
      data.rankings?.forEach((r: any) => {
        const filename = r.path?.split('/').pop() || '';
        // Map back to thumbnail_url
        for (const el of els) {
          if (el.thumbnail_url?.includes(filename)) {
            scores[el.id] = r.score;
          }
        }
      });
      setQualityScores(scores);
    } catch {}
  }, [brief]);

  // ── Load canvas state from API on mount ──────────────────────
  useEffect(() => {
    api.atelierCanvas.getState(pid).then(data => {
      if (data?.elements?.length) {
        setElements(data.elements);
        setConnections(data.connections || []);
        setViewport(data.viewport || { x: 0, y: 0, scale: 1 });
      } else {
        // No saved state — build from props
        const els = buildDefaultElements({ mainImage, whiteBg, sceneImages, sellingPoints, videoScripts, adMaterial });
        setElements(els);
        setConnections(buildDefaultConnections(els));
      }
    }).catch(() => {
      // Fallback: build from props
      const els = buildDefaultElements({ mainImage, whiteBg, sceneImages, sellingPoints, videoScripts, adMaterial });
      setElements(els);
      setConnections(buildDefaultConnections(els));
    });
  }, [pid, mainImage, whiteBg, sceneImages, sellingPoints, videoScripts, adMaterial]);

  // ── Load timeline ────────────────────────────────────────────
  useEffect(() => {
    api.atelierCanvas.getTimeline(pid).then(data => {
      setTimeline(data?.entries || []);
    }).catch(() => {});
  }, [pid]);

  // ── Update props → elements when props change ────────────────
  useEffect(() => {
    const generated = buildDefaultElements({ mainImage, whiteBg, sceneImages, sellingPoints, videoScripts, adMaterial });
    if (!generated.length) return;
    setElements(prev => {
      const next = prev.length ? mergeGeneratedElements(prev, generated) : generated;
      if (next !== prev) {
        const nextConnections = prev.length ? connections : buildDefaultConnections(next);
        setConnections(nextConnections);
        persistCanvas(next, nextConnections, viewport);
      }
      return next;
    });
  }, [mainImage, whiteBg, sceneImages, sellingPoints, videoScripts, adMaterial]);

  // ── Load quality scores when elements change ─────────────────
  useEffect(() => {
    if (elements.length > 0) loadQualityScores(elements);
  }, [elements.length]);

  // ── Save canvas state on change ──────────────────────────────
  const persistCanvas = useCallback((els: CanvasElement[], conns: CanvasConnection[], vp: ViewportState) => {
    setSaveStatus('saving');
    api.atelierCanvas.saveState(pid, {
      elements: els.map(e => ({
        id: e.id, type: e.type, label: e.label,
        x: e.x, y: e.y, width: e.width, height: e.height,
        thumbnail_url: e.thumbnail_url, asset_ref: e.asset_ref, metadata: e.metadata,
      })),
      connections: conns,
      viewport: vp,
    }).then(() => {
      setSaveStatus('saved');
    }).catch(() => {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('saved'), 3000);
    });
  }, [pid]);

  // ── Pan & Zoom ───────────────────────────────────────────────
  const handleMouseDown = (e: React.MouseEvent) => {
    // Element drag: check if clicking on a draggable element
    const elWrapper = (e.target as HTMLElement).closest('[data-element-id]');
    if (elWrapper) {
      const elId = elWrapper.getAttribute('data-element-id');
      if (elId) {
        const el = elements.find(elm => elm.id === elId);
        if (el) {
          setDraggingElId(elId);
          const scale = viewport.scale;
          setDragElOffset({
            x: (e.clientX - viewport.x) / scale - el.x,
            y: (e.clientY - viewport.y) / scale - el.y,
          });
          e.stopPropagation();
          return;
        }
      }
    }
    // Canvas pan (skip if clicking interactive controls)
    if ((e.target as HTMLElement).closest('[data-element]')) return;
    setDragging(true);
    setDragStart({ x: e.clientX - viewport.x, y: e.clientY - viewport.y });
  };
  const handleMouseMove = (e: React.MouseEvent) => {
    if (draggingElId) {
      // Element drag: update element position in canvas space
      const scale = viewport.scale;
      const newX = (e.clientX - viewport.x) / scale - dragElOffset.x;
      const newY = (e.clientY - viewport.y) / scale - dragElOffset.y;
      setElements(prev => {
        const next = prev.map(el =>
          el.id === draggingElId ? { ...el, x: newX, y: newY } : el
        );
        // Debounced save
        if ((window as any)._canvasSaveTimer) clearTimeout((window as any)._canvasSaveTimer);
        (window as any)._canvasSaveTimer = setTimeout(() => persistCanvas(next, connections, viewport), 500);
        return next;
      });
      return;
    }
    if (!dragging) return;
    const newVp = { ...viewport, x: e.clientX - dragStart.x, y: e.clientY - dragStart.y };
    setViewport(newVp);
  };
  const handleMouseUp = () => {
    if (draggingElId) {
      setDraggingElId(null);
      return;  // element positions are persisted from the latest setElements(prev => next) snapshot
    }
    if (dragging) {
      setDragging(false);
      persistCanvas(elements, connections, viewport);
    }
  };
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const newVp = { ...viewport, scale: Math.max(0.15, Math.min(3, viewport.scale - e.deltaY * 0.001)) };
    setViewport(newVp);
  }, [viewport]);

  const zoomIn = () => setViewport(p => ({ ...p, scale: Math.min(3, p.scale + 0.2) }));
  const zoomOut = () => setViewport(p => ({ ...p, scale: Math.max(0.15, p.scale - 0.2) }));
  const resetView = () => setViewport({ x: 0, y: 0, scale: 1 });

  // ── Modify handler ───────────────────────────────────────────
  const handleModify = async () => {
    if (!modifyInput.trim() || !selectedEl || !brief) return;
    setModifying(true);
    try {
      const resp = await fetch('/api/v1/asset/modify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asset_type: selectedEl.type,
          asset_id: selectedEl.id,
          project_id: pid,
          original: selectedEl.metadata || {},
          instruction: modifyInput,
          brief,
          provider: 'dataeyes',
        }),
      });
      const data = await resp.json();
      if (data.modified && !data.error) {
        if (data.canvas_element) {
          const nextElements = [...elements, data.canvas_element];
          setElements(nextElements);
          setSelectedEl(data.canvas_element)
          persistCanvas(nextElements, connections, viewport);
        } else {
          const nextElements = elements.map(el => el.id === selectedEl.id ? { ...el, metadata: data.modified, thumbnail_url: data.modified.url || el.thumbnail_url } : el);
          setElements(nextElements);
          persistCanvas(nextElements, connections, viewport);
        }
        setModifyInput('');
      }
    } catch { /* keep original */ }
    finally { setModifying(false); }
  };


  const runCanvasImageAction = async (action: 'cutout', el: CanvasElement) => {
    const imageUrl = getCanvasElementImageUrl(el);
    if (imageActionRunning) return;
    if (!imageUrl) {
      setImageActionError('当前图片缺少可处理的图片地址');
      setTimeout(() => setImageActionError(null), 3000);
      return;
    }
    setImageActionError(null);
    setImageActionRunning(action);
    try {
      const data = await api.canvasImageActions.run({
        project_id: pid,
        asset_id: el.id,
        action,
        image_url: imageUrl,
        provider: 'dataeyes',
      });
      const returnedElements = data.canvas_elements || (data.canvas_element ? [data.canvas_element] : []);
      if (returnedElements.length) {
        const nextElements = [...elements, ...returnedElements];
        setElements(nextElements);
        setSelectedEl(returnedElements[0]);
        persistCanvas(nextElements, connections, viewport);
      }
    } catch {
      setImageActionError('图片处理启动失败，请稍后重试');
      setTimeout(() => setImageActionError(null), 3000);
    } finally {
      setImageActionRunning(null);
    }
  };

  // ── Run comparison when both A and B selected ────────────────
  useEffect(() => {
    if (!compareA || !compareB) return;
    setCompareLoading(true);
    const elA = elements.find(e => e.id === compareA);
    const elB = elements.find(e => e.id === compareB);
    const pathA = elA?.thumbnail_url?.startsWith('/static/') ? `/opt/visual-agent${elA.thumbnail_url}` : elA?.thumbnail_url;
    const pathB = elB?.thumbnail_url?.startsWith('/static/') ? `/opt/visual-agent${elB.thumbnail_url}` : elB?.thumbnail_url;
    if (!pathA || !pathB) { setCompareLoading(false); return; }
    fetch('/api/v1/aesthetic/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_a: pathA, image_b: pathB, brief: brief || {} }),
    }).then(r => r.json()).then(data => {
      setCompareResult(data);
      setCompareLoading(false);
    }).catch(() => setCompareLoading(false));
  }, [compareA, compareB]);

  // ── Add asset to canvas ──────────────────────────────────────
  const addToCanvas = (item: AssetItem) => {
    const newEl: CanvasElement = {
      id: `asset_${Date.now()}`,
      type: item.type === 'image' ? 'key_visual' : item.type,
      label: item.label,
      x: 100 + elements.length * 50,
      y: 100 + elements.length * 30,
      width: 280, height: 320,
      thumbnail_url: item.url,
      metadata: { added_from_library: true },
    };
    const newElements = [...elements, newEl];
    setElements(newElements);
    persistCanvas(newElements, connections, viewport);
  };

  const deleteElement = (elId: string) => {
    setElements(prev => prev.filter(el => el.id !== elId));
    setConnections(prev => prev.filter(c => c.source_id !== elId && c.target_id !== elId));
    if (selectedEl?.id === elId) setSelectedEl(null);
  };

  // ── Handle font generated ────────────────────────────────────
  const handleFontGenerated = (fontData: any) => {
    const newEl: CanvasElement = {
      id: `font_${Date.now()}`,
      type: 'font_generation',
      label: fontData.font_name || '生成字体',
      x: 100 + elements.length * 50,
      y: 100 + elements.length * 30,
      width: 280, height: 320,
      thumbnail_url: fontData.sample_url,
      metadata: {
        font_id: fontData.font_id,
        style_description: fontData.style_description,
        generated_at: new Date().toISOString(),
      },
    };
    const newElements = [...elements, newEl];
    setElements(newElements);
    persistCanvas(newElements, connections, viewport);
  };

  const handleMenuAction = (action: string, elId: string) => {
    const el = elements.find(e => e.id === elId);
    if (!el) return;
    switch (action) {
      case 'cutout': runCanvasImageAction('cutout', el); break;
      case 'add_chat': onAddToChat?.({ id: el.id, label: el.label, image_url: getCanvasElementImageUrl(el), type: el.type, metadata: el.metadata }); break;
      case 'delete': deleteElement(elId); break;
      case 'copy': navigator.clipboard.writeText(el.label || ''); break;
      case 'front': setElements(prev => { const idx = prev.findIndex(e => e.id === elId); if (idx<0) return prev; return [...prev.filter((_,i)=>i!==idx), prev[idx]]; }); break;
      case 'back': setElements(prev => { const idx = prev.findIndex(e => e.id === elId); if (idx<0) return prev; return [prev[idx], ...prev.filter((_,i)=>i!==idx)]; }); break;
      case 'download': if (el.thumbnail_url) { const a = document.createElement('a'); a.href = el.thumbnail_url; a.download = el.label || 'download'; a.click(); } break;
      case 'generate_font': setFontPanelOpen(true); break;
      default: break;
    }
  };

  return (
    <div data-lovart-canvas-shell className="flex flex-col h-full" style={{ background: 'var(--lo-bg-canvas)' }}>
      <LovartCanvasTopBar
        scale={viewport.scale}
        elementCount={elements.length}
        saveStatus={saveStatus}
        compareMode={compareMode}
        onZoomIn={zoomIn}
        onZoomOut={zoomOut}
        onReset={resetView}
        onToggleCompare={() => { setCompareMode(!compareMode); setCompareA(null); setCompareB(null); setCompareResult(null); }}
        onOpenFont={() => setFontPanelOpen(true)}
      />
      {/* Main area: canvas + asset panel */}
      <div className="flex flex-1 overflow-hidden">
        {/* Canvas */}
        <div className="flex-1 relative overflow-hidden"
          ref={containerRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
          style={{ cursor: draggingElId ? 'grabbing' : dragging ? 'grabbing' : 'grab' }}>

          <button
            data-asset-library-trigger
            onClick={() => setAssetLibraryOpen(true)}
            className="absolute right-4 top-4 z-50 rounded-xl border border-gray-200 bg-white/90 px-3 py-2 text-xs text-gray-700 shadow-lg backdrop-blur hover:bg-white"
            title="打开素材库"
          >
            📁 素材库
          </button>

          {assetLibraryOpen && (
            <div className="absolute right-0 top-0 bottom-0 z-50">
              <button
                onClick={() => setAssetLibraryOpen(false)}
                className="absolute -left-10 top-4 z-10 h-8 w-8 rounded-lg border border-gray-200 bg-white/90 text-xs text-gray-600 shadow-lg hover:bg-white"
                title="关闭素材库"
              >
                ✕
              </button>
              <AssetLibraryPanel
                projectId={pid}
                onAddToCanvas={(item) => { addToCanvas(item); setAssetLibraryOpen(false); }}
                isLight={isLight}
                onClose={() => setAssetLibraryOpen(false)}
              />
            </div>
          )}

          {/* Legacy toolbar hidden after Lovart topbar migration */}
          

          <LovartCanvasToolbar />

          {/* Infinite canvas layer */}
          <div className="absolute inset-0"
            style={{
              transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.scale})`,
              transformOrigin: '0 0',
            }}>
            {/* Connection lines */}
            <ConnectionLines
              elements={elements}
              connections={connections}
              viewport={viewport}
              onLabelChange={(connectionId, label) => {
                const nextConnections = connections.map(conn => conn.id === connectionId ? { ...conn, label } : conn);
                setConnections(nextConnections);
                persistCanvas(elements, nextConnections, viewport);
              }}
            />

            {/* Elements */}
            {elements.map(el => (
              <div key={el.id} data-element="true" data-element-id={el.id} onContextMenu={(e) => { e.preventDefault(); e.stopPropagation(); setContextMenu({elId:el.id, x:e.clientX, y:e.clientY}); }}>
                <ElementCard
                  el={el}
                  isSelected={selectedEl?.id === el.id}
                  onClick={() => {
                    if (compareMode) {
                      if (!compareA) { setCompareA(el.id); }
                      else if (!compareB && el.id !== compareA) { setCompareB(el.id); }
                      else { setCompareA(null); setCompareB(null); }
                    } else {
                      setSelectedEl(selectedEl?.id === el.id ? null : el);
                    }
                  }}
                  scale={viewport.scale}
                  onDelete={() => deleteElement(el.id)}
                  qualityScore={qualityScores[el.id]}
                  isCompareA={compareA === el.id}
                  isCompareB={compareB === el.id}
                />
              </div>
            ))}

            {/* Empty state hint */}
            {elements.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="text-center space-y-4 max-w-sm">
                  <span className="text-6xl">🎨</span>
                  <h3 className="text-lg font-semibold text-gray-400">空白画布</h3>
                  <p className="text-sm text-gray-400 leading-relaxed">从右侧素材库拖入素材，或点击「生成」创建新的视觉内容</p>
                  <div className="flex items-center justify-center gap-2 text-xs text-gray-500 mt-2">
                    <span className="px-3 py-1.5 rounded-lg bg-gray-100">📁 拖入素材</span>
                    <span className="text-gray-300">或</span>
                    <span className="px-3 py-1.5 rounded-lg bg-orange-50 text-orange-600">✨ 生成新内容</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Asset library is now a canvas overlay, opened by data-asset-library-trigger. */}
      </div>

      {/* Detail panel (overlay, shown when element selected) */}
      {selectedEl && (
        <div className="absolute right-80 top-20 w-72 max-h-[60vh] bg-white shadow-xl border border-gray-200 rounded-2xl p-4 overflow-y-auto z-50 shadow-2xl"
          style={{ right: '20rem' }}>
          <div className="flex items-center justify-between mb-3">
            <h3 className={`text-sm font-medium ${isLight ? 'text-gray-800' : 'text-gray-300'}`}>{selectedEl.label}</h3>
            <button onClick={() => setSelectedEl(null)}
              className="text-gray-600 hover:text-gray-300 text-lg">✕</button>
          </div>
          <div className="space-y-2">
            {Object.entries(selectedEl.metadata || {}).filter(([k]) => !k.startsWith('_')).slice(0, 10).map(([k, v]) => (
              <div key={k}>
                <span className={`text-[10px] ${isLight ? 'text-gray-500' : 'text-gray-600'}`}>{k}: </span>
                <span className="text-[11px] text-gray-400">
                  {typeof v === 'object' ? JSON.stringify(v).slice(0, 100) : String(v).slice(0, 200)}
                </span>
              </div>
            ))}
          </div>
          {getVersionChain(selectedEl).length > 1 && (
            <div data-version-chain className="mt-4 pt-3 border-t border-gray-100">
              <div className="flex items-center justify-between mb-2">
                <p className="text-[10px] text-gray-600">版本链</p>
                <span className="text-[10px] text-gray-500">v{getVersionNumber(selectedEl)} / {getVersionChain(selectedEl).length}</span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => { const parent = getPreviousVersion(selectedEl); if (parent) setSelectedEl(parent); }}
                  disabled={!getPreviousVersion(selectedEl)}
                  className="flex-1 px-2 py-1 rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-40 text-[10px] text-gray-700">
                  查看上一版
                </button>
                <button
                  onClick={() => { const parent = getPreviousVersion(selectedEl); if (parent) { setCompareA(parent.id); setCompareB(selectedEl.id); setCompareMode(true); } }}
                  disabled={!getPreviousVersion(selectedEl)}
                  className="flex-1 px-2 py-1 rounded bg-blue-50 hover:bg-blue-100 disabled:opacity-40 text-[10px] text-blue-600">
                  对比上一版
                </button>
              </div>
            </div>
          )}
          {/* NL Modify */}
          {brief && (
            <div className="mt-4 pt-3 border-t border-white/5">
              <p className="text-[10px] text-gray-600 mb-2">自然语言修改</p>
              <div className="flex gap-2">
                <input value={modifyInput} onChange={e => setModifyInput(e.target.value)}
                  placeholder="例如：背景换成城市夜景..."
                  className="flex-1 bg-white/5 border border-white/10 rounded px-2 py-1 text-xs text-gray-200"
                  onKeyDown={e => { if (e.key === 'Enter') handleModify(); }} />
                <button onClick={handleModify} disabled={modifying || !modifyInput.trim()}
                  className="px-3 py-1 bg-cyan-500/20 hover:bg-cyan-500/30 disabled:opacity-30 text-cyan-400 rounded text-xs">
                  {modifying ? '...' : '修改'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Compare result panel */}
      {compareResult && (
        <div className={`absolute bottom-12 left-4 right-80 backdrop-blur-xl rounded-xl p-4 z-50 max-h-[45vh] overflow-y-auto ${isLight ? 'bg-white/95 border border-gray-200 shadow-xl' : 'bg-black/90 border border-cyan-500/20'}`}>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-cyan-400">比较结果</h3>
            <button onClick={() => setCompareResult(null)} className="text-gray-600 hover:text-gray-300">✕</button>
          </div>
          <div className="flex gap-3 mb-3">
            <div className={`flex-1 p-2 rounded-lg text-center ${compareResult.winner === 'A' ? 'bg-cyan-500/15 border border-cyan-500/40' : 'bg-white/5 border border-white/5'}`}>
              <p className="text-[10px] text-gray-500">图片 A</p>
              <p className="text-lg font-bold text-cyan-400">{compareResult.scores?.A?.toFixed(1)}</p>
              {compareResult.winner === 'A' && <span className="text-[10px] text-cyan-400">✓ 优胜</span>}
            </div>
            <div className="flex items-center text-gray-700 text-xs font-bold">VS</div>
            <div className={`flex-1 p-2 rounded-lg text-center ${compareResult.winner === 'B' ? 'bg-cyan-500/15 border border-cyan-500/40' : 'bg-white/5 border border-white/5'}`}>
              <p className="text-[10px] text-gray-500">图片 B</p>
              <p className="text-lg font-bold text-cyan-400">{compareResult.scores?.B?.toFixed(1)}</p>
              {compareResult.winner === 'B' && <span className="text-[10px] text-cyan-400">✓ 优胜</span>}
            </div>
          </div>
          {compareResult.verdict && (
            <p className={`text-[11px] mb-3 leading-relaxed ${isLight ? 'text-gray-700' : 'text-gray-300'}`}>{compareResult.verdict}</p>
          )}
          {compareResult.dimensions?.length > 0 && (
            <div className="space-y-2 mb-3">
              <p className="text-[10px] text-gray-600">维度分析</p>
              {compareResult.dimensions.map((dim: any, i: number) => (
                <div key={i} className="flex items-center gap-2 text-[10px]">
                  <span className="w-16 text-gray-500 flex-shrink-0">{dim.name}</span>
                  <span className={`w-8 text-right font-mono ${dim.score_a >= dim.score_b ? 'text-cyan-400' : 'text-gray-600'}`}>{dim.score_a}</span>
                  <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-cyan-500/50 rounded-full" style={{width: `${Math.max(3, dim.score_a)}%`}} />
                  </div>
                  <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div className="h-full bg-purple-500/50 rounded-full" style={{width: `${Math.max(3, dim.score_b)}%`}} />
                  </div>
                  <span className={`w-8 text-right font-mono ${dim.score_b >= dim.score_a ? 'text-purple-400' : 'text-gray-600'}`}>{dim.score_b}</span>
                </div>
              ))}
            </div>
          )}
          {compareResult.suggestion && (
            <p className="text-[10px] text-yellow-500/80 border-t border-white/5 pt-2">💡 {compareResult.suggestion}</p>
          )}
        </div>
      )}

      {imageActionRunning && (
        <div data-canvas-image-action-running="true" className="absolute left-1/2 top-4 z-[9998] -translate-x-1/2 rounded-full border border-orange-200 bg-white/95 px-4 py-2 text-xs text-orange-600 shadow-lg">
          抠图处理中...
        </div>
      )}
      {imageActionError && (
        <div data-canvas-image-action-error="true" className="absolute left-1/2 top-14 z-[9998] -translate-x-1/2 rounded-full border border-red-200 bg-white/95 px-4 py-2 text-xs text-red-500 shadow-lg">
          {imageActionError}
        </div>
      )}

      {/* Context Menu */}
      {contextMenu && (
        <ContextMenu x={contextMenu.x} y={contextMenu.y} elId={contextMenu.elId}
          onClose={() => setContextMenu(null)}
          onAction={handleMenuAction} />
      )}

      {/* Font Generator Panel */}
      <FontGeneratorPanel
        projectId={pid}
        isOpen={fontPanelOpen}
        onClose={() => setFontPanelOpen(false)}
        onFontGenerated={handleFontGenerated}
        isLight={isLight}
      />

      {/* Bottom Timeline */}
      {qualityReport && !generationTaskId && (
        <div className="absolute bottom-4 right-4 w-72 z-50">
          <ScoreCard report={qualityReport} isLight={isLight} />
        </div>
      )}
      <TimelineBar projectId={projectId} generationTaskId={generationTaskId} onEditPrompt={onEditPrompt} refreshTrigger={timeline.length} onRestore={(r) => { /* 点击恢复: navigate to result */ const url = `/generate/${projectId}`; window.history.pushState({ result: null, restoredFrom: r.id }, '', url); window.location.href = url; }} />
    </div>
  );
}
