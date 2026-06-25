import { useEffect, useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from '../components/Toast';
import ReviewQuestions from '../components/ReviewQuestions';
import StrategyPanel from '../components/StrategyPanel';
import BriefReviewPanel from '../components/BriefReviewPanel';
import ThemeToggle, { useTheme } from '../components/ThemeToggle';
import LibraryPanel from '../components/LibraryPanel';
import InspirationPanel from '../components/InspirationPanel';
// Prevent Vite tree-shaking
const _refInspirationPanel = InspirationPanel; void _refInspirationPanel;// Prevent tree-shaking
import AuthPage from './AuthPage';
import { api } from '../api/client';


const DIAMONDS = [
  { title: '灵感库', desc: '创意灵感', icon: '💡', action: 'inspiration' },
  { title: '资料库', desc: '品牌与产品资产', icon: '📚', action: 'library' },
  { title: '个人中心', desc: '账户与积分', icon: '👤', action: 'profile' },
  { title: '项目库', desc: '项目陈列柜', icon: '📁', action: 'projects' },
];

const PROJECT_COVER_GRADIENTS = [
  'from-orange-500/30 via-rose-400/14 to-white/[0.03]',
  'from-sky-400/22 via-orange-400/12 to-white/[0.03]',
  'from-emerald-400/18 via-orange-300/14 to-white/[0.03]',
  'from-violet-400/20 via-orange-400/12 to-white/[0.03]',
];


function ProfileGallery({ onClose }: { onClose: () => void }) {
  const profileCards = [
    { title: '积分中心', value: '1,280', desc: '当前可用积分', icon: '✦' },
    { title: '项目资产', value: '2', desc: '已创建项目', icon: '◇' },
    { title: '会员状态', value: '免费版', desc: '可升级更多生成额度', icon: '●' },
    { title: '账户设置', value: '待完善', desc: '邮箱、团队与偏好设置', icon: '◐' },
  ];
  return (
    <div data-profile-gallery className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-xl px-4 py-8 animate-fadeIn" onClick={onClose}>
      <section className="mx-auto w-full max-w-5xl rounded-[28px] border border-white/[0.14] bg-gradient-to-br from-white/[0.13] via-white/[0.07] to-white/[0.03] p-5 shadow-[0_30px_100px_rgba(0,0,0,0.55),inset_0_1px_0_rgba(255,255,255,0.16)]" onClick={e => e.stopPropagation()}>
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-1 text-[11px] font-medium tracking-[0.18em] text-orange-200/90 uppercase">
              Profile Gallery
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white">个人陈列柜</h2>
            <p className="mt-1 text-sm text-gray-400">账户、积分和创作资产集中管理 · 保持首页同一套陈列语言</p>
          </div>
          <button onClick={onClose} className="rounded-full border border-white/[0.12] bg-white/[0.05] px-3 py-2 text-xs text-gray-400 transition-colors hover:text-white">返回</button>
        </div>

        <div className="mb-3 flex items-center justify-between border-t border-white/[0.08] pt-4">
          <span className="text-xs font-semibold tracking-[0.16em] text-gray-500 uppercase">账户概览</span>
          <span className="text-[11px] text-gray-600">单次点击查看，不打断首页路径</span>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {profileCards.map(card => (
            <div key={card.title} className="profile-gallery-card overflow-hidden rounded-3xl border border-white/[0.12] bg-white/[0.055] p-4 transition-all duration-500 hover:-translate-y-1 hover:border-orange-400/45 hover:bg-white/[0.08] hover:shadow-[0_24px_70px_rgba(251,146,60,0.16)]">
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl border border-orange-400/20 bg-orange-500/10 text-xl text-orange-200">{card.icon}</div>
              <div className="text-[11px] tracking-[0.16em] text-gray-500 uppercase">{card.title}</div>
              <div className="mt-2 text-2xl font-semibold text-white">{card.value}</div>
              <p className="mt-2 text-xs leading-5 text-gray-500">{card.desc}</p>
            </div>
          ))}
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <Link to="/dashboard" className="profile-gallery-card group rounded-3xl border border-white/[0.12] bg-white/[0.055] p-4 transition-all duration-500 hover:-translate-y-1 hover:border-orange-400/45 hover:bg-white/[0.08] hover:shadow-[0_24px_70px_rgba(251,146,60,0.16)]">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-white">创作总览</div>
                <p className="mt-1 text-xs text-gray-500">查看项目、生成记录与创作状态</p>
              </div>
              <span className="text-orange-300 transition-transform group-hover:translate-x-1">Dashboard →</span>
            </div>
          </Link>
          <Link to="/history" className="profile-gallery-card group rounded-3xl border border-white/[0.12] bg-white/[0.055] p-4 transition-all duration-500 hover:-translate-y-1 hover:border-orange-400/45 hover:bg-white/[0.08] hover:shadow-[0_24px_70px_rgba(251,146,60,0.16)]">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-white">历史记录</div>
                <p className="mt-1 text-xs text-gray-500">回看过往生成与项目演进</p>
              </div>
              <span className="text-orange-300 transition-transform group-hover:translate-x-1">History →</span>
            </div>
          </Link>
        </div>
      </section>
    </div>
  );
}

function ProjectGallery({
  projects,
  loading,
  onClose,
  onOpenProject,
  onCreateProject,
}: {
  projects: Array<{ id: number; name: string; description?: string | null; created_at?: string | null; generation_count?: number }>;
  loading: boolean;
  onClose: () => void;
  onOpenProject: (id: number) => void;
  onCreateProject: () => void;
}) {
  const visibleProjects = projects.slice(0, 6);
  return (
    <div data-project-gallery className="fixed inset-0 z-50 overflow-y-auto bg-black/60 backdrop-blur-xl px-4 py-8 animate-fadeIn" onClick={onClose}>
      <section className="mx-auto w-full max-w-5xl rounded-[28px] border border-white/[0.14] bg-gradient-to-br from-white/[0.13] via-white/[0.07] to-white/[0.03] p-5 shadow-[0_30px_100px_rgba(0,0,0,0.55),inset_0_1px_0_rgba(255,255,255,0.16)]" onClick={e => e.stopPropagation()}>
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-1 text-[11px] font-medium tracking-[0.18em] text-orange-200/90 uppercase">
              Project Gallery
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white">项目陈列柜</h2>
            <p className="mt-1 text-sm text-gray-400">继续你的视觉创作项目 · 最近项目以作品封面方式陈列</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={onCreateProject} className="rounded-full border border-orange-400/30 bg-orange-500/15 px-4 py-2 text-xs font-semibold text-orange-100 transition-all duration-300 hover:bg-orange-500/25 hover:shadow-[0_0_28px_rgba(251,146,60,0.22)]">新建项目</button>
            <button onClick={onClose} className="rounded-full border border-white/[0.12] bg-white/[0.05] px-3 py-2 text-xs text-gray-400 transition-colors hover:text-white">返回</button>
          </div>
        </div>

        <div className="mb-3 flex items-center justify-between border-t border-white/[0.08] pt-4">
          <span className="text-xs font-semibold tracking-[0.16em] text-gray-500 uppercase">最近项目</span>
          <span className="text-[11px] text-gray-600">单击继续，不增加路径</span>
        </div>

        {loading ? (
          <div className="grid gap-3 sm:grid-cols-3">
            {[0, 1, 2].map(i => <div key={i} className="h-56 animate-pulse rounded-3xl bg-white/[0.06]" />)}
          </div>
        ) : visibleProjects.length > 0 ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {visibleProjects.map((project, i) => (
              <button key={project.id} onClick={() => onOpenProject(project.id)} className="project-gallery-card group overflow-hidden rounded-3xl border border-white/[0.12] bg-white/[0.055] text-left transition-all duration-500 hover:-translate-y-1 hover:border-orange-400/45 hover:bg-white/[0.08] hover:shadow-[0_24px_70px_rgba(251,146,60,0.16)]">
                <div className={`relative h-32 bg-gradient-to-br ${PROJECT_COVER_GRADIENTS[i % PROJECT_COVER_GRADIENTS.length]}`}>
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_28%_22%,rgba(255,255,255,0.28),transparent_30%),radial-gradient(circle_at_76%_70%,rgba(251,146,60,0.22),transparent_34%)]" />
                  <div className="absolute left-4 top-4 rounded-full border border-white/15 bg-black/20 px-2 py-1 text-[10px] text-white/70 backdrop-blur-md">项目封面</div>
                  <div className="absolute bottom-3 right-3 h-10 w-10 rounded-2xl border border-white/15 bg-white/10 backdrop-blur-md transition-transform duration-300 group-hover:rotate-6 group-hover:scale-110" />
                </div>
                <div className="space-y-3 p-4">
                  <div>
                    <h3 className="truncate text-sm font-semibold text-white">{project.name || '未命名项目'}</h3>
                    <p className="mt-1 line-clamp-2 min-h-[32px] text-xs leading-4 text-gray-500">{project.description || '空白画布 · 等待第一轮创作'}</p>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="rounded-full bg-white/[0.06] px-2 py-1 text-gray-400">{project.generation_count || 0} 次生成</span>
                    <span className="inline-flex items-center gap-1 text-orange-300"><span className="h-1.5 w-1.5 rounded-full bg-orange-400" />继续创作</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="rounded-3xl border border-dashed border-white/[0.14] bg-white/[0.04] px-6 py-10 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-3xl border border-orange-400/20 bg-orange-500/10 text-3xl">📁</div>
            <h3 className="text-sm font-semibold text-white">还没有陈列项目</h3>
            <p className="mx-auto mt-2 max-w-sm text-xs leading-5 text-gray-500">从一个空白画布或一份产品资料开始，项目会以作品封面的形式陈列在这里。</p>
            <button onClick={onCreateProject} className="mt-5 rounded-full bg-white px-4 py-2 text-xs font-semibold text-black transition-transform hover:scale-105">新建项目</button>
          </div>
        )}
      </section>
    </div>
  );
}


export default function ProjectsPage() {
  const navigate = useNavigate();
  const { isLight, toggle: toggleTheme } = useTheme();
  const fileRef = useRef<HTMLInputElement>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [showProjectGallery, setShowProjectGallery] = useState(false);
  const [projectGalleryItems, setProjectGalleryItems] = useState<Array<{ id: number; name: string; description?: string | null; created_at?: string | null; generation_count?: number }>>([]);
  const [projectGalleryLoading, setProjectGalleryLoading] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [taskText, setTaskText] = useState('');
  const [uploading, setUploading] = useState(false);

  const [reviewQuestions, setReviewQuestions] = useState<Array<{field:string;level:string;question:string;hint:string}>>([]);
  const [reviewBrief, setReviewBrief] = useState<any>(null);
  const [strategyData, setStrategyData] = useState<any>(null);
  const [strategyLoading, setStrategyLoading] = useState(false);
  const [showBriefReview, setShowBriefReview] = useState(false);
  const [showLibrary, setShowLibrary] = useState(false);
  const [showInspiration, setShowInspiration] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [showQuickGen, setShowQuickGen] = useState(false);
  const [quickPrompt, setQuickPrompt] = useState('');
  const [showAuth, setShowAuth] = useState(false);
  const [uploadedPdfText, setUploadedPdfText] = useState('');

  const diamondAction = (action: string) => {
    if (action === 'library') { setShowLibrary(true); return; }
    else if (action === 'projects') { setShowProjectGallery(true); return; }
    else if (action === 'inspiration') { setShowInspiration(true); return; }
    else if (action === 'profile') { setShowProfile(true); return; }
    else toast('功能开发中');
  };

  useEffect(() => {
    if (!showProjectGallery) return;
    let cancelled = false;
    setProjectGalleryLoading(true);
    api.projects.list()
      .then(items => { if (!cancelled) setProjectGalleryItems(items); })
      .catch(() => { if (!cancelled) toast('项目库加载失败'); })
      .finally(() => { if (!cancelled) setProjectGalleryLoading(false); });
    return () => { cancelled = true; };
  }, [showProjectGallery]);

  const handleQuickGen = () => {
    if (!quickPrompt.trim()) return;
    const prompt = quickPrompt;
    setShowQuickGen(false);
    setQuickPrompt('');
    navigate('/generate/new', { state: { quickMode: true, prompt } });
  };

  const createEmptyCanvasProject = async () => {
    try {
      const project = await api.projects.create('未命名项目', '');
      navigate(`/generate/${project.id}`);
    } catch (e) {
      toast('新建项目失败，请重试');
    }
  };

  const fetchStrategyPreview = async (brief: any) => {
    setStrategyLoading(true);
    try {
      const resp = await fetch('/api/v1/strategy/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brief }),
      });
      if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}));
      if (resp.status === 422) {
        toast('表单信息不完整: ' + (errData.detail || '请补充必填字段'));
      } else if (resp.status === 500) {
        toast('后端生成失败: ' + (errData.detail || '服务器内部错误'));
      } else {
        toast('请求失败 (' + resp.status + '): ' + (errData.detail || resp.statusText));
      }
      setUploading(false);
      return;
    }
    const data = await resp.json();
      setStrategyData(data.strategy);
      setReviewQuestions([]);
      setReviewBrief(brief);
    } catch (e: any) {
      toast('策略生成失败，请重试');
    }
    finally { setStrategyLoading(false); }
  };

  const confirmGenerate = async (brief?: any) => {
    const b = brief || reviewBrief;
    if (!b) return;
    setStrategyData(null);
    const fd = new FormData();
    fd.append('parsed_brief_json', JSON.stringify(b));
    fd.append('skip_review', 'true');
    fd.append('generate_images', 'true');
    fd.append('project_id', '2');
    await callGenerateAPI(fd);
  };

  const retryStrategy = async () => {
    if (!reviewBrief) return;
    await fetchStrategyPreview(reviewBrief);
  };

  const callGenerateAPI = async (formData: FormData) => {
    setUploading(true);
    try {
      const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000);
    const resp = await fetch('/api/v1/generate-from-document', {
      method: 'POST', body: formData, signal: controller.signal,
    });
    clearTimeout(timeoutId);
      if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}));
      if (resp.status === 422) {
        toast('表单信息不完整: ' + (errData.detail || '请补充必填字段'));
      } else if (resp.status === 500) {
        toast('后端生成失败: ' + (errData.detail || '服务器内部错误'));
      } else {
        toast('请求失败 (' + resp.status + '): ' + (errData.detail || resp.statusText));
      }
      setUploading(false);
      return;
    }
    const data = await resp.json();
      if (data.parsed_brief && data.generation) {
        navigate('/generate/new', { state: { quickMode: true, prompt: taskText, brief: data.parsed_brief, result: data.generation } });
      } else if (data.parsed_brief) {
        navigate('/generate/new', { state: { quickMode: true, prompt: taskText, brief: data.parsed_brief, reviewQuestions: data.questions || [] } });
      } else {
        toast(data.detail || '生成失败');
      }
    } catch (e: any) {
      if (e.name === 'AbortError') {
        toast('请求超时，正在后台继续处理…');
      } else if (e.message) {
        toast('请求失败: ' + e.message);
      } else {
        toast('请求失败，请检查网络连接');
      }
    }
    finally { setUploading(false); }
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const fd = new FormData(); fd.append('file', file);
      const resp = await fetch('/api/v1/upload/document/parse', {
        method: 'POST',
        body: fd,
        headers: {},
      });
      if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}));
      if (resp.status === 422) {
        toast('表单信息不完整: ' + (errData.detail || '请补充必填字段'));
      } else if (resp.status === 500) {
        toast('后端生成失败: ' + (errData.detail || '服务器内部错误'));
      } else {
        toast('请求失败 (' + resp.status + '): ' + (errData.detail || resp.statusText));
      }
      setUploading(false);
      return;
    }
    const data = await resp.json();
      if (data.extracted_text_preview) setUploadedPdfText(data.extracted_text_preview);
      if (data.parsed_brief) {
        setReviewBrief(data.parsed_brief);
        setReviewQuestions([]);
        setTimeout(() => setShowBriefReview(true), 300);
      } else {
        toast(data.detail || '解析失败');
      }
    } catch (e: any) {
      toast('解析失败: ' + (e?.message || '网络错误'));
    }
    finally { setUploading(false); }
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
    fd.append('generate_images', 'true');
    fd.append('project_id', '2');
    fd.append('strategy_first', 'true');
    await callGenerateAPI(fd);
  };

  const handleUseStyle = (prompt: string, item: any) => {
    navigate('/generate/2', { state: { promptTemplate: prompt, inspirationItem: item } });
  };

  return (
    <div className="liquid-page min-h-screen text-gray-100">
      
      <input ref={fileRef} type="file" className="hidden" accept=".pdf,.pptx,.docx,.xlsx,.txt,.csv,.png,.jpg,.webp"
        onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f); }} />


      {/* Floating theme toggle */}
      {/* Floating theme toggle */}      <header className="sticky top-0 z-10 px-6 py-2 flex items-start justify-between">
        <div className="flex flex-col items-start gap-0.5">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="MOYAG" className="w-5 h-5 rounded-md object-contain" />
            <span className="font-bold text-xs tracking-tight text-white/90">MOYAG</span>
          </div>
          <div className="pt-1"><ThemeToggle isLight={isLight} toggle={toggleTheme} /></div>
        </div>
        <p className="text-[11px] tracking-[0.2em] uppercase text-gray-500/80 mb-0 leading-none">AI-Powered Visual Content</p>
        <div className="flex flex-col items-end gap-1">
          <div className="flex items-center gap-1.5 text-sm">
            <span className="text-gray-500">积分</span>
            <span className="font-mono text-white/90 tabular-nums">1,280</span>
          </div>
          
        </div>
      </header>

      {showBriefReview && reviewBrief ? (
        <div className="min-h-screen flex items-start justify-center pt-12 px-4 animate-fadeIn">
          <div className="w-full max-w-5xl">
            <BriefReviewPanel missing={[]}
              brief={reviewBrief}
              onConfirm={(editedBrief) => {
                setReviewBrief(editedBrief);
                setShowBriefReview(false);
                confirmGenerate(editedBrief);
              }}
              onReupload={() => {
                setShowBriefReview(false);
                setReviewBrief(null);
                setReviewQuestions([]);
                setStrategyData(null);
              }}
            />
          </div>
        </div>
      ) : (
      <main className="max-w-2xl mx-auto px-6 pt-2 pb-12 flex flex-col items-center relative z-10">

        <div className="text-center mb-2">
          <h1 className="text-3xl md:text-5xl lg:text-6xl font-extrabold leading-[1.05] tracking-tight mb-1 bg-gradient-to-br from-gray-300 to-gray-400 bg-clip-text text-transparent" style={{ letterSpacing: '-0.02em' }}>
            让设计更简单
          </h1>
          <p className="text-xs text-gray-500 max-w-lg mx-auto leading-snug">拖拽 PDF / PPT / Word 或直接输入产品描述，AI 自动提取卖点并生成六类视觉素材</p>
        </div>

        {reviewQuestions.length > 0 && reviewBrief && (
          <div className="mb-3 w-full">
            <ReviewQuestions
              questions={reviewQuestions}
              parsedBrief={reviewBrief}
              onResubmit={handleResubmit}
              onSkip={handleSkipReview}
              loading={uploading}
            />
          </div>
        )}

        {reviewQuestions.length === 0 && !strategyData && (
          <div className="w-full max-w-2xl mx-auto mb-3">
            <div className="relative rounded-2xl bg-gradient-to-br from-white/[0.08] via-white/[0.04] to-transparent border border-white/[0.12] p-4 transition-all duration-500 focus-within:border-orange-500/30 focus-within:shadow-[0_0_50px_rgba(251,146,60,0.06),inset_0_1px_0_0_rgba(255,255,255,0.1)] hover:border-white/[0.15] backdrop-blur-xl">
              <div className="flex items-center gap-2 mb-1.5 text-[11px] text-gray-400/80 tracking-[0.15em] uppercase">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
                产品描述
              </div>
              <textarea
                className="w-full bg-white/[0.04] rounded-xl px-3 py-2 text-[14px] text-gray-100 placeholder:text-gray-600/50 resize-none focus:outline-none focus:bg-white/[0.06] focus:ring-2 focus:ring-orange-500/20 min-h-[80px] leading-relaxed border border-white/[0.08] transition-all duration-500 focus:shadow-[0_0_20px_rgba(251,146,60,0.08),inset_0_1px_0_0_rgba(255,255,255,0.06)] focus:border-orange-500/30"
                placeholder="输入产品描述，例如：300L商用冷柜，不锈钢外壳，快速制冷，节能R290制冷剂，目标市场欧美中东..."
                value={taskText}
                onChange={e => setTaskText(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleText(); } }} />
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/[0.08]">
                <button
                  onClick={() => fileRef.current?.click()}
                  className="group inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-white/[0.12] bg-white/[0.03] text-[13px] text-gray-400 hover:text-white hover:border-orange-500/40 hover:bg-orange-500/10 transition-all duration-300 hover:shadow-[0_0_15px_rgba(251,146,60,0.15)]">
                  <svg className="w-3.5 h-3.5 transition-transform duration-300 group-hover:-translate-y-0.5 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  上传文档
                </button>
                <button
                  onClick={handleText}
                  disabled={!taskText.trim() || uploading}
                  className="group inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-[13px] font-semibold transition-all duration-300 relative overflow-hidden
                    enabled:bg-gradient-to-r enabled:from-white enabled:to-gray-100 enabled:text-black enabled:hover:shadow-[0_0_30px_rgba(255,255,255,0.2),0_0_60px_rgba(251,146,60,0.1)] enabled:hover:scale-[1.03] enabled:active:scale-[0.98] enabled:border enabled:border-white/20
                    disabled:bg-white/[0.05] disabled:text-gray-400 disabled:cursor-not-allowed disabled:border disabled:border-white/[0.05]">
                  <span className="absolute inset-0 bg-gradient-to-r from-orange-400/0 via-orange-300/10 to-orange-400/0 translate-x-[-100%] group-enabled:group-hover:translate-x-[100%] transition-transform duration-1000" />
                  {uploading ? (
                    <>
                      <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      生成中...
                    </>
                  ) : (
                    <>
                      生成
                      <svg className="w-3 h-3 transition-transform duration-300 group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {strategyData && reviewBrief && (
          <div className="mb-3 w-full">
            <StrategyPanel
              strategy={strategyData}
              onConfirm={confirmGenerate}
              onRetry={retryStrategy}
              loading={uploading || strategyLoading}
            />
          </div>
        )}

                <div className="liquid-diamond-cluster relative h-[260px] w-[260px] sm:h-[300px] sm:w-[300px] mx-auto mt-2 mb-4">
          {DIAMONDS.map((d, i) => (
            <button key={d.title} onClick={() => diamondAction(d.action)}
              className={`liquid-diamond group absolute flex h-[110px] w-[110px] rotate-45 items-center justify-center rounded-2xl text-gray-100 transition-all duration-500 hover:z-10 sm:h-[130px] sm:w-[130px] sm:rounded-[20px] backdrop-blur-xl bg-gradient-to-br from-white/[0.12] via-white/[0.06] to-white/[0.02] border border-white/[0.15] hover:border-orange-500/40 hover:from-orange-500/20 hover:via-white/[0.08] hover:to-transparent hover:shadow-[0_0_40px_rgba(251,146,60,0.25),inset_0_1px_0_0_rgba(255,255,255,0.2)] hover:scale-105 active:scale-95 ${
                i === 0 ? 'left-1/2 top-0 -translate-x-1/2' :
                i === 1 ? 'left-0 top-1/2 -translate-y-1/2' :
                i === 2 ? 'right-0 top-1/2 -translate-y-1/2' :
                'left-1/2 bottom-0 -translate-x-1/2'}`}
              style={{ zIndex: i === 0 ? 2 : 1 }}>
              <span className="-rotate-45 flex flex-col items-center gap-0.5 transition-transform duration-300 group-hover:scale-105">
                <span className="text-xl group-hover:scale-110 transition-transform duration-300">{d.icon}</span>
                <span className="whitespace-nowrap text-xs font-semibold text-white/90 group-hover:text-white">{d.title}</span>
                <span className="whitespace-nowrap text-[10px] text-gray-500 group-hover:text-gray-400 transition-colors">{d.desc}</span>
              </span>
            </button>
          ))}
          {/* 花心 — 新建入口 */}
          <button onClick={createEmptyCanvasProject}
            className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10 flex h-[72px] w-[72px] sm:h-[84px] sm:w-[84px] items-center justify-center rounded-full backdrop-blur-xl bg-gradient-to-br from-orange-500/30 via-rose-500/20 to-purple-500/20 border border-orange-400/30 shadow-[0_0_40px_rgba(251,146,60,0.3),inset_0_1px_0_0_rgba(255,255,255,0.15)] hover:shadow-[0_0_60px_rgba(251,146,60,0.5),inset_0_1px_0_0_rgba(255,255,255,0.25)] hover:scale-110 hover:border-orange-400/60 transition-all duration-500 group">
            <span className="flex flex-col items-center gap-0">
              <span className="text-3xl sm:text-[36px] font-light group-hover:scale-110 transition-transform duration-300">+</span>
              <span className="text-[10px] sm:text-[11px] font-semibold text-white/80 group-hover:text-white whitespace-nowrap">新建</span>
            </span>
          </button>
        </div>
      </main>
      )}

      {showQuickGen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md" onClick={() => setShowQuickGen(false)}>
          <div className="liquid-card p-6 w-full max-w-md mx-4 space-y-4 rounded-2xl" onClick={e => e.stopPropagation()} style={{background:'linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.04))', border:'1px solid rgba(255,255,255,0.15)'}}>
            <h3 className="text-lg font-semibold text-white">+ 新建</h3>
            <p className="text-sm text-gray-400">输入一句话，AI 自动生成视觉素材</p>
            <textarea className="w-full bg-white/[0.06] border border-white/[0.12] rounded-xl px-4 py-3 text-sm text-gray-100 placeholder-gray-500 focus:border-orange-500/40 resize-none h-24" placeholder="例如：帮我生成一张运动鞋海报" value={quickPrompt} onChange={e => setQuickPrompt(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleQuickGen(); }}} autoFocus />
            <div className="flex gap-2">
              <button onClick={handleQuickGen} disabled={!quickPrompt.trim()} className="flex-1 px-4 py-2.5 bg-gradient-to-r from-orange-500 to-rose-500 rounded-xl text-sm text-white font-semibold disabled:opacity-50">开始生成</button>
              <button onClick={() => setShowQuickGen(false)} className="px-4 py-2.5 text-sm text-gray-500 hover:text-white">取消</button>
            </div>
            <p className="text-[10px] text-gray-600 text-center">按 Enter 发送 · 2 步看到结果</p>
          </div>
        </div>
      )}

      {showProjectGallery && (
        <ProjectGallery
          projects={projectGalleryItems}
          loading={projectGalleryLoading}
          onClose={() => setShowProjectGallery(false)}
          onOpenProject={(id) => navigate(`/generate/${id}`)}
          onCreateProject={createEmptyCanvasProject}
        />
      )}

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md" onClick={() => setShowCreate(false)}>
          <div className="liquid-card backdrop-blur-2xl bg-gradient-to-br from-white/[0.12] to-white/[0.04] border border-white/[0.15] p-6 w-full max-w-sm mx-4 space-y-4 rounded-2xl shadow-[0_0_60px_rgba(0,0,0,0.5),inset_0_1px_0_0_rgba(255,255,255,0.1)]" onClick={e => e.stopPropagation()}>
            <h3 className="text-sm font-medium text-white">新建项目</h3>
            <input className="w-full bg-white/[0.06] border border-white/[0.12] rounded-xl px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-orange-500/40 focus:ring-2 focus:ring-orange-500/20 transition-all duration-300 focus:bg-white/[0.08]" placeholder="项目名称" value={name} onChange={e => setName(e.target.value)} />
            <input className="w-full bg-white/[0.06] border border-white/[0.12] rounded-xl px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-orange-500/40 focus:ring-2 focus:ring-orange-500/20 transition-all duration-300 focus:bg-white/[0.08]" placeholder="描述（可选）" value={desc} onChange={e => setDesc(e.target.value)} />
            <div className="flex gap-2">
              <button onClick={() => { toast("529f80fd5f0053d14e2d"); setShowCreate(false); }} disabled={!name.trim()} className="px-4 py-2 bg-gradient-to-r from-white to-gray-100 rounded-lg text-sm text-black font-medium hover:shadow-[0_0_25px_rgba(255,255,255,0.2)] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed">创建</button>
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm text-gray-500 hover:text-white transition-colors">取消</button>
            </div>
          </div>
        </div>
      )}

      {showLibrary && (
        <LibraryPanel
          projectId={2}
          hasUploadedPdf={!!uploadedPdfText}
          pdfText={uploadedPdfText}
          onClose={() => setShowLibrary(false)}
      />
      )}

      {showProfile && (
        <ProfileGallery onClose={() => setShowProfile(false)} />
      )}

      {showAuth && <AuthPage onClose={() => setShowAuth(false)} />}
      {showInspiration && (
        <InspirationPanel onClose={() => setShowInspiration(false)} onUseStyle={handleUseStyle} />
      )}
    </div>
  );
}