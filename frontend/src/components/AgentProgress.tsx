import { useEffect, useState } from 'react';

// 具名子 Agent 流(对齐 PRD §8.2:让用户看见过程 / 思维导图式状态流)
const AGENTS = [
  { icon: '🧠', label: 'Project Manager', desc: '解析 brief · 拆解任务 · 调度子 Agent', msg: '正在理解你的目标与受众' },
  { icon: '🔍', label: 'Research · Brand · Visual', desc: '行业洞察 · 品牌策略 · 视觉方向', msg: '正在分析行业与视觉方向' },
  { icon: '✍️', label: 'Copywriting', desc: '中文广告文案 · 标题 · 卖点', msg: '正在撰写中文文案与卖点' },
  { icon: '🖼️', label: 'Image Generation', desc: '生成多平台视觉资产', msg: '正在生成第一套主视觉' },
  { icon: '🧩', label: 'Layout', desc: '中文排版 · 画布组织', msg: '正在统一排版、颜色与字体' },
  { icon: '📦', label: 'Mockup', desc: '包装 / 立牌 / 瓶身 mockup', msg: '正在套用真实场景 mockup' },
  { icon: '🛡️', label: 'Compliance', desc: '广告法 · 平台合规检查', msg: '正在检查文案与平台合规' },
  { icon: '⬇️', label: 'Export', desc: '多平台尺寸包 · 品牌资产包', msg: '正在整理可交付资产' },
];

interface Props {
  active: boolean;
}

export default function AgentProgress({ active }: Props) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (!active) { setStep(0); return; }
    setStep(0);
    const interval = setInterval(() => {
      setStep((prev) => {
        if (prev >= AGENTS.length - 1) { clearInterval(interval); return prev; }
        return prev + 1;
      });
    }, 1600 + Math.random() * 1200); // 1.6–2.8s / agent
    return () => clearInterval(interval);
  }, [active]);

  if (!active) return null;

  const percent = Math.round(((step + 1) / AGENTS.length) * 100);
  const current = AGENTS[Math.min(step, AGENTS.length - 1)];

  return (
    <div className="mx-auto w-full max-w-lg">
      <div className="liquid-card space-y-4 p-5">
        {/* 顶部:状态流 + 进度 */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="flex size-5 items-center justify-center">
              <span className="size-2.5 animate-ping rounded-full bg-orange-400" />
            </span>
            <span className="text-sm font-medium text-gray-100">AI Agent 工作中</span>
            <span className="ml-auto text-xs tabular-nums text-orange-300">{percent}%</span>
          </div>
          <p className="text-xs text-gray-400">{current.msg}…</p>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/[0.08]">
            <div className="h-full rounded-full bg-gradient-to-r from-orange-500 to-rose-500 transition-all duration-500" style={{ width: `${percent}%` }} />
          </div>
        </div>

        {/* 具名子 Agent 列表 */}
        <div className="space-y-1.5">
          {AGENTS.map((a, i) => {
            const done = i < step;
            const running = i === step;
            return (
              <div
                key={a.label}
                className={
                  'flex items-center gap-3 rounded-xl border px-3 py-2 transition-all duration-500 ' +
                  (running
                    ? 'border-orange-400/40 bg-orange-500/[0.08]'
                    : done
                      ? 'border-white/[0.06] bg-white/[0.03]'
                      : 'border-transparent opacity-40')
                }
              >
                <span
                  className={
                    'grid size-7 shrink-0 place-items-center rounded-lg text-sm ' +
                    (done ? 'bg-emerald-500/15' : running ? 'bg-orange-500/20 animate-pulse' : 'bg-white/[0.05]')
                  }
                >
                  {done ? '✓' : a.icon}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-xs font-medium text-gray-200">{a.label}</span>
                  <span className="block truncate text-[10px] text-gray-500">{a.desc}</span>
                </span>
                {done && <span className="text-[10px] text-emerald-400/70">完成</span>}
                {running && (
                  <span className="flex gap-1">
                    <span className="size-1 animate-bounce rounded-full bg-orange-400" style={{ animationDelay: '0ms' }} />
                    <span className="size-1 animate-bounce rounded-full bg-orange-400" style={{ animationDelay: '150ms' }} />
                    <span className="size-1 animate-bounce rounded-full bg-orange-400" style={{ animationDelay: '300ms' }} />
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
