/**
 * ScoreCard — Quality evaluation score display.
 *
 * Shows multi-dimensional quality scores for generated assets:
 * - Composition (构图)
 * - Color Harmony (色彩协调)
 * - Commercial Appeal (商业适用性)
 *
 * Usage:
 *   <ScoreCard
 *     report={qualityReport}
 *     isLight={isLight}
 *     onClose={() => setShowScore(false)}
 *   />
 */
import { useState } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface QualityDimension {
  name: string;
  name_cn: string;
  score: number;       // 1-10
  reasoning: string;
  suggestion: string;
}

interface QualityReport {
  dimensions: QualityDimension[];
  overall_score: number;
  summary: string;
  model_used?: string;
}

interface Props {
  report: QualityReport | null;
  isLight?: boolean;
  onClose?: () => void;
  onAskMore?: (dimension: string) => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function scoreColor(score: number): string {
  if (score >= 8) return 'text-green-500';
  if (score >= 6) return 'text-yellow-500';
  return 'text-red-500';
}

function scoreBg(score: number): string {
  if (score >= 8) return 'bg-green-500';
  if (score >= 6) return 'bg-yellow-500';
  return 'bg-red-500';
}

function scoreLabel(score: number): string {
  if (score >= 9) return '优秀';
  if (score >= 7) return '良好';
  if (score >= 5) return '一般';
  return '需改进';
}

function dimensionIcon(name: string): string {
  switch (name) {
    case 'composition': return '🎨';
    case 'color_harmony': return '🌈';
    case 'commercial_appeal': return '💼';
    default: return '📊';
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function ScoreCard({ report, isLight, onClose, onAskMore }: Props) {
  const [expandedDim, setExpandedDim] = useState<string | null>(null);

  if (!report || !report.dimensions || report.dimensions.length === 0) {
    return null;
  }

  const bg = isLight
    ? 'bg-white/95 border-gray-200'
    : 'bg-gray-900/95 border-gray-700';
  const textColor = isLight ? 'text-gray-900' : 'text-white';
  const subText = isLight ? 'text-gray-500' : 'text-gray-400';

  return (
    <div className={`${bg} border shadow-2xl rounded-2xl overflow-hidden`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200/50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">📊</span>
          <div>
            <h3 className={`text-sm font-semibold ${textColor}`}>质量评估</h3>
            <p className={`text-[10px] ${subText}`}>
              大模型生成 · 小模型评估
            </p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className={`text-xs ${subText} hover:text-orange-500`}
          >
            ✕
          </button>
        )}
      </div>

      {/* Overall Score */}
      <div className="px-4 py-3 flex items-center gap-3">
        <div className={`w-14 h-14 rounded-2xl ${scoreBg(report.overall_score)} flex items-center justify-center`}>
          <span className="text-white text-xl font-bold">{report.overall_score}</span>
        </div>
        <div className="flex-1">
          <div className={`text-sm font-medium ${textColor}`}>
            综合评分 · {scoreLabel(report.overall_score)}
          </div>
          <p className={`text-[11px] ${subText} mt-0.5`}>{report.summary}</p>
        </div>
      </div>

      {/* Dimensions */}
      <div className="px-4 pb-3 space-y-2">
        {report.dimensions.map((dim) => (
          <div key={dim.name}>
            <div
              className="flex items-center gap-2 cursor-pointer py-1"
              onClick={() => setExpandedDim(expandedDim === dim.name ? null : dim.name)}
            >
              <span className="text-sm">{dimensionIcon(dim.name)}</span>
              <span className={`text-xs font-medium flex-1 ${textColor}`}>
                {dim.name_cn}
              </span>
              <div className="flex items-center gap-1.5">
                {/* Mini bar */}
                <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${scoreBg(dim.score)}`}
                    style={{ width: `${dim.score * 10}%` }}
                  />
                </div>
                <span className={`text-xs font-bold ${scoreColor(dim.score)} w-5 text-right`}>
                  {dim.score}
                </span>
              </div>
            </div>

            {/* Expanded details */}
            {expandedDim === dim.name && (
              <div className={`ml-7 mt-1 mb-2 p-2 rounded-lg ${isLight ? 'bg-gray-50' : 'bg-gray-800'}`}>
                <p className={`text-[11px] ${textColor}`}>{dim.reasoning}</p>
                {dim.suggestion && (
                  <div className="mt-1.5 flex items-start gap-1.5">
                    <span className="text-[10px]">💡</span>
                    <p className={`text-[10px] ${subText}`}>{dim.suggestion}</p>
                  </div>
                )}
                {onAskMore && (
                  <button
                    onClick={() => onAskMore(dim.name_cn)}
                    className="mt-1.5 text-[10px] text-orange-500 hover:text-orange-400"
                  >
                    对此项进行优化 →
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      {report.model_used && (
        <div className={`px-4 py-1.5 border-t border-gray-200/50 text-[9px] ${subText}`}>
          评估模型: {report.model_used}
        </div>
      )}
    </div>
  );
}
