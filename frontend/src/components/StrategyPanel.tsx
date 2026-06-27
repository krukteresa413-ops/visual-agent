interface StrategyData {
  visual_positioning: string;
  target_customer_analysis?: string;
  visual_style: string;
  selling_points_priority: Array<{rank:number;point:string;rationale:string}>;
  asset_plan_summary?: Record<string,string>;
  brand_tone: string;
  audience_type: string;
  key_differentiators: string;
}

interface Props {
  strategy: StrategyData;
  onConfirm: () => void;
  onRetry: () => void;
  loading: boolean;
}

const ASSET_LABELS: Record<string,string> = {
  main_image: '主图', white_bg: '白底图', scene_images: '场景图',
  selling_points: '卖点图', video_scripts: '视频脚本', ad_material: '广告素材',
};

export default function StrategyPanel({ strategy, onConfirm, onRetry, loading }: Props) {
  const sp = strategy.selling_points_priority || [];

  return (
    <div className="liquid-card p-6 w-full max-w-xl mx-auto space-y-5">
      <div className="text-center space-y-1">
        <div className="mb-1 inline-flex items-center gap-2 rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em] text-orange-200/90">
          创意策略
        </div>
        <div className="text-orange-400 text-2xl">💡</div>
        <h3 className="text-sm font-medium text-gray-100">AI 创意策略</h3>
        <p className="text-xs text-gray-500">
          以下是 Agent 为你制定的视觉方向，确认后开始生成素材
        </p>
      </div>

      {/* Positioning + Audience */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white/5 rounded-xl p-3 space-y-1">
          <span className="text-[10px] text-gray-500">品牌定位</span>
          <p className="text-xs text-gray-200">{strategy.visual_positioning}</p>
        </div>
        <div className="bg-white/5 rounded-xl p-3 space-y-1">
          <span className="text-[10px] text-gray-500">受众</span>
          <p className="text-xs text-gray-200">
            <span className={`px-1.5 py-0.5 rounded text-[10px] ${
              strategy.audience_type === 'B2B'
                ? 'bg-blue-500/20 text-blue-300'
                : 'bg-pink-500/20 text-pink-300'
            }`}>{strategy.audience_type}</span>
          </p>
          {strategy.target_customer_analysis && (
            <p className="text-[10px] text-gray-500">{strategy.target_customer_analysis}</p>
          )}
        </div>
      </div>

      {/* Visual Style + Tone */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white/5 rounded-xl p-3 space-y-1">
          <span className="text-[10px] text-gray-500">视觉风格</span>
          <p className="text-xs text-gray-200">{strategy.visual_style}</p>
        </div>
        <div className="bg-white/5 rounded-xl p-3 space-y-1">
          <span className="text-[10px] text-gray-500">品牌语调</span>
          <p className="text-xs text-gray-200">{strategy.brand_tone}</p>
        </div>
      </div>

      {/* Selling points priority */}
      {sp.length > 0 && (
        <div className="space-y-2">
          <span className="text-[10px] text-gray-500">卖点优先级</span>
          <div className="space-y-1.5">
            {sp.map((s) => (
              <div key={s.rank} className="flex items-center gap-2 bg-white/5 rounded-lg px-3 py-2">
                <span className="w-5 h-5 rounded-full bg-orange-500/20 text-orange-400 text-[10px] flex items-center justify-center font-medium">
                  {s.rank}
                </span>
                <div>
                  <p className="text-xs text-gray-200">{s.point}</p>
                  <p className="text-[10px] text-gray-600">{s.rationale}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Asset plan summary */}
      {strategy.asset_plan_summary && (
        <div className="space-y-2">
          <span className="text-[10px] text-gray-500">素材规划</span>
          <div className="grid grid-cols-2 gap-1.5">
            {Object.entries(strategy.asset_plan_summary).map(([key, val]) => (
              <div key={key} className="bg-white/5 rounded-lg px-3 py-2">
                <span className="text-[10px] text-gray-600">{ASSET_LABELS[key] || key}</span>
                <p className="text-[10px] text-gray-300 truncate">{val}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Key differentiators */}
      <div className="bg-orange-500/5 border border-orange-500/10 rounded-xl p-3">
        <span className="text-[10px] text-orange-400">核心差异化</span>
        <p className="text-xs text-gray-200 mt-1">{strategy.key_differentiators}</p>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-2 border-t border-white/5">
        <button
          onClick={onRetry}
          disabled={loading}
          className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
        >
          🔄 换个方向
        </button>
        <button
          onClick={onConfirm}
          disabled={loading}
          className="px-6 py-2.5 bg-orange-500 hover:bg-orange-400 disabled:opacity-30 rounded-lg text-sm font-medium transition-all"
        >
          {loading ? '生成中...' : '确认，开始生成素材'}
        </button>
      </div>
    </div>
  );
}
