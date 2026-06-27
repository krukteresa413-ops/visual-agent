import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';

interface DistItem { name: string; count: number; color: string }
interface Overview {
  design_projects: number; completed_projects: number; completion_rate: number;
  video_projects: number; avg_video_score: number; total_assets: number;
  brand_count: number; template_count: number;
  heatmap: Array<{ label: string; date: number; count: number }>;
  type_distribution: DistItem[];
  score_distribution: Array<{ range: string; count: number }>;
  recent_projects: Array<{ id: number; name: string; type: string; assets: number; status: string; completed: boolean; date: string }>;
  user_name: string;
}

const EMPTY: Overview = {
  design_projects: 0, completed_projects: 0, completion_rate: 0, video_projects: 0,
  avg_video_score: 0, total_assets: 0, brand_count: 0, template_count: 12,
  heatmap: [], type_distribution: [], score_distribution: [], recent_projects: [], user_name: 'MOYAG',
};

const fetchOverview = () => api.get('/dashboard/overview').then((r: { data: Overview }) => r.data);

export default function DashboardPage() {
  const navigate = useNavigate();
  const { data } = useQuery({ queryKey: ['dashboard-overview'], queryFn: fetchOverview, refetchInterval: 60000 });
  const d = data || EMPTY;

  const todayCount = d.heatmap.length ? d.heatmap[d.heatmap.length - 1].count : 0;
  const maxHeat = Math.max(...d.heatmap.map((h) => h.count), 1);
  const maxType = Math.max(...d.type_distribution.map((t) => t.count), 1);
  const maxScore = Math.max(...d.score_distribution.map((s) => s.count), 1);
  const inProgress = Math.max(d.design_projects - d.completed_projects, 0);

  return (
    <div className="liquid-page min-h-screen px-6 py-7 text-white">
      <div className="mx-auto w-full max-w-6xl space-y-4">
        {/* 标题 */}
        <div className="flex items-end justify-between">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight"><span className="text-orange-300">📊</span> 数据看板</h1>
            <p className="mt-1 text-sm text-gray-400">项目统计、活动热力图、爆款分分布与最近项目</p>
          </div>
          <span className="rounded-full border border-white/[0.12] bg-white/[0.05] px-3 py-1 text-xs text-gray-300">📅 今日 {todayCount} 项活动</span>
        </div>

        {/* 4 指标卡 */}
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Metric label="设计项目" value={d.design_projects} sub={`已完成 ${d.completed_projects}`} icon="🗂" accent="from-orange-500 to-rose-500" onClick={() => navigate('/projects')} />
          <Metric label="视频项目" value={d.video_projects} sub={`平均爆款分 ${d.avg_video_score}`} icon="🎬" accent="from-fuchsia-500 to-purple-500" onClick={() => navigate('/video-edit')} />
          <Metric label="生成资产" value={d.total_assets} sub="张 / 个" icon="🖼" accent="from-amber-500 to-orange-500" />
          <Metric label="品牌数量" value={d.brand_count} sub={`${d.template_count} 模板可用`} icon="🎨" accent="from-emerald-500 to-teal-500" onClick={() => navigate('/brands')} />
        </div>

        {/* 完成率 */}
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <span className="flex items-center gap-2 font-semibold"><span className="text-emerald-400">✓</span> 项目完成率</span>
            <span className="text-lg font-bold">{d.completion_rate}%</span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/[0.08]">
            <div className="h-full rounded-full bg-gradient-to-r from-orange-500 to-rose-500 transition-all duration-700" style={{ width: `${d.completion_rate}%` }} />
          </div>
          <div className="mt-2 flex justify-between text-[11px] text-gray-500">
            <span>{d.completed_projects} 已完成</span>
            <span>{inProgress} 进行中</span>
          </div>
        </Card>

        {/* 热力图 + 类型分布 */}
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <div className="mb-3 flex items-center justify-between">
              <span className="flex items-center gap-2 text-sm font-semibold"><span className="text-orange-300">📅</span> 近 7 天活动热力图</span>
              <span className="flex items-center gap-1 text-[10px] text-gray-500">少 <i className="inline-block size-2 rounded-sm bg-orange-500/20" /><i className="inline-block size-2 rounded-sm bg-orange-500/50" /><i className="inline-block size-2 rounded-sm bg-orange-500/80" /> 多</span>
            </div>
            <div className="grid grid-cols-7 gap-2">
              {d.heatmap.map((h, i) => {
                const intensity = h.count === 0 ? 0 : 0.18 + (h.count / maxHeat) * 0.72;
                return (
                  <div key={i} className="flex flex-col items-center gap-1">
                    <div className="grid aspect-square w-full place-items-center rounded-lg text-xs font-semibold text-white" style={{ background: h.count ? `rgba(244,63,94,${intensity})` : 'rgba(255,255,255,0.04)' }}>
                      {h.count || ''}
                    </div>
                    <span className="text-[10px] text-gray-500">{h.label}</span>
                    <span className="text-[9px] text-gray-600">{h.date}</span>
                  </div>
                );
              })}
            </div>
          </Card>

          <Card>
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold"><span className="text-fuchsia-400">▤</span> 项目类型分布</div>
            {d.type_distribution.length === 0 ? (
              <Empty text="暂无类型数据" />
            ) : (
              <div className="space-y-2.5">
                {d.type_distribution.map((t) => (
                  <div key={t.name}>
                    <div className="mb-1 flex items-center justify-between text-xs">
                      <span className="truncate text-gray-300">{t.name}</span>
                      <span className="text-gray-500">{t.count}</span>
                    </div>
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/[0.06]">
                      <div className="h-full rounded-full" style={{ width: `${(t.count / maxType) * 100}%`, background: t.color }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* 视频爆款分分布 */}
        <Card>
          <div className="mb-4 flex items-center justify-between">
            <span className="flex items-center gap-2 text-sm font-semibold"><span className="text-orange-300">✦</span> 视频爆款分分布</span>
            <span className="rounded-full border border-white/[0.12] bg-white/[0.05] px-2 py-0.5 text-[11px] text-gray-300">↗ 平均 {d.avg_video_score}</span>
          </div>
          <div className="flex items-end gap-3" style={{ height: 140 }}>
            {d.score_distribution.map((s, i) => {
              const colors = ['#f43f5e', '#f59e0b', '#eab308', '#84cc16', '#10b981'];
              const h = s.count === 0 ? 4 : 12 + (s.count / maxScore) * 104;
              return (
                <div key={s.range} className="flex flex-1 flex-col items-center justify-end gap-1">
                  <span className="text-xs font-semibold text-gray-300">{s.count}</span>
                  <div className="w-full rounded-t-lg transition-all duration-500" style={{ height: h, background: colors[i] }} />
                  <span className="text-[10px] text-gray-500">{s.range}</span>
                </div>
              );
            })}
          </div>
        </Card>

        {/* 最近项目 */}
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <span className="flex items-center gap-2 text-sm font-semibold"><span className="text-orange-300">🗂</span> 最近项目</span>
            <button onClick={() => navigate('/projects')} className="text-xs text-orange-300 hover:text-orange-200">查看全部 →</button>
          </div>
          {d.recent_projects.length === 0 ? (
            <Empty text="暂无项目" />
          ) : (
            <div className="divide-y divide-white/[0.06]">
              {d.recent_projects.map((p) => (
                <button key={p.id} onClick={() => navigate(`/generate/${p.id}`)} className="flex w-full items-center gap-3 py-2.5 text-left transition-colors hover:bg-white/[0.03]">
                  <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-orange-500/25 to-rose-500/20 text-sm">🗂</span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm text-gray-100">{p.name}</span>
                    <span className="block text-[11px] text-gray-500">{p.type} · {p.assets} 个资产 · {p.date}</span>
                  </span>
                  <span className={'shrink-0 rounded-full px-2 py-0.5 text-[10px] ' + (p.completed ? 'bg-emerald-500/15 text-emerald-400' : 'bg-amber-500/15 text-amber-400')}>
                    {p.completed ? '已完成' : '进行中'}
                  </span>
                </button>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

function Metric({ label, value, sub, icon, accent, onClick }: { label: string; value: number; sub: string; icon: string; accent: string; onClick?: () => void }) {
  return (
    <button onClick={onClick} disabled={!onClick} className="rounded-3xl border border-white/[0.12] bg-white/[0.04] p-4 text-left transition-all duration-300 enabled:hover:-translate-y-0.5 enabled:hover:border-orange-400/40">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs text-gray-400">{label}</span>
        <span className={`grid size-8 place-items-center rounded-xl bg-gradient-to-br ${accent} text-sm`}>{icon}</span>
      </div>
      <div className="text-3xl font-bold text-white">{value.toLocaleString()}</div>
      <div className="mt-1 text-[11px] text-gray-500">{sub}</div>
    </button>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return <div className="rounded-3xl border border-white/[0.12] bg-white/[0.04] p-5">{children}</div>;
}

function Empty({ text }: { text: string }) {
  return <div className="py-8 text-center text-xs text-gray-500">{text}</div>;
}
