import { useMemo, useState } from 'react';
import CopywritingPanel from '../components/CopywritingPanel';

export default function CopywritingPage() {
  const [productName, setProductName] = useState('');
  const [desc, setDesc] = useState('');
  const [audience, setAudience] = useState('');
  const [ready, setReady] = useState(false);

  const brief = useMemo(
    () => ({
      product_name: productName.trim() || '产品',
      brand_name: productName.trim(),
      target_audience: audience.trim(),
      description: desc.trim(),
      selling_points: desc.split(/[,，\n]/).map((s) => s.trim()).filter(Boolean),
    }),
    [productName, desc, audience],
  );

  const canStart = !!(productName.trim() || desc.trim());

  return (
    <div className="min-h-[60vh] px-6 py-8 text-white">
      <div className="mx-auto w-full max-w-2xl space-y-5">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em] text-orange-200/90">
            AI 文案助手
          </div>
          <h1 className="text-2xl font-bold tracking-tight md:text-3xl">AI 文案助手</h1>
          <p className="mt-1 text-sm text-gray-400">
            输入产品信息,一键生成电商卖点 / 小红书标题 / 抖音口播 / 海报主标题 / 促销文案 / 品牌 Slogan,并自动做广告法合规检查。
          </p>
        </div>

        <div className="space-y-3 rounded-3xl border border-white/[0.12] bg-white/[0.04] p-5">
          <Field label="产品 / 品牌名称">
            <input value={productName} onChange={(e) => setProductName(e.target.value)} placeholder="例如:栖岚防晒衣" className={inputCls} />
          </Field>
          <Field label="目标受众(可选)">
            <input value={audience} onChange={(e) => setAudience(e.target.value)} placeholder="例如:25-35 岁都市女性" className={inputCls} />
          </Field>
          <Field label="产品描述 / 核心卖点(逗号或换行分隔)">
            <textarea value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="轻薄, 防晒 UPF50+, 冰感, 通勤户外两穿" className={inputCls + ' min-h-[88px] resize-y py-2'} />
          </Field>
          <button
            onClick={() => setReady(true)}
            disabled={!canStart}
            className="rounded-lg bg-gradient-to-r from-orange-500 to-rose-500 px-4 py-2 text-sm font-medium text-white transition-transform hover:scale-[1.02] disabled:opacity-50"
          >
            下一步:生成文案
          </button>
        </div>

        {ready && canStart && <CopywritingPanel brief={brief} />}
      </div>
    </div>
  );
}

const inputCls = 'w-full rounded-lg border border-white/[0.1] bg-white/[0.04] px-3 py-2 text-sm text-white placeholder:text-gray-600 outline-none transition-colors focus:border-orange-400/40';

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-gray-400">{label}</label>
      {children}
    </div>
  );
}
