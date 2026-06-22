/**
 * WorkflowSidebar — shows real-time generation progress as workflow steps.
 *
 * Day 2 update: accepts generationProgress prop to drive real-time step
 * highlighting instead of hardcoded fake steps.
 */
import { useState } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Step {
  key: string;
  label: string;
  icon: string;
  status: 'done' | 'active' | 'pending';
  desc: string;
  progress?: number;
  detail?: string;
}

interface GenerationProgress {
  step: string;
  percent: number;
  status: string;
  message: string;
}

interface Props {
  projectName?: string;
  steps?: Step[];
  generationProgress?: GenerationProgress | null;
}

// ---------------------------------------------------------------------------
// Step definitions — mapped to real generation steps
// ---------------------------------------------------------------------------

const STEP_MAP: Record<string, { key: string; label: string; icon: string }> = {
  '分析需求': { key: 'brief', label: '分析需求', icon: '🔍' },
  '策略规划': { key: 'mood', label: '策略规划', icon: '🎯' },
  '生成主图': { key: 'concept', label: '生成主图', icon: '🖼️' },
  '生成白底图': { key: 'refine', label: '生成白底图', icon: '📷' },
  '生成场景图': { key: 'refine', label: '生成场景图', icon: '🌆' },
  '生成卖点文案': { key: 'adapt', label: '生成文案', icon: '✍️' },
  '生成视频脚本': { key: 'adapt', label: '视频脚本', icon: '🎬' },
  '生成广告素材': { key: 'adapt', label: '广告素材', icon: '📢' },
  '排版布局': { key: 'review', label: '排版布局', icon: '📐' },
  '完成': { key: 'review', label: '审核导出', icon: '✅' },
};

function buildSteps(progress: GenerationProgress | null | undefined): Step[] {
  if (!progress) {
    // Show idle state
    return [
      { key: 'brief', label: '分析需求', icon: '🔍', status: 'pending', desc: '等待开始生成...' },
      { key: 'mood', label: '策略规划', icon: '🎯', status: 'pending', desc: '' },
      { key: 'concept', label: '素材生成', icon: '⚡', status: 'pending', desc: '' },
      { key: 'refine', label: '精细调整', icon: '🔧', status: 'pending', desc: '' },
      { key: 'adapt', label: '多端适配', icon: '📱', status: 'pending', desc: '' },
      { key: 'review', label: '审核导出', icon: '✅', status: 'pending', desc: '' },
    ];
  }

  const currentStepKey = STEP_MAP[progress.step]?.key || null;
  const isDone = progress.status === 'done';

  const allSteps: Step[] = [
    { key: 'brief', label: '分析需求', icon: '🔍', status: 'pending', desc: '分析产品定位和需求', progress: 0 },
    { key: 'mood', label: '策略规划', icon: '🎯', status: 'pending', desc: '确定创意方向', progress: 0 },
    { key: 'concept', label: '素材生成', icon: '⚡', status: 'pending', desc: '生成主图和场景图', progress: 0 },
    { key: 'refine', label: '精细调整', icon: '🔧', status: 'pending', desc: '白底图和细节优化', progress: 0 },
    { key: 'adapt', label: '多端适配', icon: '📱', status: 'pending', desc: '视频脚本和广告素材', progress: 0 },
    { key: 'review', label: '审核导出', icon: '✅', status: 'pending', desc: '排版布局和最终审核', progress: 0 },
  ];

  if (isDone) {
    return allSteps.map(s => ({
      ...s,
      status: 'done' as const,
      progress: 100,
      desc: s.key === 'review' ? '生成完成，可查看结果' : '已完成',
    }));
  }

  return allSteps.map(s => {
    if (s.key === currentStepKey) {
      return {
        ...s,
        status: 'active' as const,
        progress: progress.percent,
        desc: progress.message,
        detail: `${progress.percent}%`,
      };
    }
    // Mark steps before current as done
    const stepOrder = ['brief', 'mood', 'concept', 'refine', 'adapt', 'review'];
    const currentIdx = stepOrder.indexOf(currentStepKey || '');
    const thisIdx = stepOrder.indexOf(s.key);
    if (thisIdx < currentIdx) {
      return { ...s, status: 'done' as const, progress: 100 };
    }
    return s;
  });
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function WorkflowSidebar({
  projectName = '未命名项目',
  generationProgress,
}: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const steps = buildSteps(generationProgress);

  if (collapsed) {
    return (
      <div className="w-10 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col items-center py-3 gap-3">
        <button onClick={() => setCollapsed(false)}
          className="w-7 h-7 rounded-lg bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-500 text-xs"
          title="展开工作流">→</button>
        {steps.map(s => (
          <div key={s.key} className="relative" title={`${s.label}: ${s.desc}`}>
            <div className={`w-2.5 h-2.5 rounded-full ${
              s.status === 'done' ? 'bg-green-400' :
              s.status === 'active' ? 'bg-orange-400 animate-pulse' : 'bg-gray-300'
            }`} />
          </div>
        ))}
      </div>
    );
  }

  const doneCount = steps.filter(s => s.status === 'done').length;
  const isActive = generationProgress && generationProgress.status !== 'done' && generationProgress.status !== 'error';

  return (
    <div className="w-56 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-gray-700 truncate">{projectName}</h3>
          <button onClick={() => setCollapsed(true)}
            className="w-5 h-5 rounded hover:bg-gray-100 flex items-center justify-center text-gray-400 text-xs"
            title="收起">←</button>
        </div>
        <div className="flex items-center gap-1.5 mt-0.5">
          <p className="text-[10px] text-gray-400">创作工作流</p>
          {isActive && (
            <span className="flex gap-0.5">
              <span className="w-1 h-1 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1 h-1 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '100ms' }} />
              <span className="w-1 h-1 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '200ms' }} />
            </span>
          )}
        </div>
      </div>

      {/* Steps */}
      <div className="flex-1 overflow-y-auto py-2">
        {steps.map((step, i) => (
          <div key={step.key} className="relative">
            {i < steps.length - 1 && (
              <div className={`absolute left-[19px] top-8 w-0.5 h-[calc(100%-8px)] ${
                step.status === 'done' ? 'bg-green-200' : 'bg-gray-100'
              }`} />
            )}

            <div className={`px-4 py-2.5 ${step.status === 'active' ? 'bg-orange-50 border-l-2 border-orange-400' : ''}`}>
              <div className="flex items-start gap-2.5">
                <div className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center text-[10px] flex-shrink-0 ${
                  step.status === 'done' ? 'bg-green-100 text-green-600' :
                  step.status === 'active' ? 'bg-orange-100 text-orange-600' :
                  'bg-gray-100 text-gray-400'
                }`}>
                  {step.icon}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className={`text-xs font-medium ${
                      step.status === 'done' ? 'text-gray-500' :
                      step.status === 'active' ? 'text-gray-800' : 'text-gray-400'
                    }`}>
                      {step.label}
                    </span>
                    {step.status === 'done' && <span className="text-[10px] text-green-500">✓</span>}
                  </div>

                  <p className="text-[10px] text-gray-400 mt-0.5 leading-tight">{step.desc}</p>

                  {step.progress != null && step.status !== 'done' && (
                    <div className="mt-1.5">
                      <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full transition-all duration-500 ${
                          step.status === 'active' ? 'bg-orange-400' : 'bg-gray-300'
                        }`} style={{ width: `${step.progress}%` }} />
                      </div>
                      {step.detail && (
                        <p className="text-[9px] text-gray-400 mt-0.5">{step.detail}</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-gray-100">
        <div className="flex justify-between text-[10px] text-gray-400">
          <span>{doneCount}/{steps.length} 完成</span>
          <span className={isActive ? 'text-orange-500' : 'text-green-500'}>
            {isActive ? '● 生成中' : '● 自动保存'}
          </span>
        </div>
      </div>
    </div>
  );
}
