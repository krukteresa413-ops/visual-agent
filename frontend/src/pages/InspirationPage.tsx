import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

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

export default function InspirationPage() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState<CategoryTree>({});
  const [items, setItems] = useState<InspirationItem[]>([]);
  const [activeCat, setActiveCat] = useState('');
  const [activeSub, setActiveSub] = useState('');
  const [selected, setSelected] = useState<InspirationItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

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
    if (!activeCat && !searchQuery) return;
    setLoading(true);
    setSelected(null);
    setActiveSub('');
    
    const params = new URLSearchParams();
    if (searchQuery) {
      params.append('q', searchQuery);
    } else if (activeCat) {
      params.append('category', activeCat);
    }
    params.append('limit', '50');
    
    fetch(`/api/v1/inspirations?${params}`)
      .then(r => r.json())
      .then(data => { setItems(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [activeCat, searchQuery]);

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

  const startWithPrompt = async (prompt: string) => {
    try {
      const project = await api.projects.create(
        productName.trim() || selected?.sub_category || '灵感项目',
        '',
      );
      navigate(`/generate/${project.id}`, { state: { quickMode: true, prompt } });
    } catch {
      navigate('/');
    }
  };

  const handleUseDirect = () => startWithPrompt(editPrompt);

  const handleUseParameterized = () => startWithPrompt(buildParameterizedPrompt());

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // 搜索会通过 useEffect 自动触发
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
        <p className="text-[11px] text-gray-600 mt-1">
          {searchQuery ? '试试其他关键词' : '该分类下还没有灵感参考'}
        </p>
      </div>
    </div>
  );

  // ── Render: Main page ──
  return (
    <div className="liquid-page min-h-screen p-6">
      <div className="max-w-[1400px] mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl bg-gradient-to-br from-orange-500 to-pink-500">
                💡
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">灵感库</h1>
                <p className="text-xs text-gray-500">Creative Inspiration Library</p>
              </div>
            </div>
          </div>

          {/* Search bar */}
          <form onSubmit={handleSearch} className="mb-4">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="自然语言搜索，如：运动鞋场景图、海报设计..."
                className="w-full bg-white/[0.05] border border-white/[0.10] rounded-xl px-4 py-3 pl-11 text-sm text-gray-200
                  placeholder-gray-600 focus:border-orange-500/40 focus:bg-white/[0.08] outline-none transition-all"
              />
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">🔍</span>
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  ✕
                </button>
              )}
            </div>
          </form>

          {/* Category tabs */}
          {!searchQuery && (
            <div className="flex gap-2 overflow-x-auto scrollbar-hide">
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
          )}

          {/* Sub-category filters */}
          {!searchQuery && subs.length > 1 && (
            <div className="flex gap-1.5 mt-3 overflow-x-auto scrollbar-hide">
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
        <div>
          {loading ? (
            <SkeletonGrid />
          ) : filteredItems.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="grid gap-3" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))' }}>
              {filteredItems.map(item => {
                const c = CAT_COLORS[item.category] || CAT_COLORS.poster;
                const isSelected = selected?.id === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleSelectItem(item)}
                    className={`relative group rounded-xl overflow-hidden border-2 transition-all duration-300
                      bg-white/[0.03] aspect-square
                      ${isSelected
                        ? `border-white/30 shadow-[0_0_24px_rgba(251,146,60,0.3)] scale-[1.03]`
                        : `border-white/[0.06] hover:border-white/[0.20] hover:scale-[1.02] hover:shadow-xl`
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

                    {/* Gradient overlay */}
                    <div className={`absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent opacity-80 group-hover:opacity-100 transition-opacity`} />

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
            className="backdrop-blur-2xl bg-gradient-to-br from-[#111122] via-[#151528] to-[#0d1122]
              border border-white/[0.12] rounded-2xl w-full max-w-[560px] mx-4 max-h-[88vh] overflow-y-auto
              shadow-[0_0_80px_rgba(0,0,0,0.7),inset_0_1px_0_0_rgba(255,255,255,0.06)] animate-fadeIn"
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
