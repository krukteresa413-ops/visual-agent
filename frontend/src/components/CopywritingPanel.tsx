import { useState } from 'react';

interface CopyItem {
  headline: string;
  body: string;
  cta: string;
  compliance: Array<{type:string;matched:string;suggestion:string}>;
  error?: string;
}

interface Props {
  brief: any;
}

const TYPE_LABELS: Record<string,{icon:string;label:string}> = {
  ecommerce_selling_point: { icon: '🛒', label: '电商卖点文案' },
  xiaohongshu_title: { icon: '📕', label: '小红书标题' },
  douyin_voiceover: { icon: '🎵', label: '抖音口播' },
  poster_headline: { icon: '🎯', label: '海报主标题' },
  promo_copy: { icon: '🔥', label: '活动促销文案' },
  brand_slogan: { icon: '💎', label: '品牌 Slogan' },
};

export default function CopywritingPanel({ brief }: Props) {
  const [copies, setCopies] = useState<Record<string,CopyItem>|null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<string>('');
  const [copied, setCopied] = useState('');

  const generate = async () => {
    setLoading(true);
    try {
      const resp = await fetch('/api/v1/copywriting/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brief, copy_types: ['all'] }),
      });
      const data = await resp.json();
      setCopies(data);
      setActiveTab(Object.keys(data)[0] || '');
    } catch (e) {
      // silent fail
    }
    finally { setLoading(false); }
  };

  const copyText = async (text: string, key: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(''), 1500);
  };

  const activeCopy = copies?.[activeTab];

  return (
    <div className="liquid-card p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">✍️</span>
          <h3 className="text-sm font-medium text-gray-200">AI 文案</h3>
        </div>
        {!copies && (
          <button onClick={generate} disabled={loading}
            className="px-3 py-1.5 bg-orange-500/20 hover:bg-orange-500/30 disabled:opacity-30 text-orange-300 rounded-lg text-xs">
            {loading ? '生成中...' : '生成文案'}
          </button>
        )}
      </div>

      {copies && (
        <>
          {/* Tabs */}
          <div className="flex flex-wrap gap-1">
            {Object.keys(TYPE_LABELS).filter(k => copies[k]).map(k => (
              <button key={k} onClick={() => setActiveTab(k)}
                className={`px-2.5 py-1 rounded-full text-[10px] transition-all ${
                  activeTab === k
                    ? 'bg-orange-500/15 text-orange-300 border border-orange-500/20'
                    : 'bg-white/5 text-gray-500 hover:text-gray-300 border border-white/5'
                }`}>
                {TYPE_LABELS[k]?.icon} {TYPE_LABELS[k]?.label}
              </button>
            ))}
          </div>

          {/* Active copy */}
          {activeCopy && (
            <div className="space-y-3">
              {activeCopy.error ? (
                <p className="text-xs text-red-400">生成失败：{activeCopy.error}</p>
              ) : (
                <>
                  <div className="bg-white/5 rounded-xl p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-gray-500">标题</span>
                      <button onClick={() => copyText(activeCopy.headline, 'headline')}
                        className="text-[10px] text-gray-600 hover:text-gray-300">
                        {copied === 'headline' ? '已复制' : '复制'}
                      </button>
                    </div>
                    <p className="text-sm text-gray-100 font-medium">{activeCopy.headline}</p>
                  </div>
                  <div className="bg-white/5 rounded-xl p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-gray-500">正文</span>
                      <button onClick={() => copyText(activeCopy.body, 'body')}
                        className="text-[10px] text-gray-600 hover:text-gray-300">
                        {copied === 'body' ? '已复制' : '复制'}
                      </button>
                    </div>
                    <p className="text-xs text-gray-300 leading-relaxed">{activeCopy.body}</p>
                  </div>
                  {activeCopy.cta && (
                    <div className="bg-white/5 rounded-xl p-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-gray-500">行动号召</span>
                        <button onClick={() => copyText(activeCopy.cta, 'cta')}
                          className="text-[10px] text-gray-600 hover:text-gray-300">
                          {copied === 'cta' ? '已复制' : '复制'}
                        </button>
                      </div>
                      <p className="text-xs text-orange-300">{activeCopy.cta}</p>
                    </div>
                  )}

                  {/* Compliance warnings */}
                  {activeCopy.compliance && activeCopy.compliance.length > 0 && (
                    <div className="bg-red-500/5 border border-red-500/10 rounded-xl p-3">
                      <span className="text-[10px] text-red-400">⚠️ 合规提醒</span>
                      {activeCopy.compliance.map((w, i) => (
                        <p key={i} className="text-[10px] text-red-400/70 mt-1">
                          「{w.matched}」— {w.suggestion}
                        </p>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
