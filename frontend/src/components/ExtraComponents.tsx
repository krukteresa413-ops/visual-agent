// Part E: ExportButtons + F: ErrorPanel combined
import { useState } from 'react';
import { exportMarkdown } from '../api/client';

interface Props { projectId: number; }
export default function ExportButtons({ projectId }: Props) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try { const { markdown } = await exportMarkdown(projectId); await navigator.clipboard.writeText(markdown); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch (e) { console.error(e); }
  };
  const base = import.meta.env.VITE_API_BASE_URL || '';
  return (
    <div className="flex gap-2">
      <button onClick={handleCopy} className="px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-xs transition-colors">{copied?'已复制':'复制 MD'}</button>
      <button onClick={() => window.open(base + '/api/v1/visual-tasks/projects/' + projectId + '/export/docx', '_blank')} className="px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-xs transition-colors">下载 Word</button>
    </div>
  );
}

// Part F: ErrorPanel
export function ErrorPanel({ error, onRetry }: { error: any; onRetry: () => void }) {
  const d = error?.response?.data?.detail;
  const reason = typeof d === 'object' ? d.reason : d || error?.message || '未知错误';
  const retryable = typeof d === 'object' ? d.retryable : true;
  const code = typeof d === 'object' ? d.error_code : 'UNKNOWN';
  return (
    <div className="border border-red-800 bg-red-950/30 rounded-xl p-5 space-y-3">
      <div className="flex items-start gap-3"><span className="text-2xl">⚠️</span><div><h4 className="text-sm font-medium text-red-300">生成失败</h4><p className="text-sm text-red-200 mt-1">{reason}</p><p className="text-xs text-gray-600 mt-1">{code}</p></div></div>
      {retryable && <button onClick={onRetry} className="w-full py-2 bg-red-900 hover:bg-red-800 rounded-lg text-sm text-red-200 transition-colors">重试</button>}
    </div>
  );
}

// Part G: GenerationMeta
export function GenerationMeta({ meta }: { meta?: Record<string,any> }) {
  if (!meta) return null;
  return (
    <div className="flex flex-wrap gap-3 px-4 py-2 bg-gray-900/50 border-b border-gray-800 text-xs text-gray-400">
      {meta.generation_seconds && <span>⏱ {meta.generation_seconds}s</span>}
      {meta.total_llm_calls && <span>📞 {meta.total_llm_calls} 次调用</span>}
      {meta.total_input_tokens && meta.total_output_tokens && <span>🔤 {((meta.total_input_tokens + meta.total_output_tokens)/1000).toFixed(1)}K tokens</span>}
      {meta.estimated_cost_usd !== undefined && <span>💵 ~${meta.estimated_cost_usd.toFixed(4)}</span>}
    </div>
  );
}

// Part H: ComplianceWarnings
export function ComplianceWarnings({ issues }: { issues?: {level:string;type:string;location:string;text:string;suggestion:string}[] }) {
  if (!issues?.length) return null;
  return (
    <div className="border border-yellow-800 bg-yellow-950/20 rounded-xl p-4 mb-4">
      <h4 className="text-xs font-medium text-yellow-300 mb-2">合规提醒 ({issues.length})</h4>
      <div className="space-y-2 max-h-32 overflow-y-auto">
        {issues.map((issue,i) => (
          <div key={i} className="text-xs text-gray-300 flex items-start gap-2"><span className="text-yellow-400 mt-0.5">•</span><div><span className="text-yellow-200">{issue.text}</span><span className="text-gray-500 ml-1">({issue.location})</span><p className="text-gray-500 mt-0.5">{issue.suggestion}</p></div></div>
        ))}
      </div>
    </div>
  );
}
