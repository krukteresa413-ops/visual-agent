import { useState } from 'react';
import BrandKitPanel from './BrandKitPanel';

interface Props {
  projectId: number;
  hasUploadedPdf: boolean;
  pdfText?: string;
  onClose: () => void;
}

type LibrarySection = 'brand' | 'product' | 'company' | 'sales';

const SECTIONS: Array<{ key: LibrarySection; title: string; desc: string; icon: string; action: string }> = [
  { key: 'brand', title: '品牌资产', desc: 'Logo / 色板 / 字体 / 关键词', icon: '🎨', action: '打开品牌资产' },
  { key: 'product', title: '产品资料', desc: '规格、卖点、目标用户', icon: '📦', action: '整理产品资料' },
  { key: 'company', title: '公司资料', desc: '企业介绍、资质、案例', icon: '🏢', action: '查看资料状态' },
  { key: 'sales', title: '销售 SOP', desc: '话术、流程、常见异议', icon: '📋', action: '维护销售流程' },
];

export default function LibraryPanel({ projectId, hasUploadedPdf, pdfText, onClose }: Props) {
  const [activeSection, setActiveSection] = useState<LibrarySection | null>(null);

  const activeMeta = activeSection ? SECTIONS.find(item => item.key === activeSection) : null;

  return (
    <div data-library-panel data-library-gallery className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-xl px-4 py-8 animate-fadeIn" onClick={onClose}>
      <section className="mx-auto w-full max-w-5xl rounded-[28px] border border-white/[0.14] bg-gradient-to-br from-white/[0.13] via-white/[0.07] to-white/[0.03] p-5 shadow-[0_30px_100px_rgba(0,0,0,0.55),inset_0_1px_0_rgba(255,255,255,0.16)]" onClick={event => event.stopPropagation()}>
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-1 text-[11px] font-medium tracking-[0.18em] text-orange-200/90 uppercase">
              Library Gallery
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white">资料陈列柜</h2>
            <p className="mt-1 text-sm text-gray-400">品牌、产品、公司与销售资料集中陈列 · 品牌资产内置完整品牌套件</p>
          </div>
          <button onClick={onClose} className="rounded-full border border-white/[0.12] bg-white/[0.05] px-3 py-2 text-xs text-gray-400 transition-colors hover:text-white">返回</button>
        </div>

        <div className="mb-3 flex items-center justify-between border-t border-white/[0.08] pt-4">
          <span className="text-xs font-semibold tracking-[0.16em] text-gray-500 uppercase">资料分区</span>
          <span className="text-[11px] text-gray-600">先选分区，再进入维护</span>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {SECTIONS.map(section => (
            <button
              key={section.key}
              onClick={() => setActiveSection(section.key)}
              className="library-gallery-card group overflow-hidden rounded-3xl border border-white/[0.12] bg-white/[0.055] p-4 text-left transition-all duration-500 hover:-translate-y-1 hover:border-orange-400/45 hover:bg-white/[0.08] hover:shadow-[0_24px_70px_rgba(251,146,60,0.16)]"
            >
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl border border-orange-400/20 bg-orange-500/10 text-xl">{section.icon}</div>
              <div className="text-sm font-semibold text-white">{section.title}</div>
              <p className="mt-2 min-h-[40px] text-xs leading-5 text-gray-500">{section.desc}</p>
              <div className="mt-4 inline-flex items-center gap-1 text-[11px] text-orange-300">
                <span className="h-1.5 w-1.5 rounded-full bg-orange-400" />{section.action}
              </div>
            </button>
          ))}
        </div>

        {activeSection === 'brand' && (
          <BrandKitPanel
            projectId={projectId}
            hasUploadedPdf={hasUploadedPdf}
            pdfText={pdfText}
            onClose={() => setActiveSection(null)}
            embedded
          />
        )}

        {activeMeta && activeMeta.key !== 'brand' && (
          <div className="mt-4 rounded-3xl border border-dashed border-white/[0.14] bg-white/[0.04] px-6 py-10 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-3xl border border-orange-400/20 bg-orange-500/10 text-3xl">{activeMeta.icon}</div>
            <h3 className="text-sm font-semibold text-white">{activeMeta.title}</h3>
            <p className="mt-2 text-xs text-gray-500">敬请完善</p>
          </div>
        )}
      </section>
    </div>
  );
}
