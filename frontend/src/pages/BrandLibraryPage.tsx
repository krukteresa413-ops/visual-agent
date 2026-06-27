import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

interface Brand {
  id: number;
  tenant_id?: number | null;
  project_id?: number | null;
  is_canonical?: boolean;
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
  updated_at?: string | null;
}

const KIT_CARDS = [
  { icon: '✦', label: 'Logo', desc: '品牌标识' },
  { icon: 'A', label: '字体', desc: '品牌字体规范' },
  { icon: '◐', label: '颜色', desc: '标准色彩系统' },
  { icon: '▤', label: '设计指南', desc: '版式与使用规范' },
  { icon: '◇', label: '图像', desc: '产品与视觉素材' },
  { icon: '⛉', label: '品牌指南', desc: 'VI 完整手册' },
];

type FormState = {
  name: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  font_style: string;
  tone_of_voice: string;
  tagline: string;
  visual_keywords: string; // 逗号分隔
  forbidden_words: string; // 逗号分隔
};

const EMPTY_FORM: FormState = {
  name: '', primary_color: '#FB923C', secondary_color: '#1F2937', accent_color: '#F43F5E',
  font_style: '', tone_of_voice: '', tagline: '', visual_keywords: '', forbidden_words: '',
};

const splitTags = (s: string) => s.split(/[,，\n]/).map((x) => x.trim()).filter(Boolean);

export default function BrandLibraryPage() {
  const navigate = useNavigate();
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Brand | null>(null);
  const [form, setForm] = useState<FormState>({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);

  const selected = useMemo(() => brands.find((b) => b.id === selectedId) || null, [brands, selectedId]);

  const load = (keepId?: number) => {
    setLoading(true);
    api.brand.list()
      .then((d: { brands?: Brand[] }) => {
        const list = d.brands || [];
        setBrands(list);
        setSelectedId((cur) => keepId ?? (cur && list.some((b) => b.id === cur) ? cur : list[0]?.id ?? null));
      })
      .catch(() => setBrands([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const openNew = () => { setEditing(null); setForm({ ...EMPTY_FORM }); setDialogOpen(true); };
  const openEdit = (b: Brand) => {
    setEditing(b);
    setForm({
      name: b.name || '',
      primary_color: b.primary_color || '#FB923C',
      secondary_color: b.secondary_color || '#1F2937',
      accent_color: b.accent_color || '#F43F5E',
      font_style: b.font_style || '',
      tone_of_voice: b.tone_of_voice || '',
      tagline: b.tagline || '',
      visual_keywords: (b.visual_keywords || []).join('，'),
      forbidden_words: (b.forbidden_words || []).join('，'),
    });
    setDialogOpen(true);
  };

  const save = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    const payload = {
      name: form.name.trim(),
      primary_color: form.primary_color,
      secondary_color: form.secondary_color,
      accent_color: form.accent_color,
      font_style: form.font_style || null,
      tone_of_voice: form.tone_of_voice || null,
      tagline: form.tagline || null,
      visual_keywords: splitTags(form.visual_keywords),
      forbidden_words: splitTags(form.forbidden_words),
    };
    try {
      if (editing) {
        const updated: Brand = await api.brand.update(editing.id, payload);
        setDialogOpen(false);
        load(updated.id);
      } else {
        const created: Brand = await api.brand.createManual(payload);
        setDialogOpen(false);
        load(created.id);
      }
    } catch {
      /* 保留弹窗，避免数据丢失 */
    } finally {
      setSaving(false);
    }
  };

  const remove = async (b: Brand) => {
    if (!window.confirm(`删除品牌「${b.name}」？此操作不可撤销。`)) return;
    try {
      await api.brand.remove(b.id);
      load();
    } catch { /* 忽略 */ }
  };

  const useForNewProject = async (b: Brand) => {
    try {
      const p = await api.projects.create(`${b.name} · 新项目`, '');
      navigate(`/generate/${p.id}`);
    } catch { navigate('/'); }
  };

  const swatches = selected
    ? [
        { label: '主色', value: selected.primary_color },
        { label: '辅色', value: selected.secondary_color },
        { label: '强调色', value: selected.accent_color },
      ].filter((s) => s.value)
    : [];

  return (
    <div className="min-h-[calc(100vh-3.5rem)] text-white">
      <div className="mx-auto flex w-full max-w-6xl gap-0 md:gap-4 px-2 md:px-6 py-6">
        {/* 左:品牌列表 */}
        <aside className="flex w-44 shrink-0 flex-col md:w-60">
          <div className="mb-2 flex items-center justify-between px-1">
            <span className="text-sm font-semibold text-white">品牌库</span>
            <span className="rounded-full bg-white/[0.08] px-2 py-0.5 text-[10px] text-gray-400">{brands.length}</span>
          </div>
          <button
            onClick={openNew}
            className="mb-3 inline-flex items-center justify-center gap-1.5 rounded-lg bg-gradient-to-r from-orange-500 to-rose-500 px-3 py-2 text-sm font-medium text-white transition-transform hover:scale-[1.02]"
          >
            <svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14" /></svg>
            新建品牌
          </button>
          <div className="space-y-1 overflow-y-auto pr-1">
            {loading ? (
              [0, 1, 2, 3].map((i) => <div key={i} className="h-12 animate-pulse rounded-lg bg-white/[0.05]" />)
            ) : brands.length === 0 ? (
              <div className="py-8 text-center text-xs text-gray-500">暂无品牌，点击新建</div>
            ) : brands.map((b) => (
              <button
                key={b.id}
                onClick={() => setSelectedId(b.id)}
                className={
                  'flex w-full items-center gap-2 rounded-lg p-2 text-left transition-colors ' +
                  (selectedId === b.id ? 'bg-white/[0.1]' : 'hover:bg-white/[0.05]')
                }
              >
                <span
                  className="grid size-8 shrink-0 place-items-center rounded-lg text-xs font-bold text-white"
                  style={{ background: b.primary_color || '#FB923C' }}
                >
                  {b.name.slice(0, 1)}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium text-white">{b.name}</span>
                  <span className="block text-[10px] text-gray-500">
                    {b.is_canonical ? '主品牌 · ' : ''}{(b.visual_keywords?.length || 0)} 关键词
                  </span>
                </span>
              </button>
            ))}
          </div>
        </aside>

        {/* 右:品牌详情 */}
        <div className="min-w-0 flex-1">
          {selected ? (
            <>
              <section className="overflow-hidden rounded-3xl border border-white/[0.12] bg-gradient-to-br from-white/[0.1] via-white/[0.05] to-white/[0.02] p-5">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="grid size-14 place-items-center rounded-2xl text-xl font-bold text-white" style={{ background: selected.primary_color || '#FB923C' }}>
                      {selected.name.slice(0, 1)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-xl font-bold text-white">{selected.name}</h2>
                        {selected.is_canonical && <span className="rounded-full border border-orange-400/30 bg-orange-500/10 px-2 py-0.5 text-[10px] text-orange-200">主品牌</span>}
                      </div>
                      <p className="mt-1 text-sm text-gray-400">{selected.tagline || selected.tone_of_voice || '品牌记忆 · 后续项目自动复用'}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => openEdit(selected)} className="rounded-lg border border-white/[0.12] bg-white/[0.05] px-3 py-2 text-xs text-gray-300 transition-colors hover:text-white">编辑</button>
                    <button onClick={() => remove(selected)} className="rounded-lg border border-white/[0.12] bg-white/[0.05] px-3 py-2 text-xs text-rose-300 transition-colors hover:text-rose-200">删除</button>
                    <button onClick={() => useForNewProject(selected)} className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-orange-500 to-rose-500 px-3 py-2 text-xs font-medium text-white transition-transform hover:scale-[1.03]">用此品牌新建项目</button>
                  </div>
                </div>
              </section>

              <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {KIT_CARDS.map((c) => (
                  <div key={c.label} className="rounded-2xl border border-white/[0.1] bg-white/[0.04] p-4 transition-all duration-300 hover:-translate-y-0.5 hover:border-orange-400/40 hover:bg-white/[0.06]">
                    <div className="mb-3 grid size-10 place-items-center rounded-xl border border-orange-400/20 bg-orange-500/10 text-lg text-orange-200">{c.icon}</div>
                    <div className="text-sm font-semibold text-white">{c.label}</div>
                    <div className="text-xs text-gray-500">{c.desc}</div>
                  </div>
                ))}
              </div>

              <div className="mt-5 grid gap-4 md:grid-cols-2">
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
                <InfoCard title="品牌字体 / 语调">
                  <div className="space-y-1 text-sm text-gray-200">
                    <div>字体：{selected.font_style || <span className="text-gray-600">—</span>}</div>
                    <div>语调：{selected.tone_of_voice || <span className="text-gray-600">—</span>}</div>
                  </div>
                </InfoCard>
                <InfoCard title="视觉关键词">
                  {selected.visual_keywords?.length ? (
                    <div className="flex flex-wrap gap-1.5">
                      {selected.visual_keywords.map((k, i) => <span key={i} className="rounded-full bg-white/[0.08] px-2.5 py-0.5 text-xs text-gray-300">{k}</span>)}
                    </div>
                  ) : <Empty />}
                </InfoCard>
                <InfoCard title="禁用词 / 禁用风格">
                  {selected.forbidden_words?.length ? (
                    <div className="flex flex-wrap gap-1.5">
                      {selected.forbidden_words.map((w, i) => <span key={i} className="rounded-full border border-rose-400/30 px-2.5 py-0.5 text-xs text-rose-300">{w}</span>)}
                    </div>
                  ) : <Empty />}
                </InfoCard>
              </div>
            </>
          ) : !loading ? (
            <div className="grid h-full place-items-center rounded-3xl border border-dashed border-white/[0.14] bg-white/[0.04] px-6 py-16 text-center">
              <div>
                <div className="mx-auto mb-4 grid h-16 w-16 place-items-center rounded-3xl border border-orange-400/20 bg-orange-500/10 text-3xl">✦</div>
                <h3 className="text-base font-semibold">开始建立你的品牌记忆</h3>
                <p className="mx-auto mt-2 max-w-md text-xs leading-5 text-gray-500">新建品牌后，后续项目自动复用 Logo、色彩、字体与卖点，保持多资产视觉一致性。</p>
                <button onClick={openNew} className="mt-5 rounded-lg bg-white px-4 py-2 text-xs font-semibold text-black transition-transform hover:scale-105">新建品牌</button>
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {/* 新建/编辑弹窗 */}
      {dialogOpen && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4 backdrop-blur-sm" onClick={() => !saving && setDialogOpen(false)}>
          <div className="max-h-[88vh] w-full max-w-lg overflow-y-auto rounded-3xl border border-white/[0.14] bg-[#15161c] p-5 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-white">{editing ? '编辑品牌' : '新建品牌'}</h3>
            <p className="mt-1 text-xs text-gray-500">品牌记忆将用于保持多项目视觉一致性</p>
            <div className="mt-4 space-y-3">
              <Field label="品牌名称">
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="例如：栖岚" className={inputCls} />
              </Field>
              <Field label="标准色彩">
                <div className="flex gap-4">
                  {(['primary_color', 'secondary_color', 'accent_color'] as const).map((k, i) => (
                    <label key={k} className="flex flex-col items-center gap-1">
                      <input type="color" value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} className="size-9 cursor-pointer rounded-lg border border-white/15 bg-transparent" />
                      <span className="text-[10px] text-gray-500">{['主色', '辅色', '强调色'][i]}</span>
                    </label>
                  ))}
                </div>
              </Field>
              <Field label="品牌字体">
                <input value={form.font_style} onChange={(e) => setForm({ ...form, font_style: e.target.value })} placeholder="例如：思源黑体 Heavy + 思源宋体" className={inputCls} />
              </Field>
              <Field label="品牌语调">
                <input value={form.tone_of_voice} onChange={(e) => setForm({ ...form, tone_of_voice: e.target.value })} placeholder="例如：专业、可靠、有温度" className={inputCls} />
              </Field>
              <Field label="品牌标语 / Tagline">
                <input value={form.tagline} onChange={(e) => setForm({ ...form, tagline: e.target.value })} placeholder="一句话品牌主张" className={inputCls} />
              </Field>
              <Field label="视觉关键词（逗号分隔）">
                <input value={form.visual_keywords} onChange={(e) => setForm({ ...form, visual_keywords: e.target.value })} placeholder="极简, 科技, 高级感" className={inputCls} />
              </Field>
              <Field label="禁用词 / 禁用风格（逗号分隔）">
                <input value={form.forbidden_words} onChange={(e) => setForm({ ...form, forbidden_words: e.target.value })} placeholder="廉价, 花哨" className={inputCls} />
              </Field>
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <button onClick={() => setDialogOpen(false)} disabled={saving} className="rounded-lg border border-white/[0.12] px-4 py-2 text-sm text-gray-300 disabled:opacity-50">取消</button>
              <button onClick={save} disabled={saving || !form.name.trim()} className="rounded-lg bg-gradient-to-r from-orange-500 to-rose-500 px-4 py-2 text-sm font-medium text-white transition-transform hover:scale-[1.03] disabled:opacity-50">{saving ? '保存中…' : '保存'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const inputCls = 'h-9 w-full rounded-lg border border-white/[0.1] bg-white/[0.04] px-3 text-sm text-white placeholder:text-gray-600 outline-none transition-colors focus:border-orange-400/40';

function InfoCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-white/[0.1] bg-white/[0.04] p-4">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">{title}</div>
      <div className="text-sm">{children}</div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-gray-400">{label}</label>
      {children}
    </div>
  );
}

function Empty() {
  return <span className="text-sm text-gray-600">—</span>;
}
