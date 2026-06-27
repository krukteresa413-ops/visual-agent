import { useEffect, useState } from 'react';
import { api } from '../api/client';

// 与后端 AGENT_SEQUENCE 的具名步骤一一对应(SSE step 标签即这些名字)
const AGENTS: { name: string; sub: string; icon: string }[] = [
  { name: 'PM', sub: '拆解任务', icon: '🧠' },
  { name: 'Research', sub: '行业洞察', icon: '🔍' },
  { name: 'Brand', sub: '品牌策略', icon: '🎨' },
  { name: 'Copy', sub: '中文文案', icon: '✍️' },
  { name: 'Visual', sub: '视觉方向', icon: '🖼️' },
  { name: 'Image', sub: '渲染主视觉', icon: '⚡' },
  { name: 'Layout', sub: '排版布局', icon: '🧩' },
  { name: 'Mockup', sub: '场景套用', icon: '📦' },
  { name: 'Compliance', sub: '合规检查', icon: '🛡️' },
  { name: 'Export', sub: '整理交付', icon: '⬇️' },
];

/** 真·多 Agent 状态流:订阅 /progress/{taskId}/stream,按真实 SSE step 点亮对应 Agent;断连自动重试。 */
export default function AgentProgress({ taskId }: { taskId?: string | null }) {
  const [statusMap, setStatusMap] = useState<Record<string, string>>({});
  const [finished, setFinished] = useState(false);

  useEffect(() => {
    if (!taskId) return;
    setStatusMap({});
    setFinished(false);
    let closed = false;
    let attempts = 0;
    let src: EventSource | null = null;

    const onProgress = (e: MessageEvent) => {
      try {
        const d = JSON.parse(e.data);
        if (d.step) setStatusMap((m) => ({ ...m, [d.step]: d.status || 'running' }));
      } catch { /* ignore */ }
    };

    const connect = () => {
      if (closed) return;
      src = new EventSource(api.progress.streamUrl(taskId));
      src.addEventListener('progress', onProgress);
      src.addEventListener('done', () => { setFinished(true); closed = true; src?.close(); });
      src.addEventListener('error', () => {
        src?.close();
        // 任务可能尚未建立/瞬断 → 退避重连(覆盖竞态窗口)
        if (!closed && attempts < 8) { attempts += 1; setTimeout(connect, 1500); }
      });
    };
    connect();

    return () => { closed = true; src?.close(); };
  }, [taskId]);

  if (!taskId) return null;

  const isDone = (s?: string) => s === 'done' || s === 'success';
  const doneCount = AGENTS.filter((a) => isDone(statusMap[a.name])).length;
  const percent = finished ? 100 : Math.round((doneCount / AGENTS.length) * 100);

  return (
    <div className="mx-auto w-full max-w-lg">
      <div className="liquid-card space-y-3 p-4">
        <div className="flex items-center gap-2">
          <span className="size-2.5 animate-ping rounded-full bg-orange-400" />
          <span className="text-sm font-medium text-gray-100">多 Agent 协作中</span>
          <span className="ml-auto text-xs tabular-nums text-orange-300">{finished ? '已完成' : `${percent}%`}</span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/[0.08]">
          <div className="h-full rounded-full bg-gradient-to-r from-orange-500 to-rose-500 transition-all duration-500" style={{ width: `${percent}%` }} />
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {AGENTS.map((a) => {
            const st = statusMap[a.name];
            const done = isDone(st);
            const running = st === 'running';
            const failed = st === 'failed';
            const skipped = st === 'skipped';
            const cls = running
              ? 'border-orange-400/40 bg-orange-500/[0.08]'
              : done
                ? 'border-emerald-400/20 bg-emerald-500/[0.06]'
                : failed
                  ? 'border-rose-400/30 bg-rose-500/[0.06]'
                  : 'border-white/[0.06] opacity-50';
            return (
              <div key={a.name} className={'flex items-center gap-2 rounded-lg border px-2 py-1.5 transition-all duration-300 ' + cls}>
                <span className="text-sm">{done ? '✓' : failed ? '✕' : a.icon}</span>
                <span className="min-w-0 flex-1">
                  <span className="block text-[11px] font-medium text-gray-200">{a.name}</span>
                  <span className="block truncate text-[9px] text-gray-500">{failed ? '降级/超时' : skipped ? '跳过' : a.sub}</span>
                </span>
                {running && <span className="size-1.5 animate-pulse rounded-full bg-orange-400" />}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
