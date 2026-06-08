import { useState } from 'react';

interface Question {
  field: string;
  level: string;
  question: string;
  hint: string;
}

interface Props {
  questions: Question[];
  parsedBrief: Record<string, unknown>;
  onResubmit: (answers: Record<string, string>) => void;
  onSkip: () => void;
  loading: boolean;
}

export default function ReviewQuestions({ questions, parsedBrief, onResubmit, onSkip, loading }: Props) {
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const requiredQs = questions.filter(q => q.level === 'required');
  const recommendedQs = questions.filter(q => q.level === 'recommended');

  const handleChange = (field: string, value: string) => {
    setAnswers(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = () => {
    // Only submit non-empty answers
    const filled: Record<string, string> = {};
    for (const [k, v] of Object.entries(answers)) {
      if (v.trim()) filled[k] = v.trim();
    }
    onResubmit(filled);
  };

  const hasRequiredAnswer = requiredQs.some(q => (answers[q.field] || '').trim());

  return (
    <div className="liquid-card p-6 w-full max-w-xl mx-auto space-y-5">
      <div className="text-center space-y-1">
        <div className="text-orange-400 text-2xl">💬</div>
        <h3 className="text-sm font-medium text-gray-100">补充一些信息，生成效果更好</h3>
        <p className="text-xs text-gray-500">
          已识别产品「<span className="text-orange-400">{String(parsedBrief.product_name || '未知')}</span>」，
          还需要了解以下信息
        </p>
      </div>

      {/* Required questions */}
      {requiredQs.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
            <span className="text-[10px] text-orange-400 uppercase tracking-wide">必填</span>
          </div>
          {requiredQs.map(q => (
            <div key={q.field} className="space-y-1">
              <label className="text-xs text-gray-300">{q.question}</label>
              <input
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-orange-500/50 focus:outline-none"
                placeholder={q.hint}
                value={answers[q.field] || ''}
                onChange={e => handleChange(q.field, e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleSubmit(); }}
              />
            </div>
          ))}
        </div>
      )}

      {/* Recommended questions */}
      {recommendedQs.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-gray-500" />
            <span className="text-[10px] text-gray-500 uppercase tracking-wide">建议补充</span>
          </div>
          {recommendedQs.map(q => (
            <div key={q.field} className="space-y-1">
              <label className="text-xs text-gray-400">{q.question}</label>
              <input
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-white/20 focus:outline-none"
                placeholder={q.hint}
                value={answers[q.field] || ''}
                onChange={e => handleChange(q.field, e.target.value)}
              />
            </div>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-2 border-t border-white/5">
        <button
          onClick={onSkip}
          disabled={loading}
          className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
        >
          跳过，直接生成 →
        </button>
        <button
          onClick={handleSubmit}
          disabled={!hasRequiredAnswer || loading}
          className="px-5 py-2 bg-orange-500 hover:bg-orange-400 disabled:opacity-30 rounded-lg text-sm font-medium transition-all"
        >
          {loading ? '提交中...' : '提交补充信息'}
        </button>
      </div>
    </div>
  );
}
