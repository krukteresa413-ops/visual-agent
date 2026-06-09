import { useEffect, useState } from 'react';

const STEPS = [
  { label: '解析产品信息', icon: '🔍' },
  { label: '制定创意策略', icon: '💡' },
  { label: '生成主视觉', icon: '🖼️' },
  { label: '生成辅助素材', icon: '✨' },
  { label: '合规检查', icon: '✅' },
  { label: '整理结果', icon: '📦' },
];

interface Props {
  active: boolean;
}

export default function AgentProgress({ active }: Props) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (!active) { setStep(0); return; }
    setStep(0);
    const interval = setInterval(() => {
      setStep(prev => {
        if (prev >= STEPS.length - 1) {
          clearInterval(interval);
          return prev;
        }
        return prev + 1;
      });
    }, 2000 + Math.random() * 1500); // 2-3.5s per step
    return () => clearInterval(interval);
  }, [active]);

  if (!active) return null;

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="liquid-card p-5 space-y-3">
        <p className="text-center text-xs text-gray-400 mb-2">AI Agent 工作中...</p>
        {STEPS.map((s, i) => (
          <div key={s.label} className={`flex items-center gap-3 transition-all duration-500 ${
            i <= step ? 'opacity-100' : 'opacity-30'
          }`}>
            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs transition-colors ${
              i < step ? 'bg-orange-500/20 text-orange-400' :
              i === step ? 'bg-orange-500/30 text-orange-300 animate-pulse' :
              'bg-white/5 text-gray-600'
            }`}>
              {i < step ? '✓' : s.icon}
            </span>
            <span className={`text-xs ${i <= step ? 'text-gray-200' : 'text-gray-600'}`}>
              {s.label}
            </span>
            {i < step && (
              <span className="ml-auto text-[10px] text-orange-500/50">完成</span>
            )}
            {i === step && (
              <span className="ml-auto flex gap-1">
                <span className="w-1 h-1 rounded-full bg-orange-400 animate-bounce" style={{animationDelay:'0ms'}} />
                <span className="w-1 h-1 rounded-full bg-orange-400 animate-bounce" style={{animationDelay:'150ms'}} />
                <span className="w-1 h-1 rounded-full bg-orange-400 animate-bounce" style={{animationDelay:'300ms'}} />
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
