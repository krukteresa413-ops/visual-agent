import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

// 与后端 /library/brand(canonical 品牌)对齐的真实字段
interface Brand {
  id: number;
  tenant_id?: number;
  name: string;
  primary_color?: string | null;
  secondary_color?: string | null;
  accent_color?: string | null;
  font_style?: string | null;
  tone_of_voice?: string | null;
  visual_keywords?: string[];
  forbidden_words?: string[];
  logo_url?: string | null;
  tagline?: string | null;
}

const KIT_CARDS = [
  { icon: '✦', label: 'Logo', desc: '品牌标识' },
  { icon: 'A', label: '字体', desc: '品牌字体规范' },
  { icon: '◐', label: '颜色', desc: '标准色彩系统' },
  { icon: '▤', label: '设计指南', desc: '版式与使用规范' },
  { icon: '◇', label: '图像', desc: '产品与视觉素材' },
  { icon: '⛉', label: '品牌指南', desc: 'VI 完整手册' },
];

export default function BrandLibraryPage() {
  const navigate = useNavigate();
  const [brand, setBrand] = useState<Brand | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    api.library.brand()
      .then((d: unknown) => {
        if (!alive) return;
        const b = d as Brand | { brand: null } | null;
        setBrand(b && 'name' in (b as Brand) ? (b as Brand) : null);
      })
      .catch(() => alive && setBrand(null))
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, []);

  const useForNewProject = async () => {
    try {
      const p = await api.projects.create(brand ? `${brand.name} · 新项目` : '未命名项目', '');
      navigate(`/generate/${p.id}`);
    } catch {
      navigate('/');
    }
  };

  const swatches = brand
    ? [
        { label: '主色', value: brand.primary_color },
        { label: '辅色', value: brand.secondary_color },
        { label: '强调色', value: brand.accent_color },
      ].filter((s) => s.value)
    : [];

  return (
    <div className="min-h-[60vh] px-6 py-8 text-white">
      <div className="mx-auto w-full max-w-5xl">
        {/* 标题区 */}
        <div className="mb-6">
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-1 text-[11px] font-medium tracking-[0.18em] text-orange-200/90 uppercase">
            Brand Memory
          </div>
          <h1 className="text-2xl font-bold tracking-tight md:text-3xl">品牌库</h1>
          <p className="mt-1 text-sm text-gray-400">品牌记忆 · 后续项目自动复用 Logo、色彩、字体与卖点，保持多资产视觉一致性</p>
        </div>

        {loading ? (
          <div className="space-y-4">
            <div className="h-28 animate-pulse rounded-3xl bg-white/[0.06]" />
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {[0, 1, 2, 3, 4, 5].map((i) => <div key={i} className="h-24 animate-pulse rounded-2xl bg-white/[0.05]" />)}
            </div>
          </div>
        ) : brand ? (
          <>
            {/* 品牌主卡 */}
            <section className="overflow-hidden rounded-3xl border border-white/[0.12] bg-gradient-to-br from-white/[0.1] via-white/[0.05] to-white/[0.02] p-5 shadow-[0_24px_70px_rgba(0,0,0,0.35)]">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div
                    className="grid size-14 place-items-center rounded-2xl text-xl font-bold text-white shadow-inner"
                    style={{ background: brand.primary_color || '#FB923C' }}
                  >
                    {brand.name.slice(0, 1)}
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white">{brand.name}</h2>
                    <p className="mt-1 text-sm text-gray-400">{brand.tagline || brand.tone_of_voice || '品牌记忆 · 后续项目自动复用'}</p>
                  </div>
                </div>
                <button
                  onClick={useForNewProject}
                  className="inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-gradient-to-r from-orange-500 to-rose-500 px-3 py-2 text-sm font-medium text-white transition-transform hover:scale-[1.03]"
                >
                  <svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14" /></svg>
                  用此品牌新建项目
                </button>
              </div>
            </section>

            {/* 品牌套件卡 */}
            <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {KIT_CARDS.map((c) => (
                <div key={c.label} className="rounded-2xl border border-white/[0.1] bg-white/[0.04] p-4 transition-all duration-300 hover:-translate-y-0.5 hover:border-orange-400/40 hover:bg-white/[0.06]">
                  <div className="mb-3 grid size-10 place-items-center rounded-xl border border-orange-400/20 bg-orange-500/10 text-lg text-orange-200">{c.icon}</div>
                  <div className="text-sm font-semibold text-white">{c.label}</div>
                  <div className="text-xs text-gray-500">{c.desc}</div>
                </div>
              ))}
            </div>

            {/* 详情:色彩 / 语调 / 禁用词 / 关键词 */}
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <InfoCard title="标准色彩">
                {swatches.length ? (
                  <div className="flex flex-wrap gap-3">
                    {swatches.map((s) => (
                      <div key={s.label} className="text-center">
                        <div className="size-12 rounded-xl border border-white/15" style={{ background: s.value as string }} />
                        <div className="mt-1 font-mono text-[10px] text-gray-500">{s.value}</div>
                        <div className="text-[10px] text-gray-600">{s.label}</div>
                      </div>
                    ))}
                  </div>
                ) : <Empty />}
              </InfoCard>

              <InfoCard title="品牌语调">
                {brand.tone_of_voice ? <p className="text-sm leading-6 text-gray-200">{brand.tone_of_voice}</p> : <Empty />}
              </InfoCard>

              <InfoCard title="视觉关键词">
                {brand.visual_keywords?.length ? (
                  <div className="flex flex-wrap gap-1.5">
                    {brand.visual_keywords.map((k, i) => (
                      <span key={i} className="rounded-full bg-white/[0.08] px-2.5 py-0.5 text-xs text-gray-300">{k}</span>
                    ))}
                  </div>
                ) : <Empty />}
              </InfoCard>

              <InfoCard title="禁用词 / 禁用风格">
                {brand.forbidden_words?.length ? (
                  <div className="flex flex-wrap gap-1.5">
                    {brand.forbidden_words.map((w, i) => (
                      <span key={i} className="rounded-full border border-rose-400/30 px-2.5 py-0.5 text-xs text-rose-300">{w}</span>
                    ))}
                  </div>
                ) : <Empty />}
              </InfoCard>
            </div>
          </>
        ) : (
          /* 空状态 */
          <div className="rounded-3xl border border-dashed border-white/[0.14] bg-white/[0.04] px-6 py-14 text-center">
            <div className="mx-auto mb-4 grid h-16 w-16 place-items-center rounded-3xl border border-orange-400/20 bg-orange-500/10 text-3xl">✦</div>
            <h3 className="text-base font-semibold">开始建立你的品牌记忆</h3>
            <p className="mx-auto mt-2 max-w-md text-xs leading-5 text-gray-500">
              在项目中上传品牌手册或产品资料,Agent 会自动提取 Logo、色彩、字体与关键词写入品牌记忆,后续项目自动复用,保持多资产视觉一致性。
            </p>
            <button onClick={useForNewProject} className="mt-5 rounded-lg bg-white px-4 py-2 text-xs font-semibold text-black transition-transform hover:scale-105">新建项目并提取品牌</button>
          </div>
        )}
      </div>
    </div>
  );
}

function InfoCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-white/[0.1] bg-white/[0.04] p-4">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">{title}</div>
      <div className="text-sm">{children}</div>
    </div>
  );
}

function Empty() {
  return <span className="text-sm text-gray-600">—</span>;
}
