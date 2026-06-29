import { useState } from 'react';
import BrandKitPanel from './BrandKitPanel';
import {
  DP_BRAND, DP_COMPANY, DP_PRODUCTS, DP_CATEGORIES, DP_SALES_SOP,
  type DPProduct,
} from '../data/dreamparkLibrary';

type Section = 'brand' | 'product' | 'company' | 'sales';
type CanvasItem = { id: string; type: string; label: string; url: string };

interface Props {
  projectId: number;
  isLight?: boolean;
  hasUploadedPdf?: boolean;
  pdfText?: string;
  onAddToCanvas?: (item: CanvasItem) => void;
  onClose?: () => void;
}

const TABS: Array<{ key: Section; title: string; icon: string }> = [
  { key: 'brand', title: '品牌资产', icon: '🎨' },
  { key: 'product', title: '产品资料', icon: '📦' },
  { key: 'company', title: '公司资料', icon: '🏢' },
  { key: 'sales', title: '销售 SOP', icon: '📋' },
];

// 统一的"可拖拽 + 加入画布"封装:HTML5 DnD(主) + 按钮(退路)
function dragProps(item: CanvasItem) {
  return {
    draggable: true,
    onDragStart: (e: React.DragEvent) => {
      e.dataTransfer.setData('application/x-moyag-asset', JSON.stringify(item));
      e.dataTransfer.setData('text/plain', item.url);
      e.dataTransfer.effectAllowed = 'copy';
    },
  };
}

export default function LibraryPanel({ projectId, hasUploadedPdf, pdfText, onAddToCanvas, onClose }: Props) {
  const [section, setSection] = useState<Section>('product');
  const [cat, setCat] = useState<string>('全部');
  const [brandKit, setBrandKit] = useState(false);

  const add = (item: CanvasItem) => onAddToCanvas?.(item);
  const products = cat === '全部' ? DP_PRODUCTS : DP_PRODUCTS.filter(p => p.category === cat);

  return (
    <div className="library-inpanel flex h-full flex-col bg-transparent text-white">
      {/* 4 子-tab */}
      <div className="flex shrink-0 gap-1 border-b border-white/10 px-2 py-2">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => { setSection(t.key); setBrandKit(false); }}
            className={'flex-1 rounded-lg px-2 py-1.5 text-xs font-medium transition-colors ' +
              (section === t.key ? 'bg-orange-500/15 text-orange-300' : 'text-gray-400 hover:bg-white/5')}
          >
            <span className="mr-1">{t.icon}</span>{t.title}
          </button>
        ))}
      </div>

      {/* 内容区:切 tab 带淡入(丝滑切入) */}
      <div key={section} className="animate-fadeIn flex-1 overflow-y-auto px-3 py-3">
        {section === 'product' && (
          <>
            <div className="mb-2 flex flex-wrap gap-1.5">
              {['全部', ...DP_CATEGORIES].map(c => (
                <button key={c} onClick={() => setCat(c)}
                  className={'rounded-full border px-2.5 py-0.5 text-[11px] transition-colors ' +
                    (cat === c ? 'border-orange-400/50 bg-orange-500/15 text-orange-200' : 'border-white/10 text-gray-400 hover:text-white')}>
                  {c}
                </button>
              ))}
            </div>
            <p className="mb-2 text-[11px] text-gray-500">拖动产品图到画布,或点「+ 加入画布」</p>
            <div className="space-y-2.5">
              {products.map(p => <ProductCard key={p.id} p={p} onAdd={add} />)}
            </div>
          </>
        )}

        {section === 'brand' && (
          brandKit ? (
            <BrandKitPanel projectId={projectId} hasUploadedPdf={!!hasUploadedPdf} pdfText={pdfText} onClose={() => setBrandKit(false)} embedded />
          ) : (
            <div className="space-y-3">
              <div {...dragProps({ id: 'brand-hero', type: 'image', label: DP_BRAND.name_cn, url: DP_BRAND.hero })}
                className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/5">
                <img src={DP_BRAND.hero} alt={DP_BRAND.name_cn} className="h-36 w-full object-cover" />
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent p-3">
                  <div className="text-sm font-bold">{DP_BRAND.name_cn} · {DP_BRAND.name_en}</div>
                  <div className="text-[11px] text-gray-300">{DP_BRAND.slogan}</div>
                </div>
                <AddBtn onClick={() => add({ id: 'brand-hero', type: 'image', label: DP_BRAND.name_cn, url: DP_BRAND.hero })} />
              </div>
              <Field label="品牌理念">{DP_BRAND.philosophy}</Field>
              <div>
                <div className="mb-1 text-[11px] text-gray-500">品牌色板</div>
                <div className="flex gap-1.5">
                  {DP_BRAND.palette.map(c => (
                    <span key={c} title={c} className="h-7 w-7 rounded-lg border border-white/15" style={{ background: c }} />
                  ))}
                </div>
              </div>
              <Chips label="关键词" items={DP_BRAND.keywords} />
              <Chips label="产品系列" items={DP_BRAND.series} />
              <Chips label="资质认证" items={DP_BRAND.certs} />
              <button onClick={() => setBrandKit(true)}
                className="w-full rounded-xl border border-white/12 bg-white/5 py-2 text-xs text-gray-200 hover:bg-white/10">
                管理完整品牌套件 →
              </button>
            </div>
          )
        )}

        {section === 'company' && (
          <div className="space-y-3">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
              <div className="text-sm font-bold">{DP_COMPANY.name}</div>
              <div className="mb-2 text-[11px] text-gray-500">{DP_COMPANY.name_en}</div>
              <p className="text-xs leading-5 text-gray-300">{DP_COMPANY.intro}</p>
              <p className="mt-2 text-xs leading-5 text-gray-400">{DP_COMPANY.market}</p>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {DP_COMPANY.highlights.map(h => (
                <div key={h.title} className="rounded-xl border border-white/10 bg-white/[0.04] p-2.5">
                  <div className="text-lg">{h.icon}</div>
                  <div className="mt-1 text-xs font-semibold text-white">{h.title}</div>
                  <div className="mt-0.5 text-[11px] leading-4 text-gray-500">{h.desc}</div>
                </div>
              ))}
            </div>
            <div className="mb-1 text-[11px] text-gray-500">企业实拍(可拖到画布)</div>
            <div className="grid grid-cols-2 gap-2">
              {DP_COMPANY.gallery.map(g => (
                <div key={g.id} {...dragProps({ id: g.id, type: 'image', label: g.label, url: g.image })}
                  className="group relative overflow-hidden rounded-xl border border-white/10 bg-white/5">
                  <img src={g.image} alt={g.label} className="h-24 w-full object-cover" />
                  <div className="absolute inset-x-0 bottom-0 bg-black/60 px-2 py-1 text-[10px] text-gray-200">{g.label}</div>
                  <AddBtn onClick={() => add({ id: g.id, type: 'image', label: g.label, url: g.image })} />
                </div>
              ))}
            </div>
          </div>
        )}

        {section === 'sales' && (
          <div className="space-y-3">
            <Block title="销售流程">
              {DP_SALES_SOP.process.map(s => (
                <div key={s.step} className="rounded-lg border border-white/8 bg-white/[0.03] p-2">
                  <div className="text-xs font-semibold text-orange-200">{s.step}</div>
                  <div className="text-[11px] leading-4 text-gray-400">{s.desc}</div>
                </div>
              ))}
            </Block>
            <Block title="话术模板">
              {DP_SALES_SOP.scripts.map(s => (
                <div key={s.title} className="rounded-lg border border-white/8 bg-white/[0.03] p-2">
                  <div className="text-xs font-semibold text-white">{s.title}</div>
                  <div className="text-[11px] leading-4 text-gray-400">{s.text}</div>
                </div>
              ))}
            </Block>
            <Block title="常见异议">
              {DP_SALES_SOP.objections.map(o => (
                <div key={o.q} className="rounded-lg border border-white/8 bg-white/[0.03] p-2">
                  <div className="text-xs font-semibold text-rose-200">Q：{o.q}</div>
                  <div className="text-[11px] leading-4 text-gray-400">A：{o.a}</div>
                </div>
              ))}
            </Block>
          </div>
        )}
      </div>

      {onClose && (
        <div className="shrink-0 border-t border-white/10 px-3 py-2 text-right">
          <span className="text-[11px] text-gray-600">资料库 · 以 DreamPark 2026 目录为范例</span>
        </div>
      )}
    </div>
  );
}

function ProductCard({ p, onAdd }: { p: DPProduct; onAdd: (i: CanvasItem) => void }) {
  const item: CanvasItem = { id: p.id, type: 'image', label: p.name_cn, url: p.image };
  return (
    <div {...dragProps(item)}
      className="group relative flex gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-2.5 transition-colors hover:border-orange-400/40 hover:bg-white/[0.07]">
      <img src={p.image} alt={p.name_cn} className="h-20 w-20 shrink-0 rounded-xl object-cover" draggable={false} />
      <div className="min-w-0 flex-1">
        <div className="truncate text-xs font-semibold text-white">{p.name_cn}</div>
        <div className="truncate text-[10px] text-gray-500">{p.name_en}</div>
        <div className="mt-1 flex flex-wrap gap-1 text-[10px] text-gray-400">
          <span className="rounded bg-white/8 px-1.5 py-0.5">{p.model}</span>
          <span className="rounded bg-white/8 px-1.5 py-0.5">{p.temp}</span>
        </div>
        <ul className="mt-1 line-clamp-2 text-[10px] leading-4 text-gray-500">{p.features.slice(0, 2).join(' · ')}</ul>
      </div>
      <AddBtn onClick={() => onAdd(item)} />
    </div>
  );
}

function AddBtn({ onClick }: { onClick: () => void }) {
  return (
    <button onClick={onClick} title="加入画布"
      className="absolute right-2 top-2 rounded-lg border border-orange-400/40 bg-orange-500/20 px-1.5 py-0.5 text-[10px] text-orange-100 opacity-0 transition-opacity group-hover:opacity-100">
      + 画布
    </button>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.04] p-2.5">
      <div className="mb-0.5 text-[11px] text-gray-500">{label}</div>
      <div className="text-xs text-gray-200">{children}</div>
    </div>
  );
}

function Chips({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <div className="mb-1 text-[11px] text-gray-500">{label}</div>
      <div className="flex flex-wrap gap-1.5">
        {items.map(i => <span key={i} className="rounded-full border border-white/10 px-2 py-0.5 text-[11px] text-gray-300">{i}</span>)}
      </div>
    </div>
  );
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1.5 text-xs font-semibold tracking-wide text-gray-300">{title}</div>
      <div className="space-y-1.5">{children}</div>
    </div>
  );
}
