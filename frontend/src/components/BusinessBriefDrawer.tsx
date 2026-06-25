/**
 * BusinessBriefDrawer — 商务出图抽屉壳（Part 2，v2）
 *
 * 纯展示组件：在右侧 AI 对话列里就地展开，收集结构化商务 brief 字段，
 * 校验必填后通过 onSubmit 吐出一个 plain brief 对象。
 * 不依赖后端类型，不自行发起生成（生成由 AIChatPanel 负责）。
 * 不含资料库自动填（Part 3 再接）。
 *
 * v2 变更：
 *  - 必填标记由 · 改为醒目红色 *。
 *  - 删除「商品/品牌名」「核心卖点」的示例占位文本。
 *  - 平台提示去掉「（可改）」。
 *  - 平台改为 内部存 platform_id（taobao/jd/...）、界面显示中文，
 *    对齐后端 platform_specs / platform_prompt_loader 的匹配键。
 *
 * 字段→后端 brief_parser 字段名对齐：
 *   上架平台   → upload_platform   (必填，存 platform_id)
 *   商品/品牌名 → product_name      (必填)
 *   核心卖点   → selling_points    (必填)
 *   目标受众   → target_customer
 *   风格关键词 → brand_style
 *   禁忌/合规  → compliance_notes
 *   语言/市场  → target_market
 * 另带 _mode: 'business' 作为来源标记。
 */
import { useState } from 'react';

export interface BusinessBrief {
  upload_platform: string; // platform_id, e.g. 'taobao'
  product_name: string;
  selling_points: string;
  target_customer?: string;
  brand_style?: string;
  compliance_notes?: string;
  target_market?: string;
  _mode: 'business';
}

interface BusinessBriefDrawerProps {
  isLight: boolean;
  onSubmit: (brief: BusinessBrief) => void;
  onCancel?: () => void;
}

// id 对齐后端 platform_specs / platform_prompt_loader 的匹配键；label 仅用于显示
const PLATFORMS: { id: string; label: string; hint: string }[] = [
  { id: 'taobao', label: '淘宝 / 天猫', hint: '主图 800×800 · 详情页首屏 · 白底 / 场景图 · 极限词合规' },
  { id: 'jd', label: '京东', hint: '主图 800×800 · 详情页 · 品质感 · 资质合规' },
  { id: 'pinduoduo', label: '拼多多', hint: '主图 750×750 · 主推卖点图' },
  { id: 'xiaohongshu', label: '小红书', hint: '封面 1080×1440(3:4) · 种草调性 · 标签话题' },
  { id: 'douyin', label: '抖音', hint: '9:16 竖版 · 短视频封面 · 强钩子首图' },
  { id: 'amazon', label: '亚马逊', hint: '主图白底 2000×2000 · 英文文案 · A+ 结构化' },
  { id: 'alibaba_intl', label: '阿里国际站', hint: '英文 / 多语 · B2B 详情 · 跨境合规' },
];

export default function BusinessBriefDrawer({ isLight, onSubmit, onCancel }: BusinessBriefDrawerProps) {
  const [platform, setPlatform] = useState(''); // platform_id
  const [productName, setProductName] = useState('');
  const [sellingPoints, setSellingPoints] = useState('');
  const [targetCustomer, setTargetCustomer] = useState('');
  const [brandStyle, setBrandStyle] = useState('');
  const [compliance, setCompliance] = useState('');
  const [market, setMarket] = useState('');

  const canSubmit =
    platform.trim() !== '' && productName.trim() !== '' && sellingPoints.trim() !== '';

  const selectedHint = PLATFORMS.find((p) => p.id === platform)?.hint;

  // 主题样式
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

  // 醒目必填标记
  const Req = () => <span className="ml-0.5 text-rose-500 font-bold text-base leading-none">*</span>;

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
      _mode: 'business',
    });
  };

  return (
    <div data-testid="business-brief-drawer" className="space-y-4 text-sm">
      {/* 上架平台（龙头，必填） */}
      <div>
        <div className={`mb-1.5 ${label}`}>
          上架平台<Req />
        </div>
        <div className="flex flex-wrap gap-1.5">
          {PLATFORMS.map((p) => (
            <span
              key={p.id}
              role="button"
              tabIndex={0}
              onClick={() => setPlatform(p.id)}
              className={`${chipBase} ${platform === p.id ? chipOn : chipOff}`}
            >
              {p.label}
            </span>
          ))}
        </div>
        {selectedHint && (
          <div className={`mt-2 rounded-lg px-3 py-2 text-xs ${hintBox}`}>
            按平台自动带出：{selectedHint}
          </div>
        )}
      </div>

      {/* 商品 / 品牌名（必填） */}
      <div>
        <div className={`mb-1.5 ${label}`}>
          商品 / 品牌名<Req />
        </div>
        <input
          className={field}
          value={productName}
          onChange={(e) => setProductName(e.target.value)}
        />
      </div>

      {/* 核心卖点（必填） */}
      <div>
        <div className={`mb-1.5 ${label}`}>
          核心卖点<Req />
        </div>
        <textarea
          className={`${field} resize-y`}
          rows={2}
          value={sellingPoints}
          onChange={(e) => setSellingPoints(e.target.value)}
        />
      </div>

      {/* 选填两列 */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className={`mb-1.5 ${labelMuted}`}>目标受众</div>
          <input
            className={field}
            value={targetCustomer}
            onChange={(e) => setTargetCustomer(e.target.value)}
            placeholder="选填"
          />
        </div>
        <div>
          <div className={`mb-1.5 ${labelMuted}`}>风格关键词</div>
          <input
            className={field}
            value={brandStyle}
            onChange={(e) => setBrandStyle(e.target.value)}
            placeholder="选填"
          />
        </div>
        <div>
          <div className={`mb-1.5 ${labelMuted}`}>禁忌 / 合规</div>
          <input
            className={field}
            value={compliance}
            onChange={(e) => setCompliance(e.target.value)}
            placeholder="选填"
          />
        </div>
        <div>
          <div className={`mb-1.5 ${labelMuted}`}>语言 / 市场</div>
          <input
            className={field}
            value={market}
            onChange={(e) => setMarket(e.target.value)}
            placeholder="中文 · 选填"
          />
        </div>
      </div>

      {/* 操作区 */}
      <div className="flex items-center gap-2 pt-1">
        <button
          type="button"
          disabled={!canSubmit}
          onClick={handleStart}
          className={`flex-1 rounded-xl px-4 py-2.5 text-sm font-medium transition-colors ${
            canSubmit
              ? 'bg-indigo-500 text-white hover:bg-indigo-600'
              : isLight
                ? 'cursor-not-allowed bg-gray-100 text-gray-400'
                : 'cursor-not-allowed bg-white/5 text-gray-500'
          }`}
        >
          {canSubmit ? '开始生成' : '填齐必填项后开始生成'}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className={`rounded-xl px-3 py-2.5 text-sm ${
              isLight ? 'text-gray-500 hover:bg-gray-100' : 'text-gray-400 hover:bg-white/5'
            }`}
          >
            取消
          </button>
        )}
      </div>
    </div>
  );
}
