import { useMemo, useState } from 'react';

const CATEGORIES = [
  {
    key: 'product', label: '🛍 产品展示',
    prompts: [
      { title: '产品白底图', text: '产品名，纯白背景，专业产品摄影，柔光照明，超高清，8K，商业摄影风格，正面视角' },
      { title: '场景使用图', text: '产品名在具体使用场景中，自然光线，生活化构图，景深虚化背景，温暖色调' },
      { title: '功能特写', text: '产品关键功能细节微距特写，浅景深，金属质感，科技感冷色调，极简构图' },
      { title: '组合套装', text: '产品多个变体组合展示，俯拍45度角，柔和阴影，一致的光源方向，商业目录风格' },
    ],
  },
  {
    key: 'social', label: '📱 社交媒体',
    prompts: [
      { title: '小红书封面', text: '主题，小红书风格，莫兰迪色调，3:4竖版构图，大面积留白，手写字体元素，柔和暖光' },
      { title: '抖音竖版海报', text: '主题，抖音风格，9:16构图，高饱和度，视觉冲击力强，动态感，霓虹灯效果' },
      { title: '微信头图', text: '品牌名称，微信公众号封面，2.35:1横版，极简商务风，品牌色为主色调' },
    ],
  },
  {
    key: 'brand', label: '🎨 品牌视觉',
    prompts: [
      { title: 'Logo设计', text: '品牌名称，极简Logo，矢量风格，扁平化，单色或双色，抽象几何，可缩放' },
      { title: '品牌色板', text: '品牌调性调色板展示，5-6个主色排列，渐变过渡，时尚杂志排版风格' },
      { title: '名片模板', text: '品牌名称，现代名片设计，极简排版，烫金或压凹工艺效果，高级纸张纹理' },
    ],
  },
  {
    key: 'video', label: '🎬 视频创作',
    prompts: [
      { title: '开场镜头', text: '产品从黑暗中渐显，慢推镜头，柔光照射，电影级画质，24fps，浅景深' },
      { title: '转场动画', text: '平滑过渡动画，几何图形变化，品牌色渐变，60fps流畅，无缝循环' },
      { title: '结尾Logo', text: '品牌Logo动画，从中心放大至全屏，粒子消散效果，品牌音效同步，黑底白字' },
    ],
  },
];

type Item = { title: string; text: string; cat: string; catLabel: string };

const ALL: Item[] = CATEGORIES.flatMap((c) => c.prompts.map((p) => ({ ...p, cat: c.key, catLabel: c.label })));

export default function PromptLibrary() {
  const [activeCat, setActiveCat] = useState('all');
  const [q, setQ] = useState('');
  const [copied, setCopied] = useState('');

  const copy = (text: string) => {
    navigator.clipboard?.writeText(text);
    setCopied(text);
    setTimeout(() => setCopied(''), 1500);
  };

  const pills = useMemo(
    () => [
      { key: 'all', label: '全部脚本', count: ALL.length },
      ...CATEGORIES.map((c) => ({ key: c.key, label: c.label, count: c.prompts.length })),
    ],
    [],
  );

  const filtered = ALL.filter((p) => {
    if (activeCat !== 'all' && p.cat !== activeCat) return false;
    if (q && !(p.title + p.text + p.catLabel).toLowerCase().includes(q.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="min-h-[60vh] px-6 py-8 text-white">
      <div className="mx-auto w-full max-w-5xl">
        {/* 标题区 */}
        <div className="mb-5">
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-1 text-[11px] font-medium tracking-[0.18em] text-orange-200/90 uppercase">
            Creative Scripts
          </div>
          <h1 className="text-2xl font-bold tracking-tight md:text-3xl">创意脚本库</h1>
          <p className="mt-1 max-w-2xl text-sm text-gray-400">
            汇集高转化创意脚本与提示词模板，按平台与场景分类，一键复制即可用于生成。
          </p>
        </div>

        {/* 搜索 */}
        <div className="mb-4 max-w-md">
          <div className="relative">
            <svg viewBox="0 0 24 24" className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-gray-500" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" />
            </svg>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="搜索脚本或关键词…"
              className="h-10 w-full rounded-lg border border-white/[0.1] bg-white/[0.04] pl-9 pr-3 text-sm text-white placeholder:text-gray-600 outline-none transition-colors focus:border-orange-400/40"
            />
          </div>
        </div>

        {/* 分类 pills */}
        <div className="mb-6 flex gap-2 overflow-x-auto pb-1">
          {pills.map((c) => (
            <button
              key={c.key}
              onClick={() => setActiveCat(c.key)}
              className={
                'whitespace-nowrap rounded-full border px-3 py-1.5 text-sm transition-colors ' +
                (activeCat === c.key
                  ? 'border-orange-400/40 bg-orange-500/20 text-orange-200'
                  : 'border-white/[0.08] bg-white/[0.03] text-gray-400 hover:text-gray-200')
              }
            >
              {c.label} <span className="opacity-60">({c.count})</span>
            </button>
          ))}
        </div>

        {/* 卡片网格 */}
        <div className="grid gap-4 sm:grid-cols-2">
          {filtered.map((p, i) => (
            <div
              key={p.cat + i}
              className="group rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5 backdrop-blur-xl transition-all hover:-translate-y-0.5 hover:border-orange-400/30"
            >
              <div className="mb-3 flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <h3 className="truncate text-sm font-semibold text-white">{p.title}</h3>
                  <div className="text-[10px] text-gray-500">{p.catLabel}</div>
                </div>
                <button
                  onClick={() => copy(p.text)}
                  className={
                    'shrink-0 rounded-lg px-2 py-1 text-xs transition-all ' +
                    (copied === p.text
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'bg-white/[0.05] text-gray-500 hover:bg-orange-500/10 hover:text-orange-400')
                  }
                >
                  {copied === p.text ? '✓ 已复制' : '📋 复制'}
                </button>
              </div>
              <p className="text-sm leading-relaxed text-gray-400">{p.text}</p>
            </div>
          ))}
        </div>
        {filtered.length === 0 && (
          <div className="py-16 text-center text-sm text-gray-500">未找到匹配的脚本</div>
        )}
      </div>
    </div>
  );
}
