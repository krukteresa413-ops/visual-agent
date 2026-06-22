import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '../api/client';

interface StepInfo {
  step: string;
  label: string;
  status: string;
  progress: number;
  output?: Record<string, unknown> | null;
}

interface Asset {
  type: string;
  label: string;
  url?: string;
  preview?: string;
  text?: string;
}

interface CampaignData {
  project_id: number;
  project_name: string;
  status: string;
  steps: StepInfo[];
  assets: Asset[];
}

const fetchCampaign = (id: number) =>
  api.get<CampaignData>(`/api/v1/campaign/${id}`).then(r => r.data);

export default function CampaignPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const pid = Number(projectId);

  const { data, isLoading } = useQuery({
    queryKey: ['campaign', pid],
    queryFn: () => fetchCampaign(pid),
    refetchInterval: 3000,
    enabled: !!pid,
  });

  if (isLoading) return <div className="min-h-screen bg-black flex items-center justify-center"><p className="text-gray-400 text-sm">加载中...</p></div>;
  if (!data) return null;
  const { data: assetData } = useQuery({
    queryKey: ['assets', pid],
    queryFn: () => api.get(`/assets/?project_id=${pid}`).then(r => r.data),
    enabled: !!pid,
  });


  const statusColor = data.status === 'completed' ? 'text-green-400' : data.status === 'failed' ? 'text-red-400' : 'text-yellow-400';
  const statusBg = data.status === 'completed' ? 'bg-green-400/10 border-green-400/30' : data.status === 'failed' ? 'bg-red-400/10 border-red-400/30' : 'bg-yellow-400/10 border-yellow-400/30';

  return (
    <div className="min-h-screen bg-black text-white flex">
      {/* Left Sidebar — Pipeline Steps */}
      <aside className="hidden md:block w-64 border-r border-gray-800 flex flex-col flex-shrink-0">
        <header className="px-4 py-3 border-b border-gray-800">
          <Link to="/" className="text-xs text-gray-500 hover:text-gray-300">← 返回</Link>
          <h2 className="text-sm font-semibold mt-1">{data.project_name}</h2>
          <span className={`inline-block mt-1 px-2 py-0.5 text-xs rounded border ${statusBg} ${statusColor}`}>
            {data.status === 'completed' ? '已完成' : data.status === 'failed' ? '失败' : '进行中'}
          </span>
        </header>

        <nav className="flex-1 py-2">
          {data.steps.map((step, i) => (
            <div key={step.step} className={`px-4 py-2.5 border-l-2 ${
              step.status === 'completed' ? 'border-green-500 bg-green-500/5' :
              step.status === 'in_progress' ? 'border-blue-500 bg-blue-500/5' :
              step.status === 'failed' ? 'border-red-500 bg-red-500/5' :
              'border-transparent'
            }`}>
              <div className="flex items-center gap-2">
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                  step.status === 'completed' ? 'bg-green-500 text-black' :
                  step.status === 'in_progress' ? 'bg-blue-500 text-black' :
                  step.status === 'failed' ? 'bg-red-500 text-white' :
                  'bg-gray-800 text-gray-600'
                }`}>
                  {step.status === 'completed' ? '✓' : step.status === 'failed' ? '✗' : i + 1}
                </span>
                <span className="text-xs text-gray-300">{step.label}</span>
              </div>
              {step.status === 'in_progress' && (
                <div className="mt-1.5 h-1 bg-gray-800 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: `${step.progress}%` }} />
                </div>
              )}
            </div>
          ))}
        </nav>
      </aside>

      {/* Main Canvas */}
      <main className="flex-1 flex flex-col">
        <header className="px-6 py-2 border-b border-gray-800 flex items-center justify-between">
          <h1 className="text-sm font-semibold">Agent Canvas</h1>
          <div className="flex items-center gap-3">
            
            
          </div>
        </header>

        <div className="flex-1 p-6 overflow-auto">
          {data.assets.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-600 text-sm">等待 Agent 生成结果...</p>
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-4">
              {data.assets.map((asset, i) => (
                <div key={i} className="border border-gray-800 rounded-lg overflow-hidden bg-gray-900/50">
                  {asset.type === 'image' && asset.url ? (
                    <>
                      <img src={asset.url} alt={asset.label} className="w-full h-48 object-cover" />
                      <div className="px-3 py-2 border-t border-gray-800">
                        <p className="text-xs text-gray-400">{asset.label}</p>
                      </div>
                    </>
                  ) : asset.type === 'video' ? (
                    <div className="h-48 flex items-center justify-center bg-gray-900">
                      <span className="text-gray-600 text-xs">▶ {asset.label}</span>
                    </div>
                  ) : (
                    <div className="p-3">
                      <p className="text-xs text-gray-500 mb-1">{asset.label}</p>
                      <p className="text-xs text-gray-300 line-clamp-4">{asset.text}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Right Sidebar — Asset Library */}
      <aside className="hidden md:block w-56 border-l border-gray-800 flex-shrink-0 overflow-auto">
        <div className="px-3 py-3 border-b border-gray-800">
          <h3 className="text-xs font-medium text-gray-400">素材库</h3>
          <p className="text-xs text-gray-600 mt-0.5">{assetData?.total || 0} 个素材</p>
        </div>
        <div className="p-2 space-y-1">
          {assetData?.categories && Object.entries(assetData.categories).map(([cat, items]) => 
            Array.isArray(items) && items.length > 0 ? (
              <div key={cat}>
                <p className="text-xs text-gray-500 px-2 py-1 capitalize">{cat}</p>
                {items.slice(0, 5).map((item, i) => (
                  <div key={i} className="px-2 py-1 text-xs text-gray-400 hover:bg-gray-900 rounded truncate">
                    {item.url ? '🖼 ' : item.text ? '📝 ' : '📄 '}{item.label}
                  </div>
                ))}
              </div>
            ) : null
          )}
        </div>
      </aside>
    </div>
  );
}
