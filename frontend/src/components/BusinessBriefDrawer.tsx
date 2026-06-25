/**
 * BusinessBriefDrawer — 商务出图抽屉（Part 3b，v4：资料库自动填）
 *
 * 纯展示 + 注入式取数：开抽屉拉 canonical 公司(静默填公司级)+ 商品列表(选择器)，
 * 选中商品拉详情填商品级；「新建商品」清商品级、留公司级。
 * 取数/上传均由注入函数完成，组件不直接依赖 api client。
 * 字段可改；自动填的字段标「来自资料库」，用户一改该标即消失。
 *
 * 平台 / 参考图为每次生成的选择，不自动填。
 * 回写（新建商品存回资料库）为 Part 3c，本版不含。
 */
import { useEffect, useRef, useState } from 'react';

export interface BusinessBrief {
  upload_platform: string;
  product_name: string;
  selling_points: string;
  target_customer?: string;
  brand_style?: string;
  compliance_notes?: string;
  target_market?: string;
  reference_image_url?: string;
  product_id?: number; // 选中已有商品时带上，供 Part 3c 回写判定
  _mode: 'business';
}

interface BrandLite {
  name?: string;
  tone_of_voice?: string;
  forbidden_words?: string[] | string | null;
}
interface ProductLite {
  id: number;
  product_name: string;
  category?: string;
  selling_points?: string;
}

interface BusinessBriefDrawerProps {
  isLight: boolean;
  onSubmit: (brief: BusinessBrief) => void;
  onCancel?: () => void;
  uploadImage?: (file: File) => Promise<string>;
  fetchBrand?: () => Promise<BrandLite | null>;
  fetchProducts?: () => Promise<ProductLite[]>;
  fetchProductDetail?: (id: number) => Promise<Record<string, unknown>>;
}

const PLATFORMS: { id: string; label: string; hint: string }[] = [
  { id: 'taobao', label: '淘宝 / 天猫', hint: '主图 800×800 · 详情页首屏 · 白底 / 场景图 · 极限词合规' },
  { id: 'jd', label: '京东', hint: '主图 800×800 · 详情页 · 品质感 · 资质合规' },
  { id: 'pinduoduo', label: '拼多多', hint: '主图 750×750 · 主推卖点图' },
  { id: 'xiaohongshu', label: '小红书', hint: '封面 1080×1440(3:4) · 种草调性 · 标签话题' },
  { id: 'douyin', label: '抖音', hint: '9:16 竖版 · 短视频封面 · 强钩子首图' },
  { id: 'amazon', label: '亚马逊', hint: '主图白底 2000×2000 · 英文文案 · A+ 结构化' },
  { id: 'alibaba_intl', label: '阿里国际站', hint: '英文 / 多语 · B2B 详情 · 跨境合规' },
];

function asText(v: unknown): string {
  if (v == null) return '';
  if (Array.isArray(v)) return v.join('、');
  if (typeof v === 'string') return v;
  return String(v);
}

export default function BusinessBriefDrawer({
  isLight, onSubmit, onCancel, uploadImage, fetchBrand, fetchProducts, fetchProductDetail,
}: BusinessBriefDrawerProps) {
  const [platform, setPlatform] = useState('');
  const [productName, setProductName] = useState('');
  const [sellingPoints, setSellingPoints] = useState('');
  const [targetCustomer, setTargetCustomer] = useState('');
  const [brandStyle, setBrandStyle] = useState('');
  const [compliance, setCompliance] = useState('');
  const [market, setMarket] = useState('');
  const [referenceUrl, setReferenceUrl] = useState('');
  const [refName, setRefName] = useState('');
  const [refUploading, setRefUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 资料库
  const [companyName, setCompanyName] = useState('');
  const [products, setProducts] = useState<ProductLite[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const [libFields, setLibFields] = useState<Set<string>>(new Set());

  const markLib = (keys: string[]) =>
    setLibFields((prev) => {
      const n = new Set(prev);
      keys.forEach((k) => n.add(k));
      return n;
    });
  const clearLib = (key: string) =>
    setLibFields((prev) => {
      if (!prev.has(key)) return prev;
      const n = new Set(prev);
      n.delete(key);
      return n;
    });

  // 开抽屉：拉公司(静默填)+ 商品列表
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        if (fetchBrand) {
          const b = await fetchBrand();
          if (alive && b) {
            if (b.name) setCompanyName(b.name);
            const fw = asText(b.forbidden_words);
            const tone = asText(b.tone_of_voice);
            const filled: string[] = [];
            if (fw) { setCompliance(fw); filled.push('compliance'); }
            if (tone) { setBrandStyle(tone); filled.push('brand_style'); }
            if (filled.length) markLib(filled);
          }
        }
        if (fetchProducts) {
          const list = await fetchProducts();
          if (alive && Array.isArray(list)) setProducts(list);
        }
      } catch (e) {
        console.error('library load failed', e);
      }
    })();
    return () => { alive = false; };
  }, [fetchBrand, fetchProducts]);

  const selectProduct = async (id: number) => {
    setSelectedProductId(id);
    if (!fetchProductDetail) return;
    try {
      const d = await fetchProductDetail(id);
      const pn = asText(d.product_name);
      const sp = asText(d.selling_points);
      const tc = asText(d.target_customer);
      const bs = asText(d.brand_style);
      const cn = asText(d.compliance_notes);
      const mk = asText(d.target_market);
      const filled: string[] = [];
      if (pn) { setProductName(pn); filled.push('product_name'); }
      if (sp) { setSellingPoints(sp); filled.push('selling_points'); }
      if (tc) { setTargetCustomer(tc); filled.push('target_customer'); }
      if (bs) { setBrandStyle(bs); filled.push('brand_style'); }
      if (cn) { setCompliance(cn); filled.push('compliance'); }
      if (mk) { setMarket(mk); filled.push('market'); }
      markLib(filled);
    } catch (e) {
      console.error('product detail failed', e);
    }
  };

  const newProduct = () => {
    setSelectedProductId(null);
    setProductName('');
    setSellingPoints('');
    setTargetCustomer('');
    setMarket('');
    // 公司级（compliance/brand_style）保留
    setLibFields((prev) => {
      const n = new Set(prev);
      ['product_name', 'selling_points', 'target_customer', 'market'].forEach((k) => n.delete(k));
      return n;
    });
  };

  const canSubmit =
    platform.trim() !== '' && productName.trim() !== '' && sellingPoints.trim() !== '';
  const selectedHint = PLATFORMS.find((p) => p.id === platform)?.hint;

  const label = isLight ? 'text-gray-600' : 'text-gray-300';
  const labelMuted = isLight ? 'text-gray-400' : 'text-gray-500';
  const field = isLight
    ? 'w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:border-gray-400'
    : 'w-full rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm text-gray-100 outline-none focus:border-white/30';
  const chipBase = 'cursor-pointer rounded-lg px-3 py-1.5 text-xs transition-colors';
  const chipOff = isLight
    ? 'border border-gray-200 text-gray-600 hover:border-gray-300'
    : 'border border-white/10 text-gray-300 hover:border-white/20';
  const chipOn = isLight
    ? 'bg-indigo-50 text-indigo-600 font-medium border border-indigo-200'
    : 'bg-indigo-500/15 text-indigo-300 font-medium border border-indigo-400/30';
  const hintBox = isLight ? 'bg-gray-50 text-gray-500' : 'bg-white/5 text-gray-400';
  const dashBox = isLight
    ? 'border border-dashed border-gray-300 text-gray-400 hover:border-gray-400'
    : 'border border-dashed border-white/15 text-gray-400 hover:border-white/30';
  const libBox = isLight ? 'bg-indigo-50 text-indigo-600' : 'bg-indigo-500/10 text-indigo-300';

  const Req = () => <span className="ml-0.5 text-rose-500 font-bold text-base leading-none">*</span>;
  const LibTag = ({ k }: { k: string }) =>
    libFields.has(k) ? <span className={`ml-2 rounded px-1.5 py-0.5 text-[10px] ${libBox}`}>来自资料库</span> : null;

  const handleRefChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !uploadImage) return;
    setRefUploading(true);
    try {
      const url = await uploadImage(file);
      if (url) { setReferenceUrl(url); setRefName(file.name); }
    } catch (err) {
      console.error('reference upload failed', err);
    } finally {
      setRefUploading(false);
      if (e.target) e.target.value = '';
    }
  };

  const handleStart = () => {
    if (!canSubmit) return;
    onSubmit({
      upload_platform: platform,
      product_name: productName.trim(),
      selling_points: sellingPoints.trim(),
      target_customer: targetCustomer.trim() || undefined,
      brand_style: brandStyle.trim() || undefined,
      compliance_notes: compliance.trim() || undefined,
      target_market: market.trim() || undefined,
      reference_image_url: referenceUrl || undefined,
      product_id: selectedProductId ?? undefined,
      _mode: 'business',
    });
  };

  return (
    <div data-testid="business-brief-drawer" className="space-y-4 text-sm">
      {/* 资料库：公司 + 商品选择器 */}
      {(companyName || products.length > 0) && (
        <div className={`rounded-lg px-3 py-2.5 ${libBox}`}>
          <div className="mb-2 flex items-center gap-1.5 text-xs font-medium">
            检测到{companyName ? `「${companyName}」` : ''}资料 · 选商品自动填
          </div>
          <div className="flex flex-wrap gap-1.5">
            {products.map((p) => (
              <span key={p.id} role="button" tabIndex={0} onClick={() => selectProduct(p.id)}
                className={`${chipBase} ${selectedProductId === p.id ? chipOn : (isLight ? 'border border-gray-200 bg-white text-gray-600' : 'border border-white/10 bg-black/20 text-gray-300')}`}>
                {p.product_name}
              </span>
            ))}
            <span role="button" tabIndex={0} onClick={newProduct}
              className={`${chipBase} ${selectedProductId === null ? chipOn : dashBox}`}>
              ＋ 新建商品（同公司）
            </span>
          </div>
        </div>
      )}

      {/* 上架平台（必填） */}
      <div>
        <div className={`mb-1.5 ${label}`}>上架平台<Req /></div>
        <div className="flex flex-wrap gap-1.5">
          {PLATFORMS.map((p) => (
            <span key={p.id} role="button" tabIndex={0} onClick={() => setPlatform(p.id)}
              className={`${chipBase} ${platform === p.id ? chipOn : chipOff}`}>{p.label}</span>
          ))}
        </div>
        {selectedHint && <div className={`mt-2 rounded-lg px-3 py-2 text-xs ${hintBox}`}>按平台自动带出：{selectedHint}</div>}
      </div>

      {/* 商品 / 品牌名（必填） */}
      <div>
        <div className={`mb-1.5 ${label}`}>商品 / 品牌名<Req /><LibTag k="product_name" /></div>
        <input className={field} value={productName}
          onChange={(e) => { setProductName(e.target.value); clearLib('product_name'); }} />
      </div>

      {/* 核心卖点（必填） */}
      <div>
        <div className={`mb-1.5 ${label}`}>核心卖点<Req /><LibTag k="selling_points" /></div>
        <textarea className={`${field} resize-y`} rows={2} value={sellingPoints}
          onChange={(e) => { setSellingPoints(e.target.value); clearLib('selling_points'); }} />
      </div>

      {/* 选填两列 */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className={`mb-1.5 ${labelMuted}`}>目标受众<LibTag k="target_customer" /></div>
          <input className={field} value={targetCustomer} placeholder="选填"
            onChange={(e) => { setTargetCustomer(e.target.value); clearLib('target_customer'); }} />
        </div>
        <div>
          <div className={`mb-1.5 ${labelMuted}`}>风格关键词<LibTag k="brand_style" /></div>
          <input className={field} value={brandStyle} placeholder="选填"
            onChange={(e) => { setBrandStyle(e.target.value); clearLib('brand_style'); }} />
        </div>
        <div>
          <div className={`mb-1.5 ${labelMuted}`}>禁忌 / 合规<LibTag k="compliance" /></div>
          <input className={field} value={compliance} placeholder="选填"
            onChange={(e) => { setCompliance(e.target.value); clearLib('compliance'); }} />
        </div>
        <div>
          <div className={`mb-1.5 ${labelMuted}`}>语言 / 市场<LibTag k="market" /></div>
          <input className={field} value={market} placeholder="中文 · 选填"
            onChange={(e) => { setMarket(e.target.value); clearLib('market'); }} />
        </div>
      </div>

      {/* 参考图（选填） */}
      <div>
        <div className={`mb-1.5 ${labelMuted}`}>参考图（选填）</div>
        <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleRefChange} />
        {referenceUrl ? (
          <div className={`flex items-center gap-2 rounded-lg px-3 py-2 ${hintBox}`}>
            <img src={referenceUrl} alt="" className="h-8 w-8 rounded object-cover" />
            <span className="max-w-[150px] truncate text-xs">{refName}</span>
            <button type="button" onClick={() => { setReferenceUrl(''); setRefName(''); }} className="ml-auto text-xs text-gray-500 hover:text-rose-400" aria-label="移除参考图">✕</button>
          </div>
        ) : (
          <button type="button" onClick={() => fileInputRef.current?.click()} disabled={refUploading || !uploadImage}
            className={`flex w-full items-center justify-center gap-2 rounded-lg px-3 py-2.5 text-xs ${dashBox} disabled:opacity-50`}>
            {refUploading ? '上传中…' : '＋ 上传产品 / 参照图'}
          </button>
        )}
      </div>

      {/* 操作区 */}
      <div className="flex items-center gap-2 pt-1">
        <button type="button" disabled={!canSubmit} onClick={handleStart}
          className={`flex-1 rounded-xl px-4 py-2.5 text-sm font-medium transition-colors ${
            canSubmit ? 'bg-indigo-500 text-white hover:bg-indigo-600'
              : isLight ? 'cursor-not-allowed bg-gray-100 text-gray-400' : 'cursor-not-allowed bg-white/5 text-gray-500'}`}>
          {canSubmit ? '开始生成' : '填齐必填项后开始生成'}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel}
            className={`rounded-xl px-3 py-2.5 text-sm ${isLight ? 'text-gray-500 hover:bg-gray-100' : 'text-gray-400 hover:bg-white/5'}`}>取消</button>
        )}
      </div>
    </div>
  );
}
