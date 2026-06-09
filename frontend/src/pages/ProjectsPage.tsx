import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listProjects, createProject, deleteProject } from '../api/client';
import { useNavigate } from 'react-router-dom';
import ReviewQuestions from '../components/ReviewQuestions';
import AgentProgress from '../components/AgentProgress';
import StrategyPanel from '../components/StrategyPanel';
import ThemeToggle, { useTheme } from '../components/ThemeToggle';

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
  { title: '素材库', desc: '历史生成', icon: '📦', action: 'assets' },
  { title: '新建项目', desc: '手动创建', icon: '✨', action: 'create' },
];

const PLATFORMS = [
  { id: 'taobao', name: '淘宝', icon: '🛒' },
  { id: 'xiaohongshu', name: '小红书', icon: '📕' },
  { id: 'douyin', name: '抖音', icon: '🎵' },
  { id: 'pinduoduo', name: '拼多多', icon: '💰' },
  { id: 'wechat', name: '微信', icon: '💬' },
  { id: 'meituan', name: '美团', icon: '🍜' },
  { id: 'amazon', name: 'Amazon', icon: '🌍' },
  { id: 'alibaba', name: '阿里国际', icon: '🚢' },
];

export default function ProjectsPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { isLight, toggle: toggleTheme } = useTheme();
  const fileRef = useRef<HTMLInputElement>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [taskText, setTaskText] = useState('');
  const [uploading, setUploading] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);

  // 追问状态
  const [reviewQuestions, setReviewQuestions] = useState<Array<{field:string;level:string;question:string;hint:string}>>([]);
  const [reviewBrief, setReviewBrief] = useState<Record<string, unknown> | null>(null);
  const [strategyData, setStrategyData] = useState<any>(null);
  const [strategyLoading, setStrategyLoading] = useState(false);

  const { data: projects, isLoading } = useQuery({ queryKey: ['projects'], queryFn: listProjects });
  const createMut = useMutation({
    mutationFn: () => createProject(name, desc || undefined),
    onSuccess: (d) => { qc.invalidateQueries({ queryKey: ['projects'] }); setShowCreate(false); navigate('/generate/' + d.id); }
  });
  const delMut = useMutation({ mutationFn: (id: number) => deleteProject(id), onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }) });

  const diamondAction = (action: string) => {
    if (action === 'upload') fileRef.current?.click();
    else if (action === 'brand') navigate('/generate/2');
    else if (action === 'assets') document.getElementById('projects')?.scrollIntoView({ behavior: 'smooth' });
    else setShowCreate(true);
  };

  const fetchStrategyPreview = async (brief: any) => {
    setStrategyLoading(true);
    try {
      const resp = await fetch('/api/v1/strategy/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brief, platform_id: selectedPlatform }),
      });
      const data = await resp.json();
      setStrategyData(data.strategy);
      setReviewQuestions([]);
      setReviewBrief(brief);
    } catch (e) {
      alert('策略生成失败，请重试');
    }
    finally { setStrategyLoading(false); }
  };

  const confirmGenerate = async () => {
    if (!reviewBrief) return;
    setStrategyData(null);
    const fd = new FormData();
    fd.append('parsed_brief_json', JSON.stringify(reviewBrief));
    fd.append('skip_review', 'true');
    fd.append('project_id', '2');
    if (selectedPlatform) fd.append('platform_id', selectedPlatform);
    await callGenerateAPI(fd);
  };

  const retryStrategy = async () => {
    if (!reviewBrief) return;
    await fetchStrategyPreview(reviewBrief);
  };

  const callGenerateAPI = async (formData: FormData) => {
    if (selectedPlatform && !formData.has('platform_id')) formData.append('platform_id', selectedPlatform);
    setUploading(true);
    try {
      const resp = await fetch('/api/v1/generate-from-document', { method: 'POST', body: formData });
      const data = await resp.json();
      if (data.needs_review) {
        // 显示追问
        setReviewQuestions(data.questions || []);
        setReviewBrief(data.parsed_brief);
      } else if (data.parsed_brief && data.generation) {
        // 完整生成完成 → 跳转结果页
        navigate('/generate/2', { state: { brief: data.parsed_brief, result: data.generation } });
      } else if (data.parsed_brief) {
        // 追问已解决或无需追问 → 拉取策略预览
        setReviewBrief(data.parsed_brief);
        fetchStrategyPreview(data.parsed_brief);
      } else {
        alert(data.detail || '生成失败');
      }
    } catch (e: any) { alert('请求失败'); }
    finally { setUploading(false); }
  };

  const handleUpload = async (file: File) => {
    const fd = new FormData(); fd.append('file', file); fd.append('project_id', '2'); fd.append('strategy_first', 'true');
    await callGenerateAPI(fd);
  };

  const handleText = async () => {
    if (!taskText.trim()) return;
    const fd = new FormData(); fd.append('text', taskText); fd.append('project_id', '2'); fd.append('strategy_first', 'true');
    await callGenerateAPI(fd);
  };

  const handleResubmit = async (answers: Record<string, string>) => {
    if (!reviewBrief) return;
    const fd = new FormData();
    fd.append('parsed_brief_json', JSON.stringify(reviewBrief));
    fd.append('answers', JSON.stringify(answers));
    fd.append('project_id', '2');
    fd.append('strategy_first', 'true');
    await callGenerateAPI(fd);
  };

  const handleSkipReview = async () => {
    if (!reviewBrief) return;
    const fd = new FormData();
    fd.append('parsed_brief_json', JSON.stringify(reviewBrief));
    fd.append('skip_review', 'true');
    fd.append('project_id', '2');
    fd.append('strategy_first', 'true');
    await callGenerateAPI(fd);
  };

  return (
    <div className="liquid-page min-h-screen text-gray-100">
      <input ref={fileRef} type="file" className="hidden" accept=".pdf,.pptx,.docx,.xlsx,.txt,.csv,.png,.jpg,.webp"
        onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f); }} />

      {/* Header — Apple-style: minimal, transparent */}
      <header className="sticky top-0 z-10 backdrop-blur-xl px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ThemeToggle isLight={isLight} toggle={toggleTheme} />
          <img src="/logo.png" alt="Logo" className="w-8 h-8 rounded-lg object-contain" />
          <span className="font-semibold text-sm tracking-tight text-white/80">视觉 Agent</span>
        </div>
        <button onClick={() => setShowCreate(true)} className="text-sm text-gray-400 hover:text-white transition-colors">新建项目 →</button>
      </header>

      {/* Single column content */}
      <main className="max-w-4xl mx-auto px-6 pt-28 pb-32 flex flex-col items-center gap-20">

        {/* Hero */}
        <div className="text-center space-y-6">
          <p className="text-[11px] tracking-[0.2em] uppercase text-gray-500">AI-Powered Visual Content</p>
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-extrabold text-white leading-[1.1] tracking-tight">
            上传产品资料<br />自动生成<span className="text-gray-400">全套视觉素材</span>
          </h1>
          <p className="text-base text-gray-500 max-w-lg mx-auto leading-relaxed">拖拽 PDF / PPT / Word 或直接输入产品描述，AI 自动提取卖点并生成六类视觉素材</p>
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

        {/* Input + tags — grouped together */}
        <div className="w-full flex flex-col items-center gap-6">
          {reviewQuestions.length === 0 && !strategyData && (
            <div className="w-full max-w-2xl mx-auto">
              <div className="border border-white/10 rounded-2xl bg-white/[0.02] p-5 hover:border-white/20 transition-colors">
                <textarea
                  className="w-full bg-transparent border-0 text-base text-gray-100 placeholder-gray-500 resize-none focus:outline-none min-h-[140px] leading-relaxed"
                  placeholder="输入产品描述，例如：300L商用冷柜，不锈钢外壳，快速制冷，节能R290制冷剂，目标市场欧美中东..."
                  value={taskText}
                  onChange={e => setTaskText(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleText(); } }} />
                <div className="flex items-center justify-between mt-2 pt-3 border-t border-white/5">
                  <button onClick={() => fileRef.current?.click()}
                    className="text-sm text-gray-500 hover:text-white transition-colors">
                    上传文档 →
                  </button>
                  <button onClick={handleText} disabled={!taskText.trim() || uploading}
                    className="text-sm font-medium text-white hover:text-gray-300 disabled:text-gray-700 transition-colors">
                    {uploading ? '生成中...' : '生成 →'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Scene tags + platform */}
          <div className="flex flex-col items-center gap-5">
            <div className="flex flex-wrap gap-1.5 justify-center max-w-md">
              {SCENES.map(s => (
                <button key={s.name} onClick={() => setTaskText((prev) => prev + ' ' + s.name + '物料')}
                  className="px-2.5 py-1 rounded-full border border-white/10 bg-white/5 text-[11px] text-gray-500 hover:border-white/20 hover:text-gray-300 transition-colors">
                  {s.icon} {s.name}
                </button>
              ))}
            </div>

            <div className="flex flex-wrap gap-1.5 justify-center">
              <span className="text-[11px] text-gray-600 mr-1 self-center">平台：</span>
              {PLATFORMS.map(p => (
                <button key={p.id}
                  onClick={() => setSelectedPlatform(selectedPlatform === p.id ? null : p.id)}
                  className={`px-2.5 py-1 rounded-full border text-[11px] transition-colors ${
                    selectedPlatform === p.id
                      ? 'border-white/30 bg-white/10 text-gray-200'
                      : 'border-white/10 bg-white/5 text-gray-500 hover:border-white/20 hover:text-gray-300'
                  }`}>
                  {p.icon} {p.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Strategy confirmation — shown after review resolved */}
        {strategyData && reviewBrief && (
          <StrategyPanel
            strategy={strategyData}
            onConfirm={confirmGenerate}
            onRetry={retryStrategy}
            loading={uploading || strategyLoading}
          />
        )}

        {/* Agent progress — shown during generation */}
        <AgentProgress active={uploading && reviewQuestions.length === 0 && !strategyData} />

        {/* Diamond cluster — 菱形导航 */}
        <div className="liquid-diamond-cluster relative h-[280px] w-[280px] sm:h-[340px] sm:w-[340px] mx-auto">
          {DIAMONDS.map((d, i) => (
            <button key={d.title} onClick={() => diamondAction(d.action)}
              className={`liquid-diamond group absolute flex h-[120px] w-[120px] rotate-45 items-center justify-center rounded-2xl text-gray-100 transition duration-300 hover:z-10 sm:h-[140px] sm:w-[140px] sm:rounded-[22px] ${
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

        {/* Projects */}
        <div id="projects" className="w-full space-y-3">
          <h2 className="text-sm font-medium text-gray-500 text-center tracking-wide">最近项目</h2>
          {isLoading && <p className="text-gray-600 text-center py-6 text-sm">加载中...</p>}
          {projects?.length === 0 && (
            <div className="border border-white/5 rounded-2xl p-10 text-center">
              <p className="text-gray-600 text-sm">还没有项目</p>
              <button onClick={() => fileRef.current?.click()} className="mt-3 text-gray-400 text-xs hover:text-white transition-colors">上传第一个文档 →</button>
            </div>
          )}
          {projects?.map(p => (
            <div key={p.id} className="border border-white/5 rounded-2xl px-5 py-4 cursor-pointer group flex items-center justify-between hover:border-white/10 transition-colors"
              onClick={() => navigate('/generate/' + p.id)}>
              <div>
                <span className="text-sm text-gray-300 group-hover:text-white">{p.name}</span>
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
              <button onClick={() => createMut.mutate()} disabled={!name.trim()} className="px-4 py-2 bg-white rounded-lg text-sm text-black font-medium">创建</button>
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm text-gray-500 hover:text-white transition-colors">取消</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}