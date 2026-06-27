import { useState, useEffect } from 'react';
import type { ProductBrief } from '../types';

interface FieldConfig {
  key: keyof ProductBrief;
  label: string;
  icon: string;
  type: 'text' | 'tags' | 'date';
  readonly?: boolean;
}

const FIELD_CONFIG: FieldConfig[] = [
  { key: 'brand_name', label: '品牌名', icon: '🏢', type: 'text' },
  { key: 'product_name', label: '产品名', icon: '📦', type: 'text' },
  { key: 'category', label: '品类', icon: '🏷️', type: 'text' },
  { key: 'target_audience', label: '目标受众', icon: '👥', type: 'text' },
  { key: 'usage_scenarios', label: '使用场景', icon: '🎯', type: 'tags' },
  { key: 'selling_points', label: '核心卖点', icon: '💎', type: 'tags' },
  { key: 'brand_style', label: '品牌风格', icon: '🎨', type: 'text' },
  { key: 'target_country', label: '目标国家', icon: '🌍', type: 'text' },
  { key: 'cultural_taboos', label: '文化禁忌', icon: '⚠️', type: 'text' },
  { key: 'publish_platform', label: '发布平台', icon: '📱', type: 'text' },
  { key: 'scheduled_date', label: '预发布日期', icon: '📅', type: 'date' },
  { key: 'promotional_event', label: '促销活动', icon: '🎉', type: 'text', readonly: true },
];

function inferPromotionalEvent(date: string): string {
  if (!date) return '';
  const parts = date.split('-').map(Number);
  if (parts.length !== 3) return '';
  const [_, month, day] = parts;
  if (month === 6 && day >= 15 && day <= 20) return '618购物节';
  if (month === 11 && day >= 9 && day <= 12) return '双十一';
  if (month === 12 && day >= 10 && day <= 14) return '双十二';
  if (month === 3 && day >= 6 && day <= 10) return '女神节';
  if (month === 5 && day === 20) return '520';
  return '';
}

interface Props {
  brief: ProductBrief;
  missing: string[];
  onConfirm: (updatedBrief: ProductBrief) => void;
  onReupload: () => void;
}

export default function BriefReviewPanel({ brief, onConfirm, onReupload }: Props) {
  const [editing, setEditing] = useState<string | null>(null);
  const [localBrief, setLocalBrief] = useState(brief);

  useEffect(() => {
    setLocalBrief(brief);
  }, [brief]);

  useEffect(() => {
    if (localBrief.scheduled_date) {
      const event = inferPromotionalEvent(localBrief.scheduled_date);
      if (event !== localBrief.promotional_event) {
        setLocalBrief(prev => ({ ...prev, promotional_event: event }));
      }
    }
  }, [localBrief.scheduled_date]);

  const getValue = (key: keyof ProductBrief) => {
    const val = localBrief[key];
    if (Array.isArray(val)) return val;
    return val || '';
  };

  const isEmpty = (key: keyof ProductBrief) => {
    const val = getValue(key);
    return Array.isArray(val) ? val.length === 0 : !val;
  };

  const handleConfirm = () => {
    onConfirm(localBrief);
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em] text-orange-200/90">
          Brief 确认
        </div>
        <div className="flex items-center gap-3">
          <span className="text-2xl">📋</span>
          <h2 className="text-xl font-semibold text-white">解析产品信息如下，如有空缺请补充</h2>
        </div>
      </div>

      <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {FIELD_CONFIG.map(field => {
          const isMissing = isEmpty(field.key);
          const isEditing = editing === field.key;
          const value = getValue(field.key);

          return (
            <div
              key={field.key}
              className={`liquid-card p-4 cursor-pointer transition-all hover:scale-[1.02] ${
                isMissing
                  ? 'border-2 border-dashed border-orange-500/50 bg-orange-950/10'
                  : 'border border-white/10 bg-white/5'
              }`}
              onClick={() => !field.readonly && !isEditing && setEditing(field.key)}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{field.icon}</span>
                  <span className="text-sm font-medium text-gray-300">{field.label}</span>
                </div>
                {isMissing && <span className="text-orange-400">⚠️</span>}
                {!isMissing && !field.readonly && !isEditing && (
                  <span className="text-gray-500 text-xs">✏️</span>
                )}
              </div>

              {isEditing ? (
                field.type === 'tags' ? (
                  <textarea
                    autoFocus
                    className="w-full bg-black/30 border border-white/20 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-orange-500"
                    value={Array.isArray(value) ? value.join(', ') : ''}
                    onChange={e => {
                      const tags = e.target.value.split(',').map(t => t.trim()).filter(Boolean);
                      setLocalBrief(prev => ({ ...prev, [field.key]: tags }));
                    }}
                    onBlur={() => setEditing(null)}
                    rows={3}
                    placeholder="多个值用逗号分隔"
                  />
                ) : (
                  <input
                    autoFocus
                    type={field.type === 'date' ? 'date' : 'text'}
                    className="w-full bg-black/30 border border-white/20 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-orange-500"
                    value={value as string}
                    onChange={e => setLocalBrief(prev => ({ ...prev, [field.key]: e.target.value }))}
                    onBlur={() => setEditing(null)}
                    onKeyDown={e => e.key === 'Enter' && setEditing(null)}
                  />
                )
              ) : (
                <div className="text-sm text-gray-400 min-h-[60px]">
                  {isMissing ? (
                    <span className="text-orange-400/60 italic">请补充...</span>
                  ) : field.type === 'tags' && Array.isArray(value) ? (
                    <div className="flex flex-wrap gap-1">
                      {value.map((tag, i) => (
                        <span key={i} className="px-2 py-0.5 bg-white/10 rounded text-xs text-gray-300">
                          {tag}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-gray-200">{value as string}</span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="flex gap-3 pt-4">
        <button
          onClick={handleConfirm}
          className="flex-1 py-3 bg-orange-500 hover:bg-orange-400 text-white rounded-xl font-semibold transition-all shadow-lg shadow-orange-500/20"
        >
          ✅ 确认并生成
        </button>
        <button
          onClick={onReupload}
          className="px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 rounded-xl transition-all"
        >
          🔄 重新上传
        </button>
      </div>
    </div>
  );
}
