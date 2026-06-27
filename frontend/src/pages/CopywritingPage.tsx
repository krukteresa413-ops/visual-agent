import { useState } from 'react';
import { api } from '../api/client';

interface CopyItem {
  headline: string;
  body: string;
  cta: string;
  compliance?: Array<{ type: string; matched: string; suggestion: string }>;
  error?: string;
}

const STYLES = [
  { key: '专业权威', sub: '数据说话' },
  { key: '俏皮活泼', sub: '网感十足' },
  { key: '种草安利', sub: '真诚推荐' },
  { key: '情感共鸣', sub: '走心叙事' },
  { key: '专家背书', sub: '理性分析' },
];

const PLATFORMS = [
  { key: '小红书', icon: '📕', types: ['xiaohongshu_title', 'promo_copy', 'brand_slogan'] },
  { key: '抖音', icon: '🎵', types: ['douyin_voiceover', 'promo_copy', 'poster_headline'] },
  { key: '朋友圈', icon: '💬', types: ['promo_copy', 'brand_slogan', 'poster_headline'] },
  { key: '电商详情', icon: '🛒', types: ['ecommerce_selling_point', 'poster_headline', 'promo_copy'] },
  { key: '微博', icon: '📢', types: ['promo_copy', 'poster_headline', 'brand_slogan'] },
];

const TYPE_LABEL: Record<string, string> = {
  ecommerce_selling_point: '电商卖点', xiaohongshu_title: '小红书标题', douyin_voiceover: '抖音口播',
  poster_headline: '海报主标题', promo_copy: '活动促销', brand_slogan: '品牌 Slogan',
};

const FAV_KEY = 'moyag_copy_favorites';
const loadFavs = (): Array<{ id: string; label: string; headline: string; body: string; cta: string }> => {
  try { return JSON.parse(localStorage.getItem(FAV_KEY) || '[]'); } catch { return []; }
};

export default function CopywritingPage() {
  const [tab, setTab] = useState<'generate' | 'favorites'>('generate');
  const [productDesc, setProductDesc] = useState('');
  const [sellingPoints, setSellingPoints] = useState('');
  const [style, setStyle] = useState('种草安利');
  const [platform, setPlatform] = useState('小红书');
  const [copies, setCopies] = useState<Record<string, CopyItem> | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState('');
  const [favs, setFavs] = useState(loadFavs());

  const generate = async () => {
    if (!productDesc.trim()) return;
    setLoading(true);
    setCopies(null);
    try {
      const brief = {
        product_name: productDesc.trim().slice(0, 40),
        description: `${productDesc.trim()}\n文案风格:${style}\n目标平台:${platform}`,
        selling_points: sellingPoints.split(/[,，、\n]/).map((s) => s.trim()).filter(Boolean),
        style,
        platform,
      };
      const data = await api.copywriting.generate({ brief, copy_types: ['all'] });
      setCopies(data as Record<string, CopyItem>);
    } catch {
      setCopies({});
    } finally {
      setLoading(false);
    }
  };

  const copyText = async (text: string, key: string) => {
    try { await navigator.clipboard.writeText(text); setCopied(key); setTimeout(() => setCopied(''), 1500); } catch { /* noop */ }
  };

  const addFav = (label: string, c: CopyItem) => {
    const item = { id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`, label, headline: c.headline, body: c.body, cta: c.cta };
    const next = [item, ...favs].slice(0, 50);
    setFavs(next);
    localStorage.setItem(FAV_KEY, JSON.stringify(next));
  };
  const removeFav = (id: string) => {
    const next = favs.filter((f) => f.id !== id);
    setFavs(next);
    localStorage.setItem(FAV_KEY, JSON.stringify(next));
  };

  // 选出 3 版(优先按平台映射,回退到返回的前 3 种)
  const versionKeys = (() => {
    if (!copies) return [];
    const mapped = (PLATFORMS.find((p) => p.key === platform)?.types || []).filter((t) => copies[t] && !copies[t].error);
    const keys = mapped.length ? mapped : Object.keys(copies).filter((k) => !copies[k]?.error);
    return keys.slice(0, 3);
  })();

  return (
    <div className="liquid-page min-h-[calc(100vh-3.5rem)] px-6 py-7 text-white">
      <div className="mx-auto w-full max-w-6xl">
        {/* 标题 */}
        <div className="mb-4 flex items-start gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-orange-500/25 to-rose-500/20 text-lg">✍️</span>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">AI 营销文案助手</h1>
            <p className="mt-0.5 text-sm text-gray-400">输入产品 + 卖点,AI 生成多平台多风格营销文案,可一键复制与收藏</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-4 flex gap-2">
          {([['generate', '✍️ 生成文案'], ['favorites', `♥ 收藏夹${favs.length ? ` (${favs.length})` : ''}`]] as const).map(([k, label]) => (
            <button
              key={k}
              onClick={() => setTab(k)}
              className={'rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ' + (tab === k ? 'bg-white/[0.1] text-white' : 'text-gray-400 hover:text-white hover:bg-white/[0.05]')}
            >
              {label}
            </button>
          ))}
        </div>

        {tab === 'favorites' ? (
          <div className="rounded-3xl border border-white/[0.12] bg-white/[0.04] p-5">
            {favs.length === 0 ? (
              <div className="py-16 text-center text-sm text-gray-500">还没有收藏的文案 · 生成后点 ♥ 收藏</div>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {favs.map((f) => (
                  <div key={f.id} className="rounded-2xl border border-white/[0.1] bg-white/[0.04] p-4">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="rounded-full bg-white/[0.08] px-2 py-0.5 text-[10px] text-gray-300">{f.label}</span>
                      <button onClick={() => removeFav(f.id)} className="text-[11px] text-gray-500 hover:text-rose-400">移除</button>
                    </div>
                    <p className="text-sm font-medium text-white">{f.headline}</p>
                    <p className="mt-1 text-xs leading-relaxed text-gray-400">{f.body}</p>
                    {f.cta && <p className="mt-1 text-xs text-orange-300">{f.cta}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {/* 左:表单 */}
            <div className="space-y-4 rounded-3xl border border-white/[0.12] bg-white/[0.04] p-5">
              <Field label="产品描述" required>
                <textarea
                  value={productDesc}
                  onChange={(e) => setProductDesc(e.target.value)}
                  placeholder="例如:国产香氛品牌,木质调,目标 25-35 岁都市女性,主打东方意境"
                  className={inputCls + ' min-h-[96px] resize-y py-2.5'}
                />
              </Field>
              <Field label="核心卖点(可选)">
                <input value={sellingPoints} onChange={(e) => setSellingPoints(e.target.value)} placeholder="天然植物精油、东方木质调、持久留香 8 小时" className={inputCls} />
              </Field>

              <div>
                <div className="mb-1.5 text-xs font-medium text-gray-400">风格</div>
                <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
                  {STYLES.map((s) => (
                    <button
                      key={s.key}
                      onClick={() => setStyle(s.key)}
                      className={'rounded-xl border px-2 py-2 text-center transition-all ' + (style === s.key ? 'border-orange-400/50 bg-orange-500/[0.12]' : 'border-white/[0.1] bg-white/[0.03] hover:border-white/20')}
                    >
                      <div className="text-xs font-semibold text-white">{s.key}</div>
                      <div className="text-[10px] text-gray-500">{s.sub}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <div className="mb-1.5 text-xs font-medium text-gray-400">平台</div>
                <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
                  {PLATFORMS.map((p) => (
                    <button
                      key={p.key}
                      onClick={() => setPlatform(p.key)}
                      className={'flex flex-col items-center gap-1 rounded-xl border px-2 py-2.5 transition-all ' + (platform === p.key ? 'border-orange-400/50 bg-orange-500/[0.12]' : 'border-white/[0.1] bg-white/[0.03] hover:border-white/20')}
                    >
                      <span className="text-base">{p.icon}</span>
                      <span className="text-[11px] font-medium text-gray-200">{p.key}</span>
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={generate}
                disabled={loading || !productDesc.trim()}
                className="w-full rounded-xl bg-gradient-to-r from-orange-500 to-rose-500 py-3 text-sm font-semibold text-white transition-transform hover:scale-[1.01] disabled:opacity-50"
              >
                {loading ? '生成中…' : '✦ 生成 3 版文案'}
              </button>
              <p className="text-center text-[11px] text-gray-500">每次消耗 50 积分 · 严格符合广告法</p>
            </div>

            {/* 右:结果 */}
            <div className="rounded-3xl border border-white/[0.12] bg-white/[0.04] p-5">
              {!copies && !loading ? (
                <div className="grid h-full min-h-[300px] place-items-center text-center">
                  <div>
                    <div className="mx-auto mb-3 grid size-14 place-items-center rounded-2xl border border-white/[0.1] bg-white/[0.04] text-2xl text-gray-500">📖</div>
                    <p className="text-sm text-gray-400">填写产品信息后点击生成</p>
                    <p className="mt-1 text-xs text-gray-600">AI 将产出 3 版不同角度的营销文案</p>
                  </div>
                </div>
              ) : loading ? (
                <div className="space-y-3">
                  {[0, 1, 2].map((i) => <div key={i} className="h-28 animate-pulse rounded-2xl bg-white/[0.05]" />)}
                </div>
              ) : versionKeys.length === 0 ? (
                <div className="grid h-full min-h-[300px] place-items-center text-center text-sm text-gray-500">生成失败,请调整产品描述后重试</div>
              ) : (
                <div className="space-y-3">
                  {versionKeys.map((k, idx) => {
                    const c = copies![k];
                    const label = `版本 ${idx + 1} · ${TYPE_LABEL[k] || k}`;
                    return (
                      <div key={k} className="rounded-2xl border border-white/[0.1] bg-white/[0.04] p-4">
                        <div className="mb-2 flex items-center justify-between">
                          <span className="rounded-full bg-orange-500/15 px-2 py-0.5 text-[10px] text-orange-200">{label}</span>
                          <div className="flex gap-2">
                            <button onClick={() => copyText(`${c.headline}\n${c.body}\n${c.cta || ''}`.trim(), k)} className="text-[11px] text-gray-400 hover:text-white">{copied === k ? '已复制' : '复制'}</button>
                            <button onClick={() => addFav(label, c)} className="text-[11px] text-gray-400 hover:text-orange-300">♥ 收藏</button>
                          </div>
                        </div>
                        <p className="text-sm font-semibold text-white">{c.headline}</p>
                        <p className="mt-1 text-xs leading-relaxed text-gray-300">{c.body}</p>
                        {c.cta && <p className="mt-1.5 text-xs text-orange-300">{c.cta}</p>}
                        {c.compliance && c.compliance.length > 0 && (
                          <div className="mt-2 rounded-lg border border-rose-400/20 bg-rose-500/[0.06] p-2">
                            <span className="text-[10px] text-rose-300">⚠ 合规提醒</span>
                            {c.compliance.map((w, i) => <p key={i} className="mt-0.5 text-[10px] text-rose-300/80">「{w.matched}」— {w.suggestion}</p>)}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const inputCls = 'w-full rounded-lg border border-white/[0.1] bg-white/[0.04] px-3 py-2 text-sm text-white placeholder:text-gray-600 outline-none transition-colors focus:border-orange-400/40';

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-gray-400">
        {label}{required && <span className="ml-0.5 text-rose-400">*</span>}
      </label>
      {children}
    </div>
  );
}
