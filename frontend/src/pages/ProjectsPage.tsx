import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listProjects, createProject, deleteProject } from '../api/client';
import { useNavigate } from 'react-router-dom';
import ReviewQuestions from '../components/ReviewQuestions';

const SCENES = [
  { icon: '🛍️', name: '电商上新' },
  { icon: '📕', name: '小红书' },
  { icon: '🎵', name: '抖音' },
  { icon: '🍜', name: '餐饮' },
  { icon: '🎨', name: '品牌' },
  { icon: '🎉', name: '节日' },
  { icon: '📺', name: '直播' },
  { icon: '💬', name: '私域' },
  { icon: '📍', name: '本地' },
  { icon: '📦', name: '包装' },
];

export default function ProjectsPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [taskText, setTaskText] = useState('');
  const [uploading, setUploading] = useState(false);

  // 追问状态
  const [reviewQuestions, setReviewQuestions] = useState<Array<{field:string;level:string;question:string;hint:string}>>([]);
  const [reviewBrief, setReviewBrief] = useState<Record<string, unknown> | null>(null);

  const { data: projects, isLoading } = useQuery({ queryKey: ['projects'], queryFn: listProjects });
  const createMut = useMutation({
    mutationFn: () => createProject(name, desc || undefined),
    onSuccess: (d) => { qc.invalidateQueries({ queryKey: ['projects'] }); setShowCreate(false); navigate('/generate/' + d.id); }
  });
  const delMut = useMutation({ mutationFn: (id: number) => deleteProject(id), onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }) });

  const callGenerateAPI = async (formData: FormData) => {
    setUploading(true);
    try {
      const resp = await fetch('/api/v1/generate-from-document', { method: 'POST', body: formData });
      const data = await resp.json();
      if (data.needs_review) {
        // 显示追问
        setReviewQuestions(data.questions || []);
        setReviewBrief(data.parsed_brief);
      } else if (data.parsed_brief) {
        navigate('/generate/2', { state: { brief: data.parsed_brief, result: data.generation } });
      } else {
        alert(data.detail || '生成失败');
      }
    } catch (e: any) { alert('请求失败'); }
    finally { setUploading(false); }
  };

  const handleUpload = async (file: File) => {
    const fd = new FormData(); fd.append('file', file); fd.append('project_id', '2');
    await callGenerateAPI(fd);
  };

  const handleText = async () => {
    if (!taskText.trim()) return;
    const fd = new FormData(); fd.append('text', taskText); fd.append('project_id', '2');
    await callGenerateAPI(fd);
  };

  const handleResubmit = async (answers: Record<string, string>) => {
    if (!reviewBrief) return;
    const fd = new FormData();
    fd.append('parsed_brief_json', JSON.stringify(reviewBrief));
    fd.append('answers', JSON.stringify(answers));
    fd.append('project_id', '2');
    await callGenerateAPI(fd);
  };

  const handleSkipReview = async () => {
    if (!reviewBrief) return;
    const fd = new FormData();
    fd.append('parsed_brief_json', JSON.stringify(reviewBrief));
    fd.append('skip_review', 'true');
    fd.append('project_id', '2');
    await callGenerateAPI(fd);
  };

  return (
    <div className="liquid-page min-h-screen text-gray-100">
      <input ref={fileRef} type="file" className="hidden" accept=".pdf,.pptx,.docx,.xlsx,.txt,.csv,.png,.jpg,.webp"
        onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f); }} />

      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-white/5 bg-black/20 backdrop-blur-2xl px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md flex items-center justify-center font-bold text-xs" style={{ background: 'linear-gradient(135deg, #f97316, #ec4899)' }}>
            <span className="text-white">VA</span></div>
          <span className="font-semibold text-sm tracking-tight">视觉 Agent</span>
        </div>
        <button onClick={() => setShowCreate(true)} className="px-3 py-1.5 bg-orange-500 hover:bg-orange-400 rounded-md text-xs font-medium">+ 新建</button>
      </header>

      {/* Single column content */}
      <main className="max-w-2xl mx-auto px-6 py-16 flex flex-col items-center gap-10">

        {/* Hero */}
        <div className="text-center space-y-3">
          <div className="liquid-pill inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-300">
            <span className="text-orange-400">✦</span> 外贸产品视觉内容生成 Agent
          </div>
          <h1 className="text-2xl md:text-3xl font-semibold text-white leading-snug">
            上传产品资料，自动生成<br /><span className="gradient-text">全套视觉素材</span>
          </h1>
          <p className="text-gray-500 text-sm">拖拽 PDF / PPT / Word 或直接输入产品描述，AI 自动提取卖点生成六类素材</p>
        </div>

        {/* Review Questions — shown when API returns needs_review */}
        {reviewQuestions.length > 0 && reviewBrief && (
          <ReviewQuestions
            questions={reviewQuestions}
            parsedBrief={reviewBrief}
            onResubmit={handleResubmit}
            onSkip={handleSkipReview}
            loading={uploading}
          />
        )}

        {/* Input area — hidden during review */}
        {reviewQuestions.length === 0 && (
          <div className="w-full space-y-4">
            <div className="liquid-card p-3">
              <div className="flex gap-2">
                <textarea
                  className="flex-1 bg-transparent border-0 text-sm text-gray-100 placeholder-gray-600 resize-none focus:outline-none min-h-[80px] py-2"
                  placeholder="输入产品描述，例如：300L商用冷柜，不锈钢外壳，快速制冷，节能R290制冷剂，目标市场欧美中东..."
                  value={taskText}
                  onChange={e => setTaskText(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleText(); } }} />
              </div>
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/5">
                <button onClick={() => fileRef.current?.click()}
                  className="text-xs text-gray-500 hover:text-gray-300 transition-colors">
                  📎 上传文档（PDF·PPT·Word·Excel·图片）
                </button>
                <button onClick={handleText} disabled={!taskText.trim() || uploading}
                  className="px-5 py-2 bg-orange-500 hover:bg-orange-400 disabled:opacity-30 rounded-lg text-sm font-medium transition-all">
                  {uploading ? '生成中...' : '生成'}
                </button>
              </div>
            </div>

            {/* Scene tags */}
            <div className="flex flex-wrap gap-1.5 justify-center">
              {SCENES.map(s => (
                <button key={s.name} onClick={() => setTaskText((prev) => prev + ' ' + s.name + '物料')}
                  className="px-2.5 py-1 rounded-full border border-white/10 bg-white/5 text-[11px] text-gray-500 hover:border-orange-500/30 hover:text-gray-300 transition-all">
                  {s.icon} {s.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Projects */}
        <div className="w-full space-y-3">
          <h2 className="text-xs font-medium text-gray-600 text-center">最近项目</h2>
          {isLoading && <p className="text-gray-600 text-center py-6 text-sm">加载中...</p>}
          {projects?.length === 0 && (
            <div className="liquid-card p-8 text-center">
              <p className="text-gray-600 text-sm">还没有项目</p>
              <button onClick={() => fileRef.current?.click()} className="mt-3 text-orange-400 text-xs hover:underline">上传第一个文档 →</button>
            </div>
          )}
          {projects?.map(p => (
            <div key={p.id} className="liquid-card px-4 py-3 cursor-pointer group flex items-center justify-between hover:border-orange-500/20"
              onClick={() => navigate('/generate/' + p.id)}>
              <div>
                <span className="text-sm text-gray-200 group-hover:text-white">{p.name}</span>
                <span className="ml-3 text-[11px] text-gray-700">{p.generation_count} 次 · {new Date(p.created_at).toLocaleDateString('zh-CN')}</span>
              </div>
              <button onClick={e => { e.stopPropagation(); if (confirm('删除?')) delMut.mutate(p.id); }}
                className="text-gray-700 hover:text-red-400 text-xs opacity-0 group-hover:opacity-100">删除</button>
            </div>
          ))}
        </div>
      </main>

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setShowCreate(false)}>
          <div className="liquid-card p-6 w-full max-w-sm mx-4 space-y-4" onClick={e => e.stopPropagation()}>
            <h3 className="text-sm font-medium">新建项目</h3>
            <input className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-gray-100 placeholder-gray-600" placeholder="项目名称" value={name} onChange={e => setName(e.target.value)} />
            <input className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-gray-100 placeholder-gray-600" placeholder="描述（可选）" value={desc} onChange={e => setDesc(e.target.value)} />
            <div className="flex gap-2">
              <button onClick={() => createMut.mutate()} disabled={!name.trim()} className="px-4 py-2 bg-orange-500 rounded-lg text-sm">创建</button>
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm">取消</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
