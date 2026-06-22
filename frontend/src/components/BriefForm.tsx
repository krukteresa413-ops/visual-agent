// @ts-nocheck
import type { ProductBrief } from '../types';

interface Props { value: ProductBrief; onChange: (v: ProductBrief) => void; }

const toArr = (s: string) => s.split(/[，,\n]/).map(v => v.trim()).filter(Boolean);
const joinArr = (arr: string[]) => arr.join('，');

export default function BriefForm({ value, onChange }: Props) {
  const set = (field: keyof ProductBrief) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const raw = e.target.value;
    const arrFields = ['specifications','selling_points','target_market','usage_scenarios','materials','target_customer','compliance_notes'];
    if ((arrFields as string[]).includes(field as string)) {
      onChange({ ...value, [field]: toArr(raw) });
    } else {
      onChange({ ...value, [field]: raw });
    }
  };

  const baseInput = 'w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-gray-100 placeholder-gray-600 focus:border-orange-500/50 focus:outline-none focus:ring-1 focus:ring-orange-500/20 transition-all duration-200';
  const labelCls = 'block text-xs font-medium text-gray-400 mb-1.5';

  const fields: [string, keyof ProductBrief, string, boolean][] = [
    ['产品名称 *', 'product_name', 'e.g. Commercial Chest Freezer', false],
    ['产品品类 *', 'category', 'e.g. Commercial Refrigeration', false],
    ['核心规格 *', 'specifications', '300L, stainless steel, low noise', true],
    ['主要卖点 *', 'selling_points', 'fast cooling, energy saving', true],
    ['目标用户 *', 'target_audience', 'e.g. 25-35岁女性, 跑步爱好者, 注重颜值', false],
    ['目标市场 *', 'target_market', 'US, EU, Middle East', true],
    ['使用场景', 'usage_scenarios', 'supermarket, restaurant', true],
    ['品牌风格', 'brand_style', 'professional, clean', false],
  ];

  return (
    <div className="space-y-4">
      {fields.map(([label, field, placeholder, isTextarea]) => (
        <div key={field}>
          <label className={labelCls}>{label} <span className="text-gray-600 text-[10px]">（{isTextarea ? '逗号分隔' : '选填'}）</span></label>
          {isTextarea ? (
            <textarea className={baseInput + ' resize-none'} rows={3} placeholder={placeholder}
              value={joinArr(value[field] as string[] || [])} onChange={set(field)} />
          ) : (
            <input className={baseInput} placeholder={placeholder}
              value={(value[field] as string) || ''} onChange={set(field)} />
          )}
        </div>
      ))}
      <div>
        <label className={labelCls}>受众类型 <span className="text-gray-600 text-[10px]">（B2B/B2C）</span></label>
        <div className="flex gap-2">
          {( ['B2B','B2C','Both'] as const ).map(t => (
            <button key={t} onClick={() => onChange({...value, audience_type: t})}
              className={'flex-1 py-2 text-xs rounded-lg border transition-colors ' + (((value as any).audience_type===t || (!(value as any).audience_type && t==='B2B')) ? 'border-orange-500 bg-orange-950/30 text-orange-200' : 'border-gray-700 bg-gray-900 text-gray-500 hover:border-gray-600')}>
              {t==='B2B' ? 'B2B 批发' : t==='B2C' ? 'B2C 零售' : 'Both 双模'}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
