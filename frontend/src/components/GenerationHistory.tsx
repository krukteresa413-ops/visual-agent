// Part D: GenerationHistory
import { useQuery } from '@tanstack/react-query';
import { listGenerations } from '../api/client';
import type { GenerationRecord } from '../api/client';

interface Props { projectId: number; onSelect: (r: GenerationRecord) => void; }
export default function GenerationHistory({ projectId, onSelect }: Props) {
  const { data, isLoading } = useQuery({ queryKey: ['gens', projectId], queryFn: () => listGenerations(projectId) });
  if (isLoading) return <p className="text-xs text-gray-600">加载中...</p>;
  if (!data?.length) return null;
  return (
    <div className="border border-gray-800 rounded-xl p-4">
      <h3 className="text-xs font-medium text-gray-400 mb-3">历史生成</h3>
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {data.map(r => (
          <button key={r.id} onClick={() => onSelect(r)} className="w-full text-left p-3 bg-gray-900 rounded-lg hover:bg-gray-800 transition-colors">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-300">#{r.id} {r.model_used||'unknown'}</span>
              <span className="text-xs text-gray-600">{r.generation_seconds ? r.generation_seconds + "s" : ""}</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">{new Date(r.created_at).toLocaleString('zh-CN')}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
