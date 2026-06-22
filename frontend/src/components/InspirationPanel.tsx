import { useState, useEffect } from 'react';

interface InspirationItem {
  id: number;
  category: string;
  sub_category: string;
  preview_url: string;
  prompt_template: string;
  aspect_ratio: string;
}

interface CategoryTree {
  [category: string]: string[];
}

interface Props {
  onClose: () => void;
  onUseStyle?: (prompt: string, item: InspirationItem) => void;
}

const CATEGORY_LABELS: Record<string, string> = {
  poster: '海报', app: 'APP', illustration: '插画', ops: '运营', ip: 'IP',
};

const CAT_COLORS: Record<string, { from: string; to: string; text: string; bg: string }> = {
  poster: { from: 'from-orange-500', to: 'to-pink-500', text: 'text-orange-400', bg: 'bg-orange-500/10' },
  app: { from: 'from-blue-500', to: 'to-cyan-500', text: 'text-blue-400', bg: 'bg-blue-500/10' },
  illustration: { from: 'from-pink-500', to: 'to-rose-500', text: 'text-pink-400', bg: 'bg-pink-500/10' },
  ops: { from: 'from-emerald-500', to: 'to-teal-500', text: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  ip: { from: 'from-violet-500', to: 'to-purple-500', text: 'text-violet-400', bg: 'bg-violet-500/10' },
};

const PLATFORM_OPTIONS = ['不指定', '淘宝', '小红书', '抖音', '拼多多', '微信', 'Amazon'];

const CAT_ICONS: Record<string, string> = {
  poster: '🎬', app: '📱', illustration: '🎨', ops: '📊', ip: '🐱',
};

export default function InspirationPanel({ onClose, onUseStyle }: Props) {
  const [categories, setCategories] = useState<CategoryTree>({});
  const [items, setItems] = useState<InspirationItem[]>([]);
  const [activeCat, setActiveCat] = useState('');
  const [activeSub, setActiveSub] = useState('');
  const [selected, setSelected] = useState<InspirationItem | null>(null);
  const [loading, setLoading] = useState(true);

  const [editPrompt, setEditPrompt] = useState('');
  const [productName, setProductName] = useState('');
  const [brandDesc, setBrandDesc] = useState('');
  const [platform, setPlatform] = useState('');

  useEffect(() => {
    fetch('/api/v1/inspirations/categories')
      .then(r => r.json())
      .then(data => {
        setCategories(data);
        const cats = Object.keys(data).filter(k => k !== 'test');
        if (cats.length > 0) setActiveCat(cats[0]);
      })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!activeCat) return;
    setLoading(true);
    setSelected(null);
    setActiveSub('');
    const params = new URLSearchParams({ category: activeCat, limit: '50' });
    fetch(`/api/v1/inspirations?${params}`)
      .then(r => r.json())
      .then(data => { setItems(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [activeCat]);

  const handleSelectItem = (item: InspirationItem) => {
    setSelected(item);
    setEditPrompt(item.prompt_template);
    setProductName('');
    setBrandDesc('');
    setPlatform('');
      };

  const buildParameterizedPrompt = () => {
    let p = editPrompt;
    const extras: string[] = [];
    if (productName.trim()) extras.push(`产品名称：${productName.trim()}`);
    if (brandDesc.trim()) extras.push(`品牌描述：${brandDesc.trim()}`);
    if (platform) extras.push(`目标平台：${platform}`);
    if (extras.length > 0) {
      p += '\n\n---\n产品信息：\n' + extras.join('\n') + '\n请基于以上风格参考和产品信息生成视觉素材。';
    }
    return p;
  };

  const handleUseDirect = () => {
    if (selected && onUseStyle) onUseStyle(editPrompt, selected);
  };

  const handleUseParameterized = () => {
    if (selected && onUseStyle) onUseStyle(buildParameterizedPrompt(), selected);
  };

  const filteredItems = activeSub
    ? items.filter(i => i.sub_category === activeSub)
    : items;

  const subs = categories[activeCat] || [];
  const accent = CAT_COLORS[activeCat] || CAT_COLORS.poster;

  // ── Render: Skeleton loader ──
  const SkeletonGrid = () => (
    <div className="grid gap-3" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))' }}>
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} className="aspect-square rounded-xl bg-white/[0.04] border border-white/[0.06] animate-pulse" />
      ))}
    </div>
  );

  // ── Render: Empty state ──
  const EmptyState = () => (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <div className="w-20 h-20 rounded-2xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center">
        <span className="text-3xl opacity-30">🖼</span>
      </div>
      <div className="text-center">
        <p className="text-sm text-gray-400 font-medium">暂无灵感素材</p>
        <p className="text-[11px] text-gray-600 mt-1">该分类下还没有灵感参考</p>
      </div>
    </div>
  );

  // ── Render: Main panel ──
  return (
    <div data-inspiration-gallery className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-xl px-4 py-8 animate-fadeIn" onClick={onClose}>
      <div
        className="mx-auto w-full max-w-5xl rounded-[28px] border border-white/[0.14] bg-gradient-to-br from-white/[0.13] via-white/[0.07] to-white/[0.03]
          p-5 shadow-[0_30px_100px_rgba(0,0,0,0.55),inset_0_1px_0_rgba(255,255,255,0.16)]"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 -mx-1 bg-gradient-to-b from-black/25 via-black/10 to-transparent pb-3 backdrop-blur-xl">
          <div className="mb-4 flex items-start justify-between gap-4 px-1 pt-1">
            <div>
              <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-1 text-[11px] font-medium tracking-[0.18em] text-orange-200/90 uppercase">
                Inspiration Gallery
              </div>
              <h2 className="text-2xl font-bold tracking-tight text-white">灵感陈列柜</h2>
              <p className="mt-1 text-sm text-gray-400">像逛作品集一样挑选创意参考 · 选中后可直接复用或参数化生成</p>
            </div>
            <div className="flex items-center gap-2">
              {selected && (
                <button
                  onClick={() => { setSelected(null);  }}
                  className="rounded-full border border-white/[0.12] bg-white/[0.05] px-3 py-2 text-xs text-gray-400 transition-colors hover:text-white"
                >
                  返回列表
                </button>
              )}
              <button onClick={onClose}
                className="rounded-full border border-white/[0.12] bg-white/[0.05] px-3 py-2 text-xs text-gray-400 transition-colors hover:text-white"
              >返回</button>
            </div>
          </div>

          {/* Category tabs */}
          <div className="flex gap-2 border-t border-white/[0.08] px-1 pt-4 pb-1 overflow-x-auto scrollbar-hide">
            {Object.keys(categories).filter(k => k !== 'test').map(cat => {
              const c = CAT_COLORS[cat] || CAT_COLORS.poster;
              const count = cat === activeCat ? items.length : 0;
              const isActive = activeCat === cat;
              return (
                <button
                  key={cat}
                  onClick={() => setActiveCat(cat)}
                  className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-medium whitespace-nowrap
                    transition-all duration-200 border
                    ${isActive
                      ? `bg-gradient-to-r ${c.from}/20 ${c.to}/20 ${c.text} border-${c.from.replace('from-', '')}/30`
                      : 'text-gray-400 hover:text-gray-200 hover:bg-white/[0.04] border-transparent'
                    }`}
                >
                  <span>{CAT_ICONS[cat]}</span>
                  <span>{CATEGORY_LABELS[cat] || cat}</span>
                  {isActive && count > 0 && (
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${c.bg} ${c.text}`}>{count}</span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Sub-category filters */}
          {subs.length > 1 && (
            <div className="flex gap-1.5 px-1 pt-2 overflow-x-auto scrollbar-hide">
              <button
                onClick={() => setActiveSub('')}
                className={`px-2.5 py-1 rounded-lg text-xs whitespace-nowrap transition-all ${
                  !activeSub
                    ? 'bg-white/10 text-white'
                    : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.04]'
                }`}
              >
                全部 <span className="text-gray-600">({items.length})</span>
              </button>
              {subs.map(sub => {
                const count = items.filter(i => i.sub_category === sub).length;
                return (
                  <button
                    key={sub}
                    onClick={() => setActiveSub(sub)}
                    className={`px-2.5 py-1 rounded-lg text-xs whitespace-nowrap transition-all ${
                      activeSub === sub
                        ? 'bg-white/10 text-white'
                        : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.04]'
                    }`}
                  >
                    {sub} <span className="text-gray-600">({count})</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Content area */}
        <div className="pt-3">
          {loading ? (
            <SkeletonGrid />
          ) : filteredItems.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {filteredItems.map(item => {
                const c = CAT_COLORS[item.category] || CAT_COLORS.poster;
                const isSelected = selected?.id === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleSelectItem(item)}
                    className={`inspiration-gallery-card relative group rounded-3xl overflow-hidden border transition-all duration-500
                      bg-white/[0.055] aspect-square
                      ${isSelected
                        ? `border-orange-400/45 shadow-[0_24px_70px_rgba(251,146,60,0.22)] scale-[1.03]`
                        : `border-white/[0.12] hover:-translate-y-1 hover:border-orange-400/45 hover:bg-white/[0.08] hover:shadow-[0_24px_70px_rgba(251,146,60,0.16)]`
                      }`}
                  >
                    {/* Image */}
                    <img
                      src={item.preview_url}
                      alt={item.sub_category}
                      className="absolute inset-0 w-full h-full object-cover"
                      loading="lazy"
                      onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                    />

                    {/* Gradient overlay for text readability */}
                    <div className={`absolute inset-0 bg-gradient-to-t from-black/75 via-black/10 to-transparent opacity-80 group-hover:opacity-100 transition-opacity`} />
                    <div className="absolute left-3 top-3 rounded-full border border-white/15 bg-black/25 px-2 py-1 text-[10px] text-white/70 backdrop-blur-md">灵感封面</div>

                    {/* Bottom label */}
                    <div className="absolute bottom-0 left-0 right-0 p-2.5">
                      <span className={`inline-block px-2 py-0.5 rounded-md text-[10px] font-medium backdrop-blur-md
                        ${c.bg} ${c.text} border border-white/[0.06]`}>
                        {item.sub_category}
                      </span>
                    </div>

                    {/* Hover prompt preview */}
                    <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition-all duration-300
                      flex items-center justify-center p-4 backdrop-blur-sm">
                      <p className="text-white text-xs text-center leading-relaxed line-clamp-5">
                        {item.prompt_template.slice(0, 200)}...
                      </p>
                    </div>

                    {/* Aspect ratio badge */}
                    <div className="absolute top-2 right-2 px-1.5 py-0.5 rounded text-[9px] bg-black/60 text-gray-300 backdrop-blur-sm border border-white/[0.08]">
                      {item.aspect_ratio}
                    </div>

                    {/* Selected indicator */}
                    {isSelected && (
                      <div className="absolute top-2 left-2 w-5 h-5 rounded-full bg-gradient-to-r from-orange-500 to-pink-500 flex items-center justify-center">
                        <span className="text-white text-[10px]">✓</span>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* ── Detail / Template Modal ── */}
      {selected && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={() => { setSelected(null);  }}>
          <div
            className="backdrop-blur-2xl bg-gradient-to-br from-white/[0.13] via-white/[0.07] to-white/[0.03]
              border border-white/[0.14] rounded-[28px] w-full max-w-[560px] mx-4 max-h-[88vh] overflow-y-auto
              shadow-[0_30px_100px_rgba(0,0,0,0.65),inset_0_1px_0_rgba(255,255,255,0.16)] animate-fadeIn"
            onClick={e => e.stopPropagation()}
          >
            {/* Preview image */}
            <div className="relative aspect-[16/9] rounded-t-2xl overflow-hidden bg-white/[0.03]">
              <img
                src={selected.preview_url}
                alt="Preview"
                className="w-full h-full object-cover"
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
              />
              <div className="absolute top-3 left-3 flex gap-1.5">
                <span className={`px-2 py-0.5 rounded-md text-[10px] font-medium backdrop-blur-md ${accent.bg} ${accent.text} border border-white/[0.06]`}>
                  {selected.category}
                </span>
                <span className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-black/50 text-gray-300 backdrop-blur-md border border-white/[0.06]">
                  {selected.sub_category}
                </span>
              </div>
            </div>

            {/* Body */}
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-[11px] text-gray-500 uppercase tracking-wider mb-2">风格 Prompt · 可编辑</label>
                <textarea
                  value={editPrompt}
                  onChange={e => setEditPrompt(e.target.value)}
                  rows={6}
                  className="w-full bg-white/[0.05] border border-white/[0.10] rounded-xl px-4 py-3 text-sm text-gray-200
                    placeholder-gray-600 focus:border-orange-500/40 focus:bg-white/[0.08] outline-none resize-y
                    leading-relaxed transition-all"
                />
              </div>

              {/* Quick parameters */}
              <div>
                <label className="block text-[11px] text-gray-500 uppercase tracking-wider mb-2">快速参数替换 · 可选</label>
                <div className="space-y-2">
                  <input
                    type="text" value={productName}
                    onChange={e => setProductName(e.target.value)}
                    placeholder="产品名称，如：无线降噪耳机"
                    className="w-full bg-white/[0.05] border border-white/[0.10] rounded-lg px-3 py-2.5 text-sm text-gray-200
                      placeholder-gray-600 focus:border-orange-500/40 outline-none transition-all"
                  />
                  <input
                    type="text" value={brandDesc}
                    onChange={e => setBrandDesc(e.target.value)}
                    placeholder="品牌描述/调性，如：极简科技风"
                    className="w-full bg-white/[0.05] border border-white/[0.10] rounded-lg px-3 py-2.5 text-sm text-gray-200
                      placeholder-gray-600 focus:border-orange-500/40 outline-none transition-all"
                  />
                  <select
                    value={platform}
                    onChange={e => setPlatform(e.target.value)}
                    className="w-full bg-white/[0.05] border border-white/[0.10] rounded-lg px-3 py-2.5 text-sm text-gray-200
                      focus:border-orange-500/40 outline-none transition-all appearance-none cursor-pointer"
                  >
                    {PLATFORM_OPTIONS.map(p => (
                      <option key={p} value={p === '不指定' ? '' : p} className="bg-[#151528] text-gray-200">{p}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Live preview */}
              {(productName || brandDesc || platform) && (
                <div>
                  <label className="block text-[11px] text-gray-500 uppercase tracking-wider mb-2">实时预览</label>
                  <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.08] text-xs text-gray-400
                    leading-relaxed max-h-28 overflow-y-auto whitespace-pre-wrap font-mono">
                    {buildParameterizedPrompt()}
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center gap-2 px-5 py-4 border-t border-white/[0.08]">
              <button
                onClick={() => { setSelected(null);  }}
                className="px-4 py-2.5 rounded-xl bg-white/[0.05] border border-white/[0.10] text-gray-400 text-sm
                  hover:text-white hover:bg-white/[0.10] transition-all"
              >
                取消
              </button>
              <button
                onClick={handleUseDirect}
                className="flex-1 py-2.5 rounded-xl border border-orange-500/30 text-orange-400 text-sm font-medium
                  hover:bg-orange-500/10 transition-all"
              >
                直接复用原 Prompt
              </button>
              <button
                onClick={handleUseParameterized}
                className="flex-[1.3] py-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-pink-500 text-white text-sm font-medium
                  hover:from-orange-400 hover:to-pink-400 transition-all shadow-lg shadow-orange-500/20"
              >
                参数化后生成 →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Prevent tree-shaking
const _ref = InspirationPanel; void _ref;
