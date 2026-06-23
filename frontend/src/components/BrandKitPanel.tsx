import { useState, useEffect } from 'react';
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
}

interface Props {
  projectId: number;
  hasUploadedPdf: boolean;
  pdfText?: string;
  onClose: () => void;
}

const EMPTY_KIT: BrandKitData = {
  brand_name: '', tagline: null, primary_color: null, secondary_color: null,
  accent_color: null, font_headings: null, font_body: null, tone_of_voice: null,
  visual_style: null, iconography: null, brand_story: null,
};

function ColorSwatch({ color, label }: { color: string | null; label: string }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className="w-16 h-16 rounded-2xl shadow-[0_2px_8px_rgba(0,0,0,0.08)]"
        style={{ background: color || '#D0D0D0' }}
      />
      <span className="text-[13px] text-[#666]">{label}</span>
      <span className="text-xs font-mono text-[#999]">{color || '—'}</span>
    </div>
  );
}

export default function BrandKitPanel({ projectId, hasUploadedPdf, pdfText, onClose }: Props) {
  const [kit, setKit] = useState<BrandKitData | null>(null);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editKit, setEditKit] = useState<BrandKitData | null>(null);
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [logoUploading, setLogoUploading] = useState(false);

  useEffect(() => { loadKit(); }, [projectId]);

  const loadKit = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`/api/v1/brand/${projectId}`);
      const data = await resp.json();
      if (data.brand_kit) { setKit(data.brand_kit); setEditKit(data.brand_kit); }
    } catch {}
    setLoading(false);
  };

  const extractFromPdf = async () => {
    if (!pdfText) { toast('请先上传文档'); return; }
    setExtracting(true);
    try {
      const fd = new FormData(); fd.append('text', pdfText); fd.append('project_id', String(projectId));
      const resp = await fetch('/api/v1/brand/extract', { method: 'POST', body: fd });
      const data = await resp.json();
      setKit(data); setEditKit(data);
      toast('品牌元素提取完成');
    } catch { toast('提取失败', 'error'); }
    setExtracting(false);
  };

  const extractFromFile = async (file: File) => {
    setExtracting(true);
    try {
      const fd = new FormData(); fd.append('file', file); fd.append('project_id', String(projectId));
      const resp = await fetch('/api/v1/brand/extract', { method: 'POST', body: fd });
      const data = await resp.json();
      setKit(data); setEditKit(data);
      toast('品牌元素提取完成');
    } catch { toast('提取失败', 'error'); }
    setExtracting(false);
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; if (!file) return;
    setLogoUploading(true);
    try {
      const fd = new FormData(); fd.append('file', file);
      const resp = await fetch(`/api/v1/brand/${projectId}/logo`, { method: 'POST', body: fd });
      const data = await resp.json();
      setLogoUrl(data.logo_url);
    } catch { toast('Logo 上传失败', 'error'); }
    setLogoUploading(false);
  };

  const saveEdits = async () => {
    if (!editKit) return;
    try {
      await fetch('/api/v1/brand/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId, name: editKit.brand_name,
          primary_color: editKit.primary_color, secondary_color: editKit.secondary_color,
          accent_color: editKit.accent_color, font_style: editKit.font_headings,
          tone_of_voice: editKit.tone_of_voice,
          visual_keywords: [editKit.visual_style, editKit.iconography].filter(Boolean),
        }),
      });
      setKit(editKit); setEditing(false);
      toast('已保存');
    } catch { toast('保存失败', 'error'); }
  };

  const update = (field: keyof BrandKitData, value: string) => {
    setEditKit(prev => prev ? { ...prev, [field]: value } : null);
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
        <div className="animate-spin w-6 h-6 border-2 border-[#FF8C42] border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fadeIn">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      {/* Panel — light theme matching target style */}
      <div
        className="relative w-full max-w-3xl max-h-[88vh] overflow-y-auto rounded-[28px] bg-[#E8E8E8] shadow-[0_24px_48px_rgba(0,0,0,0.18)]"
        onClick={e => e.stopPropagation()}
      >
        <div className="p-10 space-y-8">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center text-lg"
                style={{ background: 'linear-gradient(135deg, #FF7A59, #FF9473)' }}
              >
                🎨
              </div>
              <div>
                <h2 className="text-[22px] font-bold text-[#2D2D2D]">品牌套件</h2>
                <p className="text-sm text-[#666]">Brand Identity Kit</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="w-10 h-10 rounded-lg bg-white/[0.6] hover:bg-white flex items-center justify-center text-[#666] hover:text-[#333] transition-colors text-lg leading-none"
            >
              ✕
            </button>
          </div>

          {extracting ? (
            <div className="flex flex-col items-center py-16 gap-4">
              <div className="relative">
                <div className="w-16 h-16 rounded-2xl bg-[#FF7A59]/20 animate-pulse" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="animate-spin w-6 h-6 border-2 border-[#FF7A59] border-t-transparent rounded-full" />
                </div>
              </div>
              <p className="text-sm text-[#888]">AI 正在分析品牌元素...</p>
              <p className="text-xs text-[#AAA]">提取色彩、字体、调性等信息</p>
            </div>
          ) : !kit ? (
            /* Empty state */
            <div className="space-y-4">
              <div className="text-center py-8">
                <div className="text-5xl mb-4">🎨</div>
                <h3 className="text-base font-semibold text-[#333] mb-1">创建品牌套件</h3>
                <p className="text-xs text-[#999] max-w-sm mx-auto">
                  从已上传的产品文档中自动提取品牌元素，或手动上传品牌素材
                </p>
              </div>
              <div className="grid gap-3">
                {hasUploadedPdf && pdfText && (
                  <button onClick={extractFromPdf}
                    className="w-full p-4 rounded-xl bg-white border border-[#E5E5E5] text-left hover:border-[#FF8C42]/40 hover:bg-[#FFF8F4] transition-all group">
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">🤖</span>
                      <div>
                        <p className="text-sm font-medium text-[#333] group-hover:text-[#FF8C42] transition-colors">从已上传文档中解析</p>
                        <p className="text-[11px] text-[#999] mt-0.5">AI 自动提取品牌色、字体、调性等元素</p>
                      </div>
                    </div>
                  </button>
                )}
                <label className="w-full p-4 rounded-xl border-2 border-dashed border-[#D0D0D0] hover:border-[#AAA] text-left cursor-pointer transition-all group bg-white/50">
                  <input type="file" className="hidden" accept=".pdf,.docx,.txt"
                    onChange={e => { const f = e.target.files?.[0]; if (f) extractFromFile(f); }} />
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">📄</span>
                    <div>
                      <p className="text-sm font-medium text-[#555] group-hover:text-[#333] transition-colors">上传品牌文档</p>
                      <p className="text-[11px] text-[#999] mt-0.5">上传品牌手册 PDF / Word，自动解析</p>
                    </div>
                  </div>
                </label>
                <button onClick={() => { setKit(EMPTY_KIT); setEditKit(EMPTY_KIT); setEditing(true); }}
                  className="w-full p-4 rounded-xl bg-white border border-[#E5E5E5] text-left hover:border-[#CCC] transition-all group">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">✏️</span>
                    <div>
                      <p className="text-sm font-medium text-[#555] group-hover:text-[#333] transition-colors">手动填写</p>
                      <p className="text-[11px] text-[#999] mt-0.5">自行输入品牌色、字体、调性等信息</p>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          ) : editing ? (
            /* Edit mode */
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                {([
                  ['brand_name', '品牌名称'],
                  ['tagline', '品牌标语'],
                  ['tone_of_voice', '品牌调性'],
                  ['visual_style', '视觉风格'],
                  ['iconography', '图标风格'],
                  ['font_headings', '标题字体'],
                  ['font_body', '正文字体'],
                ] as const).map(([field, label]) => (
                  <div key={field} className={field === 'brand_name' ? 'col-span-2' : ''}>
                    <label className="text-[11px] text-[#888] uppercase tracking-wider mb-1 block">{label}</label>
                    <input type="text" value={editKit?.[field] || ''}
                      onChange={e => update(field, e.target.value)}
                      className="w-full bg-white border border-[#E5E5E5] rounded-lg px-3 py-2 text-sm text-[#333] placeholder-[#BBB] focus:border-[#FF8C42]/50 focus:ring-1 focus:ring-[#FF8C42]/20 outline-none transition-all" />
                  </div>
                ))}
                <div className="col-span-2">
                  <label className="text-[11px] text-[#888] uppercase tracking-wider mb-1 block">色彩系统</label>
                  <div className="grid grid-cols-3 gap-2">
                    {(['primary_color', 'secondary_color', 'accent_color'] as const).map(field => (
                      <div key={field} className="flex gap-1.5">
                        <input type="color" value={editKit?.[field] || '#333333'}
                          onChange={e => update(field, e.target.value)}
                          className="w-9 h-9 rounded-lg border border-[#E0E0E0] cursor-pointer flex-shrink-0" />
                        <input type="text" value={editKit?.[field] || ''}
                          onChange={e => update(field, e.target.value)}
                          placeholder="#000000"
                          className="w-full bg-white border border-[#E5E5E5] rounded-lg px-2 py-2 text-[11px] font-mono text-[#555] placeholder-[#BBB] focus:border-[#FF8C42]/50 outline-none" />
                      </div>
                    ))}
                  </div>
                </div>
                <div className="col-span-2">
                  <label className="text-[11px] text-[#888] uppercase tracking-wider mb-1 block">品牌故事</label>
                  <textarea value={editKit?.brand_story || ''}
                    onChange={e => update('brand_story', e.target.value)} rows={3}
                    className="w-full bg-white border border-[#E5E5E5] rounded-lg px-3 py-2 text-sm text-[#333] placeholder-[#BBB] focus:border-[#FF8C42]/50 outline-none resize-none transition-all" />
                </div>
              </div>
              <div className="flex gap-2 pt-1">
                <button onClick={saveEdits}
                  className="flex-1 py-2.5 rounded-xl bg-[#FF8C42] text-white text-sm font-medium hover:bg-[#FF7A30] transition-colors">
                  保存品牌套件
                </button>
                <button onClick={() => { setEditing(false); setEditKit(kit); }}
                  className="px-5 py-2.5 rounded-xl bg-white border border-[#E5E5E5] text-[#888] text-sm hover:text-[#333] hover:bg-[#F5F5F5] transition-all">
                  取消
                </button>
              </div>
            </div>
          ) : (
            /* Display mode — matching target style */
            <div className="space-y-8">
              {/* Logo + Brand Name — large display */}
              <div className="flex items-center gap-6">
                <div className="relative group flex-shrink-0">
                  <div className="w-[88px] h-[88px] rounded-[20px] bg-[#E8D4D4] flex items-center justify-center text-[42px] font-bold text-[#6B5B6E] overflow-hidden"
                    style={{ fontFamily: 'Georgia, "Times New Roman", serif' }}>
                    {logoUrl ? (
                      <img src={logoUrl} alt="Logo" className="w-full h-full object-contain" />
                    ) : (
                      kit.brand_name?.charAt(0)?.toUpperCase() || '?'
                    )}
                  </div>
                  <label className="absolute inset-0 rounded-[20px] bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer">
                    <input type="file" accept="image/*" className="hidden" onChange={handleLogoUpload} />
                    <span className="text-[10px] text-white">{logoUploading ? '...' : '更换'}</span>
                  </label>
                </div>
                <div>
                  <h3 className="text-[38px] font-extrabold text-[#1A1A1A] leading-none">
                    {kit.brand_name || '未命名品牌'}
                  </h3>
                  {kit.tagline && (
                    <p className="text-sm text-[#888] mt-1">{kit.tagline}</p>
                  )}
                </div>
              </div>

              {/* Color System — with star icon */}
              {(kit.primary_color || kit.secondary_color || kit.accent_color) && (
                <div>
                  <p className="flex items-center gap-1.5 text-base font-medium text-[#4A4A4A] mb-4">
                    <span>✨</span> 色彩系统
                  </p>
                  <div className="flex gap-8 justify-center">
                    <ColorSwatch color={kit.primary_color} label="主色" />
                    <ColorSwatch color={kit.secondary_color} label="辅色" />
                    <ColorSwatch color={kit.accent_color} label="强调色" />
                  </div>
                </div>
              )}

              {/* Typography */}
              {(kit.font_headings || kit.font_body) && (
                <div>
                  <p className="flex items-center gap-1.5 text-base font-medium text-[#4A4A4A] mb-4">
                    <span>🔤</span> 字体系统
                  </p>
                  <div className="grid grid-cols-2 gap-4">
                    {kit.font_headings && (
                      <div className="bg-white rounded-xl px-5 py-4 border border-[#EBEBEB]">
                        <p className="text-[11px] text-[#999] uppercase tracking-wider mb-2">标题字体</p>
                        <p className="text-lg text-[#333] font-bold" style={{ fontFamily: kit.font_headings }}>
                          {kit.font_headings}
                        </p>
                        <p className="text-[28px] text-[#555] mt-1" style={{ fontFamily: kit.font_headings }}>Aa</p>
                      </div>
                    )}
                    {kit.font_body && (
                      <div className="bg-white rounded-xl px-5 py-4 border border-[#EBEBEB]">
                        <p className="text-[11px] text-[#999] uppercase tracking-wider mb-2">正文字体</p>
                        <p className="text-sm text-[#666]" style={{ fontFamily: kit.font_body }}>
                          {kit.font_body}
                        </p>
                        <p className="text-[20px] text-[#888] mt-1" style={{ fontFamily: kit.font_body }}>Aa</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Brand attributes */}
              <div className="grid grid-cols-2 gap-3">
                {kit.tone_of_voice && (
                  <div className="bg-white rounded-xl px-4 py-3 border border-[#EBEBEB]">
                    <p className="text-[11px] text-[#999] uppercase tracking-wider mb-1">💬 品牌调性</p>
                    <p className="text-sm text-[#555]">{kit.tone_of_voice}</p>
                  </div>
                )}
                {kit.visual_style && (
                  <div className="bg-white rounded-xl px-4 py-3 border border-[#EBEBEB]">
                    <p className="text-[11px] text-[#999] uppercase tracking-wider mb-1">🎯 视觉风格</p>
                    <p className="text-sm text-[#555]">{kit.visual_style}</p>
                  </div>
                )}
                {kit.iconography && (
                  <div className="bg-white rounded-xl px-4 py-3 border border-[#EBEBEB]">
                    <p className="text-[11px] text-[#999] uppercase tracking-wider mb-1">🔷 图标风格</p>
                    <p className="text-sm text-[#555]">{kit.iconography}</p>
                  </div>
                )}
              </div>

              {/* Brand story */}
              {kit.brand_story && (
                <div className="bg-white rounded-xl px-4 py-3 border border-[#EBEBEB]">
                  <p className="text-[11px] text-[#999] uppercase tracking-wider mb-1">📖 品牌故事</p>
                  <p className="text-sm text-[#555] leading-relaxed">{kit.brand_story}</p>
                </div>
              )}

              {/* Action buttons — matching target style */}
              <div className="flex gap-4 pt-2">
                <button onClick={() => setEditing(true)}
                  className="flex-1 py-3.5 rounded-xl bg-[#D8D8D8]/60 text-[#4A4A4A] text-base font-medium hover:bg-[#D0D0D0] transition-colors flex items-center justify-center gap-1.5">
                  <span>✏️</span> 编辑
                </button>
                <button onClick={onClose}
                  className="flex-1 py-3.5 rounded-xl bg-[#C9A48A] text-white text-base font-medium hover:bg-[#B89278] transition-colors">
                  关闭
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
