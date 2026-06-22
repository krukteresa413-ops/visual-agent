import { useState, useEffect, useRef } from 'react';
import { toast } from './Toast';

interface BrandKitData {
  brand_name: string;
  tagline: string | null;
  primary_color: string | null;
  secondary_color: string | null;
  accent_color: string | null;
  font_headings: string | null;
  font_body: string | null;
  tone_of_voice: string | null;
  visual_style: string | null;
  iconography: string | null;
  brand_story: string | null;
  logo_url?: string | null;
}

interface Props {
  projectId: number;
  hasUploadedPdf: boolean;
  pdfText?: string;
  onClose: () => void;
}

interface SectionState {
  logo: boolean;
  font: boolean;
  color: boolean;
  designGuide: boolean;
  image: boolean;
  brandGuide: boolean;
}

type SectionKey = keyof SectionState;

const EMPTY_KIT: BrandKitData = {
  brand_name: '', tagline: null, primary_color: null, secondary_color: null,
  accent_color: null, font_headings: null, font_body: null, tone_of_voice: null,
  visual_style: null, iconography: null, brand_story: null, logo_url: null,
};

const CARD_DEFS: { key: SectionKey; label: string; icon: string }[] = [
  { key: 'logo', label: 'Logo', icon: '🅻' },
  { key: 'font', label: '字体', icon: 'Ag' },
  { key: 'color', label: '颜色', icon: '■' },
  { key: 'designGuide', label: '设计指南', icon: '💬' },
  { key: 'image', label: '图像', icon: '🖼' },
  { key: 'brandGuide', label: '品牌指南', icon: '📖' },
];

export default function BrandKitPanel({ projectId, onClose }: Props) {
  const [kit, setKit] = useState<BrandKitData | null>(null);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [activeSection, setActiveSection] = useState<SectionKey | null>(null);
  const [sections, setSections] = useState<SectionState>({
    logo: false, font: false, color: false, designGuide: false, image: false, brandGuide: false,
  });
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [logoUploading, setLogoUploading] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { loadKit(); }, [projectId]);

  const loadKit = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`/api/v1/brand/${projectId}`);
      const data = await resp.json();
      if (data.brand_kit) {
        setKit(data.brand_kit);
                setLogoUrl(data.brand_kit.logo_url || null);
        // Mark sections with data
        const k = data.brand_kit;
        setSections({
          logo: !!(k.logo_url || k.brand_name),
          font: !!(k.font_headings || k.font_body),
          color: !!(k.primary_color || k.secondary_color || k.accent_color),
          designGuide: !!(k.visual_style || k.iconography),
          image: false,
          brandGuide: !!(k.brand_story || k.tone_of_voice),
        });
      }
    } catch { /* silent */ }
    setLoading(false);
  };


  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; if (!file) return;
    setExtracting(true);
    try {
      const fd = new FormData(); fd.append('file', file); fd.append('project_id', String(projectId));
      const resp = await fetch('/api/v1/brand/extract', { method: 'POST', body: fd });
      const data = await resp.json();
      setKit(data);       setSections({
        logo: !!(data.logo_url || data.brand_name),
        font: !!(data.font_headings || data.font_body),
        color: !!(data.primary_color || data.secondary_color || data.accent_color),
        designGuide: !!(data.visual_style || data.iconography),
        image: false,
        brandGuide: !!(data.brand_story || data.tone_of_voice),
      });
      toast('品牌元素提取完成');
    } catch { toast('提取失败', 'error'); }
    setExtracting(false);
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; if (!file) return;
    setLogoUploading(true);
    try {
      const fd = new FormData(); fd.append('file', file);
      const resp = await fetch(`/api/v1/brand/1/logo`, { method: 'POST', body: fd });
      const data = await resp.json();
      setLogoUrl(data.logo_url);
      setSections(prev => ({ ...prev, logo: true }));
      toast('Logo 已上传');
    } catch { toast('Logo 上传失败', 'error'); }
    setLogoUploading(false);
  };

  const handleCardClick = (key: SectionKey) => {
    setActiveSection(activeSection === key ? null : key);
  };

  const updateField = (field: keyof BrandKitData, value: string) => {
    setKit(prev => prev ? { ...prev, [field]: value || null } : null);
  };

  const saveKit = async () => {
    if (!kit) return;
    try {
      await fetch('/api/v1/brand/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId, name: kit.brand_name,
          primary_color: kit.primary_color, secondary_color: kit.secondary_color,
          accent_color: kit.accent_color, font_style: kit.font_headings,
          tone_of_voice: kit.tone_of_voice,
          visual_keywords: [kit.visual_style, kit.iconography].filter(Boolean),
        }),
      });
      toast('品牌资产已保存');
      setActiveSection(null);
    } catch { toast('保存失败', 'error'); }
  };

  const startFromScratch = () => {
    setKit(EMPTY_KIT);
    setActiveSection(null);
  };

  // ── Render helpers ──────────────────────────────────────────

  const renderCard = (key: SectionKey, label: string, _icon: string) => {
    const isFilled = sections[key];
    const isActive = activeSection === key;

    // Card background styles per category
    const cardBg: Record<SectionKey, string> = {
      logo: 'bg-gradient-to-br from-lime-500/25 via-lime-600/15 to-lime-800/10 border-lime-500/15',
      font: 'bg-gradient-to-br from-gray-900/80 via-gray-900/60 to-gray-800/40 border-white/[0.06]',
      color: 'bg-[#d9d9d9] border-gray-300/30',
      designGuide: 'bg-gradient-to-br from-blue-900/20 via-indigo-900/15 to-blue-800/20 border-blue-500/10',
      image: 'bg-gradient-to-br from-purple-900/20 via-fuchsia-900/15 to-purple-800/20 border-purple-500/10',
      brandGuide: 'bg-gradient-to-br from-amber-900/20 via-orange-900/15 to-amber-800/20 border-amber-500/10',
    };

    return (
      <div className="flex flex-col items-center">
        <button
          onClick={() => handleCardClick(key)}
          className={`w-full aspect-square rounded-xl flex items-center justify-center overflow-hidden relative
            border transition-all duration-200 cursor-pointer group
            ${cardBg[key]}
            ${isActive ? 'ring-2 ring-orange-400/60 scale-[1.03]' : 'hover:scale-[1.02] hover:border-white/[0.15]'}`}
        >
          {/* Card content based on category */}
          {key === 'logo' && (
            <div className="flex flex-col items-center gap-2">
              {logoUrl ? (
                <img src={logoUrl} alt="Logo" className="w-16 h-16 object-contain rounded-lg" />
              ) : (
                <div className="w-16 h-16 rounded-full border-2 border-lime-400/50 flex items-center justify-center">
                  <span className="text-lime-300 text-lg font-bold tracking-wider"
                    style={{ fontFamily: 'Georgia, serif' }}>
                    {kit?.brand_name?.charAt(0)?.toUpperCase() || 'L°'}
                  </span>
                </div>
              )}
              {isFilled && (
                <span className="text-[10px] text-lime-400/70 bg-lime-500/10 px-2 py-0.5 rounded-full">已设置</span>
              )}
            </div>
          )}

          {key === 'font' && (
            <div className="flex flex-col items-center">
              <span className="text-[64px] text-white/95 font-serif leading-none"
                style={{ fontFamily: kit?.font_headings || 'Georgia, "Times New Roman", serif' }}>
                Ag
              </span>
              {isFilled && (
                <span className="text-[10px] text-gray-400 mt-1">{kit?.font_headings}</span>
              )}
            </div>
          )}

          {key === 'color' && (
            <div className="flex gap-[2px] w-full h-full absolute inset-0">
              <div className="flex-1 h-full" style={{ background: kit?.primary_color || '#c9c9c9' }} />
              <div className="flex-1 h-full" style={{ background: kit?.secondary_color || '#a0a0a0' }} />
              <div className="flex-1 h-full" style={{ background: kit?.accent_color || '#707070' }} />
              <div className="flex-1 h-full bg-[#4a4a4a]" />
              <div className="flex-1 h-full bg-[#d4d76a]" />
            </div>
          )}

          {key === 'designGuide' && (
            <div className="flex flex-col items-center gap-1">
              <svg width="56" height="48" viewBox="0 0 56 48" fill="none">
                <rect x="4" y="4" width="48" height="36" rx="10" stroke="currentColor" strokeWidth="2" className="text-blue-400/60" />
                <circle cx="20" cy="20" r="3" fill="currentColor" className="text-blue-400/40" />
                <circle cx="28" cy="20" r="3" fill="currentColor" className="text-blue-400/40" />
                <circle cx="36" cy="20" r="3" fill="currentColor" className="text-blue-400/40" />
                <path d="M12 32 L18 22 L24 28 L28 22 L36 30" stroke="currentColor" strokeWidth="1.5" className="text-blue-400/30" fill="none" />
              </svg>
              {isFilled && (
                <span className="text-[10px] text-blue-400/70">已设置</span>
              )}
            </div>
          )}

          {key === 'image' && (
            <div className="w-full h-full flex items-center justify-center relative">
              {isFilled && logoUrl ? (
                <img src={logoUrl} alt="Brand" className="w-full h-full object-cover" />
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                    <rect x="6" y="8" width="36" height="32" rx="4" stroke="currentColor" strokeWidth="1.5" className="text-purple-400/40" />
                    <circle cx="18" cy="20" r="5" stroke="currentColor" strokeWidth="1.5" className="text-purple-400/30" />
                    <path d="M6 34 L16 24 L26 32 L32 26 L42 34" stroke="currentColor" strokeWidth="1.5" className="text-purple-400/20" />
                  </svg>
                  <span className="text-[10px] text-purple-400/50">添加图片</span>
                </div>
              )}
            </div>
          )}

          {key === 'brandGuide' && (
            <div className="flex flex-col items-center gap-1">
              <svg width="44" height="54" viewBox="0 0 44 54" fill="none">
                <rect x="3" y="6" width="38" height="46" rx="3" stroke="currentColor" strokeWidth="2" className="text-amber-400/50" />
                <line x1="12" y1="18" x2="32" y2="18" stroke="currentColor" strokeWidth="1.5" className="text-amber-400/30" />
                <line x1="12" y1="26" x2="32" y2="26" stroke="currentColor" strokeWidth="1.5" className="text-amber-400/30" />
                <line x1="12" y1="34" x2="28" y2="34" stroke="currentColor" strokeWidth="1.5" className="text-amber-400/30" />
                <line x1="12" y1="42" x2="26" y2="42" stroke="currentColor" strokeWidth="1.5" className="text-amber-400/30" />
              </svg>
              {isFilled && (
                <span className="text-[10px] text-amber-400/70">已设置</span>
              )}
            </div>
          )}

          {/* Hover overlay */}
          <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <span className="text-xs text-white font-medium bg-white/10 px-3 py-1 rounded-full backdrop-blur-sm">
              {isFilled ? '编辑' : '添加'}
            </span>
          </div>
        </button>
        <span className="text-[13px] text-gray-300 mt-1.5 font-medium">{label}</span>
      </div>
    );
  };

  const renderSectionPanel = () => {
    if (!activeSection || !kit) return null;

    const sectionTitles: Record<SectionKey, string> = {
      logo: 'Logo',
      font: '字体设置',
      color: '品牌色彩',
      designGuide: '设计指南',
      image: '品牌图像',
      brandGuide: '品牌指南',
    };

    return (
      <div className="mt-6 p-5 rounded-2xl bg-white/[0.04] border border-white/[0.10] animate-fadeIn">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-base font-semibold text-white">{sectionTitles[activeSection]}</h4>
          <button
            onClick={() => setActiveSection(null)}
            className="w-7 h-7 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-gray-400 text-xs flex items-center justify-center"
          >✕</button>
        </div>

        {/* Logo Section */}
        {activeSection === 'logo' && (
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="relative group w-20 h-20 rounded-2xl bg-gradient-to-br from-orange-500/20 to-pink-500/20 border border-white/10 flex items-center justify-center overflow-hidden">
                {logoUrl ? (
                  <img src={logoUrl} alt="Logo" className="w-full h-full object-contain" />
                ) : (
                  <span className="text-3xl text-gray-500">{kit.brand_name?.charAt(0) || '?'}</span>
                )}
                <label className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer">
                  <input type="file" accept="image/*" className="hidden" onChange={handleLogoUpload} />
                  <span className="text-xs text-white">{logoUploading ? '上传中...' : '更换'}</span>
                </label>
              </div>
              <div>
                <input
                  type="text" value={kit.brand_name || ''}
                  onChange={e => updateField('brand_name', e.target.value)}
                  placeholder="品牌名称"
                  className="bg-white/[0.05] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-orange-500/40 outline-none w-48"
                />
                <input
                  type="text" value={kit.tagline || ''}
                  onChange={e => updateField('tagline', e.target.value)}
                  placeholder="品牌标语"
                  className="bg-white/[0.05] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-orange-500/40 outline-none w-48 mt-2"
                />
              </div>
            </div>
          </div>
        )}

        {/* Font Section */}
        {activeSection === 'font' && (
          <div className="space-y-4">
            <div>
              <label className="text-[11px] text-gray-500 uppercase tracking-wider mb-1.5 block">标题字体</label>
              <input
                type="text" value={kit.font_headings || ''}
                onChange={e => updateField('font_headings', e.target.value)}
                placeholder="例如: Playfair Display, 思源宋体"
                className="w-full bg-white/[0.05] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-orange-500/40 outline-none"
              />
              <p className="text-2xl text-white/80 mt-2 font-bold"
                style={{ fontFamily: kit.font_headings || 'serif' }}>
                {kit.font_headings || '标题字体预览'}
              </p>
            </div>
            <div>
              <label className="text-[11px] text-gray-500 uppercase tracking-wider mb-1.5 block">正文字体</label>
              <input
                type="text" value={kit.font_body || ''}
                onChange={e => updateField('font_body', e.target.value)}
                placeholder="例如: Inter, 思源黑体"
                className="w-full bg-white/[0.05] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-orange-500/40 outline-none"
              />
              <p className="text-base text-gray-300 mt-2"
                style={{ fontFamily: kit.font_body || 'sans-serif' }}>
                {kit.font_body || '正文字体预览 · The quick brown fox'}
              </p>
            </div>
          </div>
        )}

        {/* Color Section */}
        {activeSection === 'color' && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              {([
                ['primary_color', '主色', kit.primary_color],
                ['secondary_color', '辅色', kit.secondary_color],
                ['accent_color', '强调色', kit.accent_color],
              ] as const).map(([field, label, color]) => (
                <div key={field} className="flex flex-col items-center gap-2">
                  <div
                    className="w-16 h-16 rounded-2xl border border-white/10 shadow-lg"
                    style={{ background: color || '#333' }}
                  />
                  <span className="text-[10px] text-gray-500">{label}</span>
                  <div className="flex gap-1">
                    <input
                      type="color" value={color || '#333333'}
                      onChange={e => updateField(field, e.target.value)}
                      className="w-7 h-7 rounded border-0 cursor-pointer"
                    />
                    <input
                      type="text" value={color || ''}
                      onChange={e => updateField(field, e.target.value)}
                      placeholder="#000000"
                      className="w-20 bg-white/[0.05] border border-white/[0.10] rounded px-2 py-1 text-[11px] font-mono text-gray-300 placeholder-gray-600 focus:border-orange-500/40 outline-none"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Design Guide Section */}
        {activeSection === 'designGuide' && (
          <div className="space-y-3">
            <div>
              <label className="text-[11px] text-gray-500 uppercase tracking-wider mb-1 block">视觉风格</label>
              <input
                type="text" value={kit.visual_style || ''}
                onChange={e => updateField('visual_style', e.target.value)}
                placeholder="例如: 极简主义, 科技感, 自然清新"
                className="w-full bg-white/[0.05] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-orange-500/40 outline-none"
              />
            </div>
            <div>
              <label className="text-[11px] text-gray-500 uppercase tracking-wider mb-1 block">图标风格</label>
              <input
                type="text" value={kit.iconography || ''}
                onChange={e => updateField('iconography', e.target.value)}
                placeholder="例如: 线性图标, 面性图标, 自定义插画"
                className="w-full bg-white/[0.05] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-orange-500/40 outline-none"
              />
            </div>
          </div>
        )}

        {/* Image Section */}
        {activeSection === 'image' && (
          <div className="space-y-4">
            <div className="p-8 rounded-xl border-2 border-dashed border-gray-600 hover:border-gray-500 text-center cursor-pointer transition-colors"
              onClick={() => fileInputRef.current?.click()}>
              <input ref={fileInputRef} type="file" accept="image/*" className="hidden"
                onChange={handleLogoUpload} />
              <div className="text-3xl mb-2">🖼</div>
              <p className="text-sm text-gray-400">上传品牌参考图像</p>
              <p className="text-[11px] text-gray-600 mt-1">用于 AI 生成时的风格参考</p>
            </div>
          </div>
        )}

        {/* Brand Guide Section */}
        {activeSection === 'brandGuide' && (
          <div className="space-y-4">
            <div>
              <label className="text-[11px] text-gray-500 uppercase tracking-wider mb-1 block">品牌调性</label>
              <input
                type="text" value={kit.tone_of_voice || ''}
                onChange={e => updateField('tone_of_voice', e.target.value)}
                placeholder="例如: 专业可信赖, 年轻活力, 高端优雅"
                className="w-full bg-white/[0.05] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-orange-500/40 outline-none"
              />
            </div>
            <div>
              <label className="text-[11px] text-gray-500 uppercase tracking-wider mb-1 block">品牌故事</label>
              <textarea
                value={kit.brand_story || ''}
                onChange={e => updateField('brand_story', e.target.value)}
                rows={4} placeholder="讲述你的品牌故事..."
                className="w-full bg-white/[0.05] border border-white/[0.10] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-orange-500/40 outline-none resize-none"
              />
            </div>
          </div>
        )}

        <button onClick={saveKit}
          className="w-full mt-4 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-orange-600 text-white text-sm font-medium hover:from-orange-400 hover:to-orange-500 transition-all shadow-lg shadow-orange-500/20">
          保存
        </button>
      </div>
    );
  };

  // ── Main render ─────────────────────────────────────────────

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md" onClick={onClose}>
        <div className="animate-spin w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md animate-fadeIn" onClick={onClose}>
      <div
        className="liquid-card backdrop-blur-2xl bg-gradient-to-br from-[#111122] via-[#151528] to-[#0d1122]
          border border-white/[0.10] p-6 w-full max-w-[640px] mx-4 max-h-[90vh] overflow-y-auto rounded-2xl
          shadow-[0_0_80px_rgba(0,0,0,0.6),inset_0_1px_0_0_rgba(255,255,255,0.06)]"
        onClick={e => e.stopPropagation()}
      >
        {/* Close button */}
        <button onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-gray-400 hover:text-white text-sm transition-all flex items-center justify-center z-10"
        >✕</button>

        {/* Header */}
        <div className="text-center mb-4">
          <h2 className="text-xl font-bold text-white tracking-tight">开始使用你的品牌资产</h2>
          <p className="text-[13px] text-gray-400 mt-1.5">添加 Logo、颜色、字体等，保持品牌一致性。</p>
        </div>

        {extracting ? (
          <div className="flex flex-col items-center py-16 gap-4">
            <div className="relative">
              <div className="w-14 h-14 rounded-2xl bg-orange-500/20 animate-pulse" />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="animate-spin w-7 h-7 border-2 border-orange-400 border-t-transparent rounded-full" />
              </div>
            </div>
            <p className="text-sm text-gray-300">AI 正在分析品牌元素...</p>
            <p className="text-[11px] text-gray-500">提取色彩、字体、调性等信息</p>
          </div>
        ) : (
          <>
            {/* 3×2 Card Grid */}
            <div className="grid grid-cols-3 gap-3">
              {CARD_DEFS.map(({ key, label, icon }) => (
                <div key={key}>{renderCard(key, label, icon)}</div>
              ))}
            </div>

            {/* Section sub-panel (if a card is active) */}
            {renderSectionPanel()}

            {/* Upload zone */}
            <div className="mt-5">
              <label
                className="block w-full p-3 rounded-xl border-2 border-dashed border-gray-500/50 hover:border-gray-400/60
                  text-center cursor-pointer transition-all duration-200 bg-white/[0.02] hover:bg-white/[0.04]"
              >
                <input type="file" className="hidden" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
                  onChange={handleFileUpload} />
                <div className="flex flex-col items-center gap-2.5">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-gray-500">
                    <path d="M12 16V4M12 4L8 8M12 4L16 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M4 16V18C4 19.1046 4.89543 20 6 20H18C19.1046 20 20 19.1046 20 18V16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                  <span className="text-sm text-gray-300">上传完整的品牌手册，自动填充所有内容</span>
                  <span className="text-[11px] text-gray-500">PNG、JPG、PDF · 最大 20MB</span>
                </div>
              </label>
            </div>

            {/* "或" Divider */}
            <div className="flex items-center gap-3 my-3">
              <div className="flex-1 h-px bg-white/[0.08]" />
              <span className="text-xs text-gray-500">或</span>
              <div className="flex-1 h-px bg-white/[0.08]" />
            </div>

            {/* "From scratch" option */}
            <button
              onClick={startFromScratch}
              className="w-full p-3 rounded-xl border-2 border-dashed border-gray-500/50 hover:border-gray-400/60
                text-center transition-all duration-200 bg-white/[0.02] hover:bg-white/[0.04] cursor-pointer"
            >
              <span className="text-sm text-gray-400 hover:text-gray-300 transition-colors">
                还没有品牌素材？从零开始在画布上创建。
              </span>
            </button>
          </>
        )}
      </div>
    </div>
  );
}
