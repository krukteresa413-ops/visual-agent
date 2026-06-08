import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listProjects, createProject, deleteProject } from '../api/client';
import { useNavigate } from 'react-router-dom';
import ReviewQuestions from '../components/ReviewQuestions';
import HistoryTimeline from '../components/HistoryTimeline';

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

const DIAMONDS = [
  { title: '上传文档', desc: 'PDF/PPT/Word', icon: '📄', action: 'upload' },
  { title: '品牌套件', desc: '品牌管理', icon: '🎨', action: 'brand' },
  { title: '素材库', desc: '历史生成', icon: '📦', action: 'scroll' },
  { title: '新建项目', desc: '手动创建', icon: '✨', action: 'create' },
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
  const [selectedProjectId, setSelectedProjectId] = useState(2);

  const [reviewQuestions, setReviewQuestions] = useState<Array<{field:string;level:string;question:string;hint:string}>>([]);
  const [reviewBrief, setReviewBrief] = useState<Record<string,unknown>>({});

  const { data: projects, isLoading } = useQuery({ queryKey: ['projects'], queryFn: listProjects });
  const createMut = useMutation({
    mutationFn: () => createProject(name, desc || undefined),
    onSuccess: (d) => { qc.invalidateQueries({ queryKey: ['projects'] }); setShowCreate(false); setSelectedProjectId(d.id); navigate('/generate/' + d.id); }
  });
  const delMut = useMutation({ mutationFn: (id: number) => deleteProject(id), onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }) });

  const callGenerateApi = async (formData: FormData) => {
    const resp = await fetch('/api/v1/generate-from-document', { method: 'POST', body: formData });
    const text = await resp.text();
    let data: any;
    try { data = JSON.parse(text); } catch {
      alert('服务器返回异常 (HTTP ' + resp.status + '): ' + text.slice(0, 200));
      return null;
    }
    if (data.needs_review) {
      setReviewQuestions(data.questions || []);
      setReviewBrief(data.parsed_brief || {});
      return null;
    }
    if (data.parsed_brief) {
      navigate('/generate/' + selectedProjectId, { state: { brief: data.parsed_brief, result: data.generation, images: data.images } });
      return data;
    }
    alert(data.detail || '操作失败');
    return null;
  };

  const pid = () => String(selectedProjectId);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const fd = new FormData(); fd.append('file', file); fd.append('project_id', pid());
      await callGenerateApi(fd);
    } catch (e: any) { alert('上传失败: ' + e.message); }
    finally { setUploading(false); }
  };

  const handleText = async () => {
    if (!taskText.trim()) return;
    setUploading(true);
    try {
      const fd = new FormData(); fd.append('text', taskText); fd.append('project_id', pid());
      await callGenerateApi(fd);
    } catch (e: any) { alert('提交失败: ' + e.message); }
    finally { setUploading(false); }
  };

  const handleResubmit = async (answers: Record<string, string>) => {
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('parsed_brief_json', JSON.stringify(reviewBrief));
      fd.append('project_id', pid());
      fd.append('answers', JSON.stringify(answers));
      await callGenerateApi(fd);
    } catch (e: any) { alert('提交失败: ' + e.message); }
    finally { setUploading(false); }
  };

  const handleSkip = async () => {
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('text', taskText);
      fd.append('project_id', pid());
      fd.append('skip_review', 'true');
      await callGenerateApi(fd);
    } catch (e: any) { alert('提交失败: ' + e.message); }
    finally { setUploading(false); }
  };

  const diamondAction = (a: string) => {
    if (a === 'upload') fileRef.current?.click();
    else if (a === 'brand') navigate('/generate/' + selectedProjectId);
    else if (a === 'scroll') document.getElementById('projects')?.scrollIntoView({ behavior: 'smooth' });
    else setShowCreate(true);
  };

  return (
    <div className="liquid-page min-h-screen text-gray-100">
      <input ref={fileRef} type="file" className="hidden" accept=".pdf,.pptx,.docx,.xlsx,.txt,.csv,.png,.jpg,.webp"
        onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f); }} />

      <header className="sticky top-0 z-10 border-b border-white/5 bg-black/20 backdrop-blur-2xl px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm" style={{ background: 'linear-gradient(135deg, #f97316, #ec4899)' }}>
            <span className="text-white">VA</span></div>
          <span className="font-semibold text-lg tracking-tight">视觉 Agent</span>
        </div>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-orange-500 hover:bg-orange-400 rounded-lg text-sm font-medium">+ 新建项目</button>
      </header>

      <div className="liquid-orb pointer-events-none fixed right-10 top-20 w-72 h-72 rotate-45 rounded-[48px] opacity-50 -z-10" />
      <div className="liquid-orb pointer-events-none fixed left-8 bottom-32 w-48 h-48 rotate-45 rounded-[32px] opacity-35 -z-10" />

      {reviewQuestions.length > 0 ? (
        <section className="px-5 pt-12 pb-6">
          <ReviewQuestions questions={reviewQuestions} parsedBrief={reviewBrief} onResubmit={handleResubmit} onSkip={handleSkip} loading={uploading} />
        </section>
      ) : (
        <>
          <section id="hero-section" className="relative px-5 pt-12 pb-6">
            <div className="mx-auto max-w-3xl text-center">
              <div className="liquid-pill inline-flex items-center gap-2 px-4 py-2 text-sm text-gray-300 mb-6">
                <span className="text-orange-400">✦</span> 外贸产品视觉内容生成 Agent
              </div>
              <h1 className="text-3xl md:text-4xl font-semibold text-white mb-3">上传产品资料，<span className="gradient-text">自动生成全套视觉素材</span></h1>
              <p className="text-gray-400 text-sm mb-8">拖拽 PDF/PPT/Word 或直接输入产品描述，AI 自动提取卖点生成六类素材</p>
              <div className="liquid-card p-4 max-w-xl mx-auto">
                <div className="flex gap-2">
                  <input className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-gray-100 placeholder-gray-600 focus:border-orange-500/50 focus:outline-none"
                    placeholder="输入产品描述，例如：300L商用冷柜，不锈钢外壳，快速制冷..."
                    value={taskText} onChange={e => setTaskText(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') handleText(); }} />
                  <button onClick={handleText} disabled={!taskText.trim() || uploading}
                    className="px-5 py-3 bg-orange-500 hover:bg-orange-400 disabled:opacity-30 rounded-xl text-sm font-medium whitespace-nowrap">
                    {uploading ? '...' : '生成 →'}</button>
                </div>
                <div className="mt-3 text-xs text-gray-500 text-center">
                  或 <span className="text-orange-400 cursor-pointer hover:underline" onClick={() => fileRef.current?.click()}>上传文档</span>（PDF·PPT·Word·Excel·图片）
                </div>
              </div>
            </div>
          </section>

          <section className="px-5 pb-4">
            <div className="max-w-3xl mx-auto">
              <div className="flex flex-wrap justify-center gap-2">
                {SCENES.map(s => (
                  <button key={s.name} onClick={() => setTaskText(s.name + '物料生成')}
                    className="px-3 py-1.5 rounded-full border border-white/10 bg-white/5 text-xs text-gray-400 hover:border-orange-500/30 hover:text-gray-200 transition-all">
                    {s.icon} {s.name}
                  </button>
                ))}
              </div>
            </div>
          </section>

          <section className="px-5 pb-8">
            <div className="liquid-diamond-cluster relative h-[240px] w-[240px] sm:h-[280px] sm:w-[280px] mx-auto">
              {DIAMONDS.map((d, i) => (
                <button key={d.title} onClick={() => diamondAction(d.action)}
                  className={`liquid-diamond group absolute flex h-[112px] w-[112px] rotate-45 items-center justify-center rounded-2xl text-gray-100 transition duration-300 hover:z-10 sm:h-[130px] sm:w-[130px] sm:rounded-[22px] ${
                    i === 0 ? 'left-1/2 top-0 -translate-x-1/2' :
                    i === 1 ? 'left-0 top-1/2 -translate-y-1/2' :
                    i === 2 ? 'right-0 top-1/2 -translate-y-1/2' :
                    'left-1/2 bottom-0 -translate-x-1/2'}`}
                  style={{ zIndex: i === 0 ? 2 : 1 }}>
                  <span className="-rotate-45 flex flex-col items-center gap-0.5">
                    <span className="text-xl">{d.icon}</span>
                    <span className="whitespace-nowrap text-xs font-semibold">{d.title}</span>
                    <span className="whitespace-nowrap text-[10px] text-gray-500">{d.desc}</span>
                  </span>
                </button>
              ))}
            </div>
          </section>
        </>
      )}

      <section className="px-5 pb-8">
        <div className="max-w-2xl mx-auto">
          <HistoryTimeline projectId={selectedProjectId} />
        </div>
      </section>

      <main id="projects" className="max-w-2xl mx-auto px-8 pb-20">
        <h2 className="text-sm font-medium text-gray-400 mb-4 text-center">最近项目</h2>
        {isLoading && <p className="text-gray-500 text-center py-8">加载中...</p>}
        {projects?.length === 0 && <div className="liquid-card p-8 text-center text-gray-500">还没有项目，上传一个文档开始吧</div>}
        <div className="space-y-2">
          {projects?.map(p => (
            <div key={p.id}
              className={`liquid-card p-4 cursor-pointer group flex items-center justify-between transition-all ${p.id === selectedProjectId ? 'border-orange-500/40 bg-orange-500/5' : 'hover:border-orange-500/20'}`}
              onClick={() => { setSelectedProjectId(p.id); document.getElementById('hero-section')?.scrollIntoView({ behavior: 'smooth' }); }}>
              <div><h3 className="font-medium text-sm text-gray-100">{p.name}</h3>
                <div className="flex gap-3 mt-1 text-[11px] text-gray-600"><span>{p.generation_count} 次</span><span>{new Date(p.created_at).toLocaleDateString('zh-CN')}</span></div></div>
              <div className="flex items-center gap-2">
                <span className="text-orange-400 text-xs opacity-0 group-hover:opacity-100">选中</span>
                <button onClick={e => { e.stopPropagation(); if (confirm('删除?')) delMut.mutate(p.id); }}
                  className="text-gray-600 hover:text-red-400 text-xs opacity-0 group-hover:opacity-100">删除</button>
              </div>
            </div>
          ))}
        </div>
      </main>

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
