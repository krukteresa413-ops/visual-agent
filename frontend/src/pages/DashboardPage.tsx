import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import api from '../api/client';

interface TrendPoint {
  label: string;
  value: number;
}

interface DistributionItem {
  name: string;
  count: number;
  color: string;
}

interface DashboardData {
  greeting: string;
  user_name: string;
  total_projects: number;
  total_generations: number;
  projects_with_activity: number;
  generations_today: number;
  generations_this_week: number;
  success_rate: number;
  active_agents: string[];
  agent_distribution: DistributionItem[];
  daily_trend: TrendPoint[];
  type_distribution: DistributionItem[];
  recent_activity: Array<{
    id: number;
    project_name: string;
    asset_type: string;
    model_used: string;
    status: string;
    created_at: string | null;
  }>;
}

const TYPE_LABELS: Record<string, string> = {
  main_image: '主视觉', white_bg: '白底图', scene_image: '场景图',
  selling_point: '卖点', video_script: '视频脚本', ad_material: '广告素材',
};

const fetchDashboard = () =>
  api.get<DashboardData>('/dashboard/').then((r: any) => r.data).then(r => r.data);

export default function DashboardPage() {
  const { data } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
    refetchInterval: 60000,
  });

  const [chartTab, setChartTab] = useState<'trend' | 'distribution'>('trend');

  const dd = data || {
    greeting: '你好', user_name: 'MOYAG', total_projects: 0, total_generations: 0,
    projects_with_activity: 0, generations_today: 0, generations_this_week: 0,
    success_rate: 0, active_agents: [], agent_distribution: [],
    daily_trend: [], type_distribution: [], recent_activity: [],
  } as DashboardData;

  const maxTrend = Math.max(...dd.daily_trend.map((d: TrendPoint) => d.value), 1);
  const maxDist = Math.max(...dd.type_distribution.map((d: DistributionItem) => d.count), 1);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0a14] via-[#0f0f1e] to-[#0a0a14] text-white">
      {/* Header */}
      <header className="px-6 pt-6 pb-2">
        <h1 className="text-xl font-bold">
          <span className="text-gray-400">👋 {dd.greeting}，</span>
          <span className="text-white">{dd.user_name}</span>
        </h1>
      </header>

      <main className="px-6 pb-12 max-w-6xl mx-auto space-y-4">
        {/* ── Metric Cards Row ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Card 1: 项目概览 */}
          <MetricCardGroup
            title="项目概览"
            icon="📊"
            items={[
              { label: '项目总数', value: dd.total_projects.toLocaleString(), color: '#3b82f6', icon: '📁' },
              { label: '活跃项目', value: dd.projects_with_activity.toLocaleString(), color: '#8b5cf6', icon: '📈' },
            ]}
          />

          {/* Card 2: 生成统计 */}
          <MetricCardGroup
            title="生成统计"
            icon="✅"
            items={[
              { label: '总生成次数', value: dd.total_generations.toLocaleString(), color: '#10b981', icon: '🎯' },
              { label: '今日生成', value: dd.generations_today.toLocaleString(), color: '#06b6d4', icon: '📅' },
              { label: '成功率', value: `${dd.success_rate}%`, color: '#f59e0b', icon: '✨' },
            ]}
            miniChart={
              <div className="flex items-end gap-[1px] h-10 mt-2">
                {dd.daily_trend.map((d: TrendPoint, i: number) => (
                  <div
                    key={i}
                    className="flex-1 rounded-t-sm transition-all"
                    style={{
                      height: `${Math.max((d.value / maxTrend) * 100, 4)}%`,
                      backgroundColor: d.value > 0 ? '#06b6d4' : '#1f2937',
                      opacity: 0.6 + (d.value / maxTrend) * 0.4,
                    }}
                  />
                ))}
              </div>
            }
          />

          {/* Card 3: Agent 活跃度 */}
          <MetricCardGroup
            title="Agent 活跃度"
            icon="AI"
            items={[
              { label: '活跃 Agent', value: dd.active_agents.length.toString(), color: '#f59e0b', icon: '🔧' },
              { label: '本周生成', value: dd.generations_this_week.toLocaleString(), color: '#ec4899', icon: '📊' },
            ]}
          >
            {/* Horizontal bar chart for agent distribution */}
            <div className="mt-2 space-y-1.5">
              {dd.agent_distribution.map((item: DistributionItem, i: number) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-[10px] text-gray-500 w-20 truncate">{item.name}</span>
                  <div className="flex-1 h-2 bg-white/[0.06] rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${(item.count / Math.max(...dd.agent_distribution.map((d: DistributionItem) => d.count), 1)) * 100}%`,
                        backgroundColor: item.color,
                      }}
                    />
                  </div>
                  <span className="text-[10px] text-gray-600 w-8 text-right">{item.count}</span>
                </div>
              ))}
            </div>
          </MetricCardGroup>
        </div>

        {/* ── Active Agents Tags ── */}
        <div className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <span className="text-[11px] text-gray-500 font-medium shrink-0">活跃 Agent</span>
          <div className="flex flex-wrap gap-1.5">
            {dd.active_agents.map((agent: string) => (
              <span key={agent}
                className="px-2 py-0.5 text-[11px] rounded-md bg-green-500/10 text-green-400 border border-green-500/20"
              >{agent}</span>
            ))}
          </div>
          <a href="/generate/2" className="ml-auto text-[11px] text-orange-400 hover:text-orange-300 shrink-0">
            图片生成 →
          </a>
        </div>

        {/* ── Chart Section ── */}
        <div className="rounded-xl bg-white/[0.03] border border-white/[0.06] overflow-hidden">
          {/* Chart header + tabs */}
          <div className="flex items-center justify-between px-5 py-3 border-b border-white/[0.06]">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">⏰</span>
              <h3 className="text-sm font-medium text-white">生成数据分析</h3>
            </div>
            <div className="flex gap-1">
              {([
                ['trend', '生成趋势'],
                ['distribution', '类型分布'],
              ] as const).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setChartTab(key)}
                  className={`px-3 py-1.5 rounded-lg text-xs transition-all ${
                    chartTab === key
                      ? 'bg-white/[0.10] text-white'
                      : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.04]'
                  }`}
                >{label}</button>
              ))}
            </div>
          </div>

          {/* Chart content */}
          <div className="p-5">
            {chartTab === 'trend' ? (
              /* ── Daily Trend Bar Chart ── */
              <div>
                <div className="flex items-baseline gap-2 mb-4">
                  <span className="text-lg font-bold text-white">
                    {dd.daily_trend.reduce((s: number, d: TrendPoint) => s + d.value, 0)} 次
                  </span>
                  <span className="text-[11px] text-gray-500">近14天总生成</span>
                </div>
                <div className="flex items-end gap-[2px] h-32">
                  {dd.daily_trend.map((d: TrendPoint, i: number) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1 group">
                      <span className="text-[9px] text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity">
                        {d.value}
                      </span>
                      <div
                        className="w-full rounded-t-sm transition-all hover:opacity-80 cursor-pointer"
                        style={{
                          height: `${Math.max((d.value / maxTrend) * 100, 3)}%`,
                          backgroundColor: d.value > 0 ? '#f97316' : '#1f2937',
                        }}
                      />
                      <span className="text-[9px] text-gray-600 mt-1">{d.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              /* ── Type Distribution ── */
              <div>
                <div className="flex items-baseline gap-2 mb-4">
                  <span className="text-lg font-bold text-white">
                    {dd.type_distribution.length} 类
                  </span>
                  <span className="text-[11px] text-gray-500">素材类型</span>
                </div>
                <div className="space-y-3">
                  {dd.type_distribution.map((item: DistributionItem, i: number) => (
                    <div key={i} className="flex items-center gap-3">
                      <span className="text-xs text-gray-400 w-16 shrink-0">
                        {TYPE_LABELS[item.name] || item.name}
                      </span>
                      <div className="flex-1 h-3 bg-white/[0.04] rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${(item.count / maxDist) * 100}%`,
                            backgroundColor: item.color,
                          }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 w-10 text-right">{item.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Recent Activity Table ── */}
        <div className="rounded-xl bg-white/[0.03] border border-white/[0.06] overflow-hidden">
          <div className="px-5 py-3 border-b border-white/[0.06] flex items-center gap-2">
            <span className="text-sm text-gray-400">📋</span>
            <h3 className="text-sm font-medium text-white">最近生成</h3>
          </div>
          <div className="divide-y divide-white/[0.04]">
            {dd.recent_activity.length === 0 ? (
              <p className="p-6 text-center text-xs text-gray-600">暂无生成记录</p>
            ) : (
              dd.recent_activity.map((item: DashboardData["recent_activity"][number]) => (
                <div key={item.id}
                  className="px-5 py-3 flex items-center justify-between hover:bg-white/[0.03] transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center text-xs"
                      style={{ backgroundColor: '#f9731620', color: '#f97316' }}>
                      #{item.id}
                    </div>
                    <div>
                      <p className="text-xs text-gray-300">{item.project_name}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] text-gray-500">
                          {TYPE_LABELS[item.asset_type] || item.asset_type}
                        </span>
                        <span className="text-[10px] text-gray-600">·</span>
                        <span className="text-[10px] text-gray-600">{item.model_used}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      item.status === 'completed'
                        ? 'bg-green-500/10 text-green-400'
                        : 'bg-yellow-500/10 text-yellow-400'
                    }`}>
                      {item.status === 'completed' ? '完成' : item.status}
                    </span>
                    <span className="text-[10px] text-gray-600">
                      {item.created_at ? formatTime(item.created_at) : ''}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// ── Sub-components ──

function MetricCardGroup({
  title, icon, items, miniChart, children,
}: {
  title: string;
  icon: string;
  items: Array<{ label: string; value: string; color: string; icon: string }>;
  miniChart?: React.ReactNode;
  children?: React.ReactNode;
}) {
  return (
    <div className="rounded-xl bg-white/[0.03] border border-white/[0.06] p-4">
      <div className="flex items-center gap-2 mb-3">
        <span>{icon}</span>
        <span className="text-xs text-gray-400 font-medium">{title}</span>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {items.map((item, i) => (
          <div key={i}>
            <div className="flex items-center gap-1.5 mb-1">
              <span className="text-xs">{item.icon}</span>
              <span className="text-[10px] text-gray-500">{item.label}</span>
            </div>
            <p className="text-lg font-bold text-white">{item.value}</p>
          </div>
        ))}
      </div>
      {miniChart}
      {children}
    </div>
  );
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  const month = (d.getMonth() + 1).toString().padStart(2, '0');
  const day = d.getDate().toString().padStart(2, '0');
  const h = d.getHours().toString().padStart(2, '0');
  const m = d.getMinutes().toString().padStart(2, '0');
  return `${month}-${day} ${h}:${m}`;
}
