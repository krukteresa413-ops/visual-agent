// 图一:AI 追问面板 —— 渲染当前模板问题 + 快选小弹窗(chips)。纯展示,逻辑在 AIChatPanel。
import {
  TEMPLATE_QUESTIONS,
  answerDisplay,
  type AnswerValue,
  type TemplateQuestion,
} from '../lib/questionnaire/templateQuestions';

interface Props {
  isLight?: boolean;
  index: number;
  question: TemplateQuestion;
  answers: Record<string, AnswerValue>;
  multiSelected: string[];
  onPickSingle: (option: string) => void;
  onToggleMulti: (option: string) => void;
  onCommitMulti: () => void;
  onSubmitDate: (value: string) => void;
  onSkip: () => void;
  onCancel: () => void;
}

export default function QuestionnairePanel({
  isLight,
  index,
  question,
  answers,
  multiSelected,
  onPickSingle,
  onToggleMulti,
  onCommitMulti,
  onSubmitDate,
  onSkip,
  onCancel,
}: Props) {
  const total = TEMPLATE_QUESTIONS.length;
  const answered = TEMPLATE_QUESTIONS.slice(0, index).filter((q) => q.key in answers);
  const card = isLight ? 'border-gray-200 bg-white' : 'border-white/10 bg-white/[0.03]';
  const sub = isLight ? 'text-gray-500' : 'text-gray-400';
  const chip = isLight
    ? 'border-gray-200 bg-gray-50 text-gray-700 hover:border-purple-300 hover:text-purple-600'
    : 'border-white/10 bg-white/5 text-gray-200 hover:border-purple-400/50 hover:text-purple-200';
  const chipOn = 'border-purple-500 bg-purple-500/15 text-purple-300';

  return (
    <div className={`rounded-2xl border ${card} p-4`} data-testid="questionnaire-panel">
      <div className="mb-2 flex items-center justify-between">
        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-purple-400">
          <span>💬</span> AI 追问 · {index + 1}/{total}
        </span>
        <button onClick={onCancel} className={`text-[11px] ${sub} hover:underline`}>
          跳过追问,直接生成
        </button>
      </div>

      {answered.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-1.5">
          {answered.map((q) => (
            <span key={q.key} className={`rounded-full border px-2 py-0.5 text-[11px] ${chip}`}>
              {q.icon} {q.label}:{answerDisplay(answers[q.key])}
            </span>
          ))}
        </div>
      )}

      <div className="mb-3 flex items-start gap-2">
        <span className="text-lg leading-none">{question.icon}</span>
        <p className={`text-sm ${isLight ? 'text-gray-800' : 'text-gray-100'}`}>{question.prompt}</p>
      </div>

      {question.type === 'single' && question.options && (
        <div className="flex flex-wrap gap-1.5">
          {question.options.map((opt) => (
            <button key={opt} onClick={() => onPickSingle(opt)} className={`rounded-full border px-3 py-1 text-xs transition-colors ${chip}`}>
              {opt}
            </button>
          ))}
        </div>
      )}

      {question.type === 'multi' && question.options && (
        <>
          <div className="flex flex-wrap gap-1.5">
            {question.options.map((opt) => {
              const on = multiSelected.includes(opt);
              return (
                <button
                  key={opt}
                  onClick={() => onToggleMulti(opt)}
                  className={`rounded-full border px-3 py-1 text-xs transition-colors ${on ? chipOn : chip}`}
                >
                  {on ? '✓ ' : ''}{opt}
                </button>
              );
            })}
          </div>
          <button
            onClick={onCommitMulti}
            className="mt-3 rounded-lg bg-purple-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-purple-500"
          >
            确定{multiSelected.length ? `(${multiSelected.length})` : ''}
          </button>
        </>
      )}

      {question.type === 'date' && (
        <input
          type="date"
          onChange={(e) => e.target.value && onSubmitDate(e.target.value)}
          className={`rounded-lg border px-3 py-1.5 text-xs ${card} ${isLight ? 'text-gray-800' : 'text-gray-100'}`}
        />
      )}

      {(question.type === 'text' || question.type === 'tags') && (
        <p className={`text-[11px] ${sub}`}>在下方输入框作答,Enter 提交。</p>
      )}

      {question.optional && (
        <button onClick={onSkip} className={`mt-3 ml-1 text-[11px] ${sub} hover:underline`}>
          跳过本题 →
        </button>
      )}
    </div>
  );
}
