import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

interface HistoryRecord {
  id: number;
  project_id: number;
  brief_id: number | null;
  model_used: string;
  generation_seconds: number;
  created_at: string;
}

interface Props {
  projectId: number;
  onSelect?: (r: HistoryRecord) => void;
}

export default function HistoryTimeline({ projectId }: Props) {
  const navigate = useNavigate();
  const [loadingId, setLoadingId] = useState<number | null>(null);

  const { data: records, isLoading } = useQuery({
    queryKey: ['history', projectId],
    queryFn: async () => {
      const resp = await fetch(`/api/v1/projects/${projectId}/history`);
      const data = await resp.json();
      return data.records as HistoryRecord[];
    },
  });

  const handleRestore = async (record: HistoryRecord) => {
    setLoadingId(record.id);
    try {
      const resp = await fetch(`/api/v1/projects/${projectId}/history/${record.id}`);
      const data = await resp.json();
      // Navigate with restored plan
      navigate(`/generate/${projectId}`, {
        state: {
          result: data.asset_plan,
          restoredFrom: record.id,
        },
      });
    } catch {
      alert('加载历史记录失败');
    } finally {
      setLoadingId(null);
    }
  };

  if (isLoading) {
    return <p className="text-gray-600 text-sm text-center py-4">加载中...</p>;
  }

  if (!records?.length) {
    return (
      <div className="liquid-card p-6 text-center">
        <p className="text-gray-500 text-sm">暂无生成记录</p>
        <p className="text-gray-700 text-xs mt-1">生成素材后会自动保存在这里</p>
      </div>
    );
  }

  return (
    <div className="w-full space-y-2">
      <h2 className="text-xs font-medium text-gray-500 text-center mb-3">
        生成历史 · {records.length} 条记录
      </h2>
      {records.map((r) => (
        <div
          key={r.id}
          className="liquid-card px-4 py-3 flex items-center justify-between group hover:border-orange-500/20 cursor-pointer"
          onClick={() => handleRestore(r)}
        >
          <div className="flex items-center gap-3">
            <span className="text-lg">📋</span>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-200">#{r.id}</span>
                <span className="text-[10px] bg-gray-800 px-1.5 py-0.5 rounded text-gray-500">
                  {r.model_used || 'unknown'}
                </span>
              </div>
              <span className="text-[11px] text-gray-600">
                {new Date(r.created_at).toLocaleString('zh-CN')}
                {r.generation_seconds ? ` · ${r.generation_seconds}s` : ''}
              </span>
            </div>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleRestore(r);
            }}
            disabled={loadingId === r.id}
            className="text-xs text-orange-400 hover:text-orange-300 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            {loadingId === r.id ? '加载中...' : '查看 →'}
          </button>
        </div>
      ))}
    </div>
  );
}
