import { useState } from 'react';
import { Link } from 'react-router-dom';

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

export default function PromptLibrary() {
  const [activeCat, setActiveCat] = useState('product');
  const [copied, setCopied] = useState('');

  const copy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(text);
    setTimeout(() => setCopied(''), 1500);
  };

  return (
    <div className="min-h-screen bg-black text-gray-100">
      <header className="sticky top-0 z-10 px-6 py-2 flex items-center justify-between bg-black/80 backdrop-blur border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <Link to="/" className="text-gray-500 hover:text-white transition-colors text-sm">← 返回</Link>
          <span className="text-white/20">|</span>
          <span className="text-sm font-medium">📚 提示词库</span>
        </div>
        <span className="text-xs text-gray-600">{CATEGORIES.reduce((s, c) => s + c.prompts.length, 0)} 条精选提示词</span>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Category tabs */}
        <div className="flex gap-2 mb-8 flex-wrap">
          {CATEGORIES.map(cat => (
            <button key={cat.key} onClick={() => setActiveCat(cat.key)}
              className={`px-4 py-2 rounded-xl text-sm transition-all ${
                activeCat === cat.key
                  ? 'bg-orange-500/20 border border-orange-500/40 text-orange-300'
                  : 'bg-white/[0.03] border border-white/[0.06] text-gray-500 hover:text-gray-300'
              }`}>
              {cat.label}
            </button>
          ))}
        </div>

        {/* Prompt cards */}
        <div className="grid gap-4 sm:grid-cols-2">
          {CATEGORIES.find(c => c.key === activeCat)?.prompts.map((p, i) => (
            <div key={i}
              className="backdrop-blur-xl bg-white/[0.03] border border-white/[0.08] hover:border-orange-500/20 rounded-2xl p-5 transition-all group">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-white">{p.title}</h3>
                <button onClick={() => copy(p.text)}
                  className={`text-xs px-2 py-1 rounded-lg transition-all ${
                    copied === p.text
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-white/[0.05] text-gray-500 hover:text-orange-400 hover:bg-orange-500/10'
                  }`}>
                  {copied === p.text ? '✓ 已复制' : '📋 复制'}
                </button>
              </div>
              <p className="text-sm text-gray-400 leading-relaxed">{p.text}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
