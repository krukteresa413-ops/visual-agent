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
  onUseStyle?: (item: InspirationItem) => void;
}

const CATEGORY_LABELS: Record<string, string> = {
  poster: '海报',
  app: 'APP',
  illustration: '插画',
  ops: '运营',
  ip: 'IP',
};

export default function InspirationPanel({ onClose, onUseStyle }: Props) {
  const [categories, setCategories] = useState<CategoryTree>({});
  const [items, setItems] = useState<InspirationItem[]>([]);
  const [activeCat, setActiveCat] = useState<string>('');
  const [activeSub, setActiveSub] = useState<string>('');
  const [selected, setSelected] = useState<InspirationItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/v1/inspirations/categories')
      .then(r => r.json())
      .then(data => {
        setCategories(data);
        const firstCat = Object.keys(data).filter(k => k !== 'test')[0];
        if (firstCat) setActiveCat(firstCat);
      });
  }, []);

  useEffect(() => {
    if (!activeCat) return;
    setLoading(true);
    const params = new URLSearchParams({ category: activeCat, limit: '50' });
    fetch(`/api/v1/inspirations?${params}`)
      .then(r => r.json())
      .then(data => {
        setItems(data);
        setLoading(false);
        setSelected(null);
        setActiveSub('');
      });
  }, [activeCat]);

  const filteredItems = activeSub
    ? items.filter(i => i.sub_category === activeSub)
    : items;

  const subs = categories[activeCat] || [];

  // Count items per sub-category
  const subCounts: Record<string, number> = {};
  items.forEach(i => {
    subCounts[i.sub_category] = (subCounts[i.sub_category] || 0) + 1;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fadeIn">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      {/* Panel — light theme matching target style */}
      <div
        className="relative w-full max-w-5xl max-h-[90vh] bg-white rounded-2xl shadow-[0_24px_48px_rgba(0,0,0,0.15)] flex flex-col overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-8 py-5 shrink-0">
          <div className="flex items-center gap-2.5">
            <span className="text-2xl">💡</span>
            <h2 className="text-xl font-bold text-[#1F1F1F]">灵感库</h2>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-[#666] hover:text-[#333] hover:bg-[#F5F5F5] transition-colors text-lg leading-none"
          >
            ✕
          </button>
        </div>

        {/* Category tabs — orange selected style */}
        <div className="flex gap-3 px-8 pb-4 shrink-0">
          {Object.keys(categories).filter(k => k !== 'test').map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCat(cat)}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                activeCat === cat
                  ? 'bg-white text-[#FF8C42] border-2 border-[#FF8C42]'
                  : 'text-[#666] hover:text-[#333] hover:bg-[#F5F5F5] border-2 border-transparent'
              }`}
            >
              {CATEGORY_LABELS[cat] || cat}
            </button>
          ))}
        </div>

        {/* Sub-category filter tags with counts */}
        {subs.length > 1 && (
          <div className="flex gap-2 px-8 pb-4 shrink-0 flex-wrap">
            <button
              onClick={() => setActiveSub('')}
              className={`px-3.5 py-1.5 rounded-lg text-xs transition-all border ${
                !activeSub
                  ? 'bg-[#FAFAFA] border-[#E5E5E5] text-[#333]'
                  : 'bg-white border-[#EBEBEB] text-[#666] hover:text-[#333] hover:border-[#D0D0D0]'
              }`}
            >
              全部({items.length})
            </button>
            {subs.map(sub => (
              <button
                key={sub}
                onClick={() => setActiveSub(sub)}
                className={`px-3.5 py-1.5 rounded-lg text-xs whitespace-nowrap transition-all border ${
                  activeSub === sub
                    ? 'bg-[#FAFAFA] border-[#E5E5E5] text-[#333]'
                    : 'bg-white border-[#EBEBEB] text-[#666] hover:text-[#333] hover:border-[#D0D0D0]'
                }`}
              >
                {sub}({subCounts[sub] || 0})
              </button>
            ))}
          </div>
        )}

        {/* Content area */}
        <div className="flex-1 overflow-y-auto px-8 pb-6">
          {loading ? (
            <div className="flex items-center justify-center h-40 text-[#999] text-sm">加载中...</div>
          ) : filteredItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-60 gap-4">
              <div className="w-24 h-24 rounded-2xl bg-[#F5F5F5] flex items-center justify-center">
                <span className="text-4xl">🖼️</span>
              </div>
              <p className="text-[#999] text-sm">暂无灵感</p>
            </div>
          ) : (
            <div className="grid gap-5" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
              {filteredItems.map(item => (
                <button
                  key={item.id}
                  onClick={() => setSelected(item)}
                  className={`relative group rounded-2xl overflow-hidden transition-all duration-200 ${
                    selected?.id === item.id
                      ? 'ring-2 ring-[#FF8C42] shadow-[0_0_20px_rgba(255,140,66,0.2)]'
                      : 'shadow-[0_2px_8px_rgba(0,0,0,0.08)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.12)] hover:-translate-y-0.5'
                  }`}
                  style={{ aspectRatio: '2/3' }}
                >
                  {/* Placeholder gradient */}
                  <div className="absolute inset-0 bg-gradient-to-br from-[#F0F0F0] to-[#E8E8E8]" />
                  {/* Hover overlay with prompt text */}
                  <div className="absolute inset-0 flex items-center justify-center p-3 opacity-0 group-hover:opacity-100 transition-opacity bg-black/50">
                    <span className="text-white text-xs text-center line-clamp-4 leading-relaxed">
                      {item.prompt_template.slice(0, 120)}...
                    </span>
                  </div>
                  {/* Sub-category badge — top left */}
                  <div className="absolute top-3 left-3 px-2.5 py-1 rounded-md text-[11px] bg-white/85 backdrop-blur-sm text-[#666]">
                    {item.sub_category}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Detail panel — bottom */}
        {selected && (
          <div className="border-t border-[#EBEBEB] px-8 py-4 shrink-0 bg-[#FAFAFA]">
            <div className="flex items-start justify-between mb-2">
              <div>
                <span className="text-xs text-[#666]">{selected.category} / {selected.sub_category}</span>
                <span className="ml-2 text-xs text-[#999]">{selected.aspect_ratio}</span>
              </div>
              <button onClick={() => setSelected(null)} className="text-[#999] hover:text-[#333] text-sm">✕</button>
            </div>
            <p className="text-[#444] text-sm leading-relaxed mb-3 max-h-24 overflow-y-auto">
              {selected.prompt_template}
            </p>
            {onUseStyle && (
              <button
                onClick={() => onUseStyle(selected)}
                className="w-full py-2.5 rounded-xl bg-[#FF8C42] text-white text-sm font-medium hover:bg-[#FF7A30] transition-colors"
              >
                用这个风格生成 →
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
