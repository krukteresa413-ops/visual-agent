import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../api/client';

interface HistoryItem {
  id: number;
  project_name: string;
  model_used: string;
  generation_seconds: number | null;
  created_at: string | null;
  main_image_url: string | null;
}

interface HistoryResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

const PAGE_SIZE = 20;

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const [projectFilter, setProjectFilter] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['history', page, projectFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
      if (projectFilter) params.set('project_id', projectFilter);
      return api.get<HistoryResponse>('/api/v1/history/?' + params.toString()).then(r => r.data);
    },
  });

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  return (
    <div className="min-h-screen bg-black text-white">
      <header className="py-2 px-6 border-b border-gray-800 flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold">生成历史</h1>
          <p className="text-xs text-gray-500">
            {data ? `${data.total} 条记录` : '加载中...'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-600">历史记录</span>
        </div>
      </header>

      <main className="pt-2 pb-12 px-6 max-w-5xl mx-auto">
        {/* Filters */}
        <div className="mb-3 flex items-center gap-2">
          <input
            type="number"
            placeholder="按项目ID筛选..."
            value={projectFilter}
            onChange={e => { setProjectFilter(e.target.value); setPage(1); }}
            className="bg-gray-900 border border-gray-800 rounded px-3 py-1.5 text-xs text-gray-300 w-40 focus:outline-none focus:border-gray-600"
          />

          <input
            type="text"
            placeholder="搜索关键词..."
            className="bg-gray-900 border border-gray-800 rounded px-3 py-1.5 text-xs text-gray-300 w-48 focus:outline-none focus:border-gray-600"
          />
          {projectFilter && (
            <button
              onClick={() => { setProjectFilter(''); setPage(1); }}
              className="text-xs text-gray-500 hover:text-gray-300"
            >
              清除
            </button>
          )}
        </div>

        {isLoading ? (
          <p className="text-xs text-gray-600">加载中...</p>
        ) : !data?.items.length ? (
          <p className="text-xs text-gray-600">暂无记录</p>
        ) : (
          <>
            {/* History list */}
            <div className="border border-gray-800 rounded-lg divide-y divide-gray-800">
              {data.items.map((item) => (
                <div key={item.id} className="px-4 py-2.5 flex items-center gap-3 hover:bg-gray-900/50">
                  {/* Thumbnail */}
                  <div className="w-10 h-10 bg-gray-900 rounded flex-shrink-0 flex items-center justify-center overflow-hidden border border-gray-800">
                    {item.main_image_url ? (
                      <img src={item.main_image_url} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <span className="text-xs text-gray-700">IMG</span>
                    )}
                  </div>
                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-300 truncate">
                      #{item.id} — {item.project_name}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-gray-600">{item.model_used}</span>
                      {item.generation_seconds && (
                        <span className="text-xs text-gray-700">{item.generation_seconds}s</span>
                      )}
                    </div>
                  </div>
                  {/* Time */}
                  <span className="text-xs text-gray-600 flex-shrink-0">
                    {item.created_at ? formatDate(item.created_at) : ''}
                  </span>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-4">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1 text-xs text-gray-400 border border-gray-800 rounded disabled:opacity-30 hover:border-gray-600"
                >
                  上一页
                </button>
                <span className="text-xs text-gray-600">
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="px-3 py-1 text-xs text-gray-400 border border-gray-800 rounded disabled:opacity-30 hover:border-gray-600"
                >
                  下一页
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
}
