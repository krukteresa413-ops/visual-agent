import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { generateAll, exportMarkdown, saveBrief, getProjectBrief } from '../api/client';
import type { ProductBrief, VisualAssetPlan } from '../api/client';
import BriefForm from '../components/BriefForm';
import BriefParsePanel from '../components/BriefParsePanel';
import MissingFieldsAlert from '../components/MissingFieldsAlert';
import ImageUploader from '../components/ImageUploader';
import DocumentUploader from '../components/DocumentUploader';
import ResultTabs from '../components/ResultTabs';
import CanvasView from '../components/CanvasView';
import CopywritingPanel from '../components/CopywritingPanel';
import ThemeToggle, { useTheme } from '../components/ThemeToggle';

const DF: ProductBrief = { product_name:'', category:'', specifications:[], selling_points:[], target_market:[], usage_scenarios:[], brand_style: "" };

export default function GeneratePage() {
  const { projectId } = useParams<{projectId:string}>();
  const pid = Number(projectId) || 2;
  const [brief, setBrief] = useState<ProductBrief>(DF);
  const [result, setResult] = useState<VisualAssetPlan | null>(null);
  const [images, setImages] = useState<any>(null);
  const [copied, setCopied] = useState(false);
  const [mode, setMode] = useState<'manual'|'parse'|'doc'>('manual');
  const [missing, setMissing] = useState<any[]>([]);
  const [startTime, setStartTime] = useState(0);
  const { isLight, toggle: toggleTheme } = useTheme();
  const [viewMode, setViewMode] = useState<'tabs' | 'canvas'>('canvas');
  const [uploadedImages, setUploadedImages] = useState<Array<{filename:string;url:string}>>([]);

    useEffect(() => {
    const st = (window as any).__reactRouterState || history.state?.usr || {};
    if (st.images) setImages(st.images);
    if (st.result) {
      setResult(st.result);
      if (st.brief) setBrief(st.brief);
    }
  }, []);

  const { data: saved } = useQuery({ queryKey: ['brief', pid], queryFn: () => getProjectBrief(pid) });
  useEffect(() => { if (saved?.brief) setBrief(saved.brief); }, [saved]);

  const gen = useMutation({
    mutationFn: async () => { setStartTime(Date.now()); const d = await generateAll({ project_id: pid, brief }); return { data: d, elapsed: ((Date.now()-startTime)/1000).toFixed(0) }; },
    onSuccess: async ({ data }) => { try { await saveBrief(pid, brief); } catch(e){} setResult(data); },
  });

  const copy = async () => { try { const { markdown } = await exportMarkdown(pid); await navigator.clipboard.writeText(markdown); setCopied(true); setTimeout(()=>setCopied(false),2000); } catch(e){} };
  const ready = brief.product_name && brief.selling_points.length > 0;
  const btnClass = ready && !gen.isPending ? 'bg-orange-500 hover:bg-orange-400 text-white shadow-lg shadow-orange-500/20' : 'bg-white/5 text-gray-500 cursor-not-allowed';

  return (
    <div className="liquid-page min-h-screen">
      {/* Glass header */}
      <header className="sticky top-0 z-50 border-b border-white/5 bg-black/20 backdrop-blur-2xl px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ThemeToggle isLight={isLight} toggle={toggleTheme} />
          <a href="/" className="text-gray-400 hover:text-gray-200 mr-2 text-sm transition-colors">← 返回</a>
          <img src="/logo.png" alt="Logo" className="w-8 h-8 rounded-lg object-contain" />
          <span className="font-semibold text-lg text-white tracking-tight">视觉 Agent</span>
        </div>
        <div className="flex items-center gap-3">
          {result && <span className="text-xs text-gray-400">耗时 {gen.data?.elapsed||'?'}s</span>}
          {result && <button onClick={copy} className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm text-gray-200 transition-all">{copied?'已复制':'复制 Markdown'}</button>}
          {result && (
            <button onClick={() => setViewMode(m => m === 'canvas' ? 'tabs' : 'canvas')}
              className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs text-gray-300 transition-all">
              {viewMode === 'canvas' ? '📋 标签视图' : '🎨 画布视图'}
            </button>
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-10">
        <div className="grid gap-8" style={{gridTemplateColumns:result?'380px 1fr':'480px 1fr'}}>
          {/* Left: input area */}
          <div className="space-y-5">
            {/* Mode selector */}
            <div className="liquid-card p-6">
              <div className="flex items-center gap-3 mb-3"><span className="text-2xl">📋</span><h2 className="text-lg font-semibold text-white">产品资料</h2></div>
              <div className="flex gap-2">
                <button onClick={()=>setMode('manual')} className={`flex-1 py-2 text-xs rounded-lg transition-colors ${mode==='manual'?'bg-orange-500 text-white':'bg-white/5 text-gray-400 hover:text-gray-200 border border-white/10'}`}>手动填写</button>
                <button onClick={()=>setMode('parse')} className={`flex-1 py-2 text-xs rounded-lg transition-colors ${mode==='parse'?'bg-blue-600 text-white':'bg-white/5 text-gray-400 hover:text-gray-200 border border-white/10'}`}>智能解析</button>
                <button onClick={()=>setMode('doc')} className={`flex-1 py-2 text-xs rounded-lg transition-colors ${mode==='doc'?'bg-green-600 text-white':'bg-white/5 text-gray-400 hover:text-gray-200 border border-white/10'}`}>上传文档</button>
              </div>
            </div>
            {mode==='parse' && <BriefParsePanel onParsed={(p,m)=>{setBrief(p);setMissing(m);setMode('manual');}} />}
            {mode==='doc' && <DocumentUploader onParsed={(p,m,_preview)=>{setBrief(p);setMissing(m);setMode('manual');}} />}
            <MissingFieldsAlert fields={missing} onDismiss={()=>setMissing([])} />
            <div className="liquid-card p-6"><BriefForm value={brief} onChange={setBrief} /></div>
            <ImageUploader images={uploadedImages} onChange={setUploadedImages} />
            <button onClick={()=>gen.mutate()} disabled={!ready||gen.isPending} className={`w-full py-4 rounded-2xl font-semibold text-base transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed ${btnClass}`}>
              {gen.isPending
                ? <span className="flex items-center justify-center gap-3"><svg className="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>并行生成中...</span>
                : '一键生成六类素材'}
            </button>
            {gen.isError && <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">生成失败</div>}
          </div>

          {/* Right: results */}
          <div className="liquid-card p-6 min-h-[600px]">
            {result ? (
            viewMode === 'canvas' ? (
              <CanvasView
                mainImage={result.main_image}
                whiteBg={result.white_bg}
                sceneImages={result.scene_images}
                sellingPoints={result.selling_points}
                videoScripts={result.video_scripts}
                adMaterial={result.ad_material}
                brief={brief}
              />
            ) : <ResultTabs plan={result} images={images} />
          ) : (
              <div className="flex flex-col items-center justify-center h-full text-gray-500">
                <div className="text-5xl mb-5">✨</div>
                <p className="text-lg mb-2">准备好开始了吗？</p>
                <p className="text-sm">填写左侧产品资料，点击生成按钮</p>
              </div>
            )}
          </div>

          {/* Copywriting Panel */}
          {result && <CopywritingPanel brief={brief} />}
        </div>
      </main>

      {/* Background orbs */}
      <div className="liquid-orb pointer-events-none fixed right-16 top-40 w-64 h-64 rotate-45 rounded-[40px] opacity-50 -z-10" />
      <div className="liquid-orb pointer-events-none fixed left-12 bottom-20 w-48 h-48 rotate-45 rounded-[32px] opacity-30 -z-10" />
    </div>
  );
}