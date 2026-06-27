// @ts-nocheck
import { useState, useEffect, useRef } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api, generateAll, exportMarkdown, saveBrief, getProjectBrief } from '../api/client';
import type { ProductBrief, VisualAssetPlan } from '../types';
import BriefForm from '../components/BriefForm';
import BriefParsePanel from '../components/BriefParsePanel';
import BriefReviewPanel from '../components/BriefReviewPanel';
import MissingFieldsAlert from '../components/MissingFieldsAlert';
import ImageUploader from '../components/ImageUploader';
import DocumentUploader from '../components/DocumentUploader';
import ResultTabs from '../components/ResultTabs';
import CanvasView from '../components/CanvasView';
import AIChatPanel from '../components/AIChatPanel';
import LibraryPanel from '../components/LibraryPanel';
import CopywritingPanel from '../components/CopywritingPanel';
import AgentProgress from '../components/AgentProgress';
import ThemeToggle, { useTheme } from '../components/ThemeToggle';
import ModelPreferencePanel from '../components/model/ModelPreferencePanel';
import { formatElapsedSeconds } from '../lib/elapsed';


const DF: ProductBrief = { product_name:'', category:'', specifications:[], selling_points:[], target_market:[], usage_scenarios:[], brand_style: "" };

export default function GeneratePage() {
  const { projectId } = useParams<{projectId:string}>();
  const pid = Number(projectId) || 2;
  const [brief, setBrief] = useState<ProductBrief>(DF);
  const [result, setResult] = useState<VisualAssetPlan | null>(null);
  const [images, setImages] = useState<any>(null);
  const [copied, setCopied] = useState(false);
  const [mode, setMode] = useState<'manual'|'parse'|'doc'|'quick'>('quick');
  const [missing, setMissing] = useState<any[]>([]);
  const [showReview, setShowReview] = useState(false);
  const [startTime, setStartTime] = useState(0);
  const { isLight, toggle: toggleTheme } = useTheme();
  const [viewMode, setViewMode] = useState<'tabs' | 'canvas'>('canvas');
  const [uploadedImages, setUploadedImages] = useState<Array<{filename:string;url:string}>>([]);
  const [panelOpen, setPanelOpen] = useState(false);  // form panel expanded?
  const [rightPanel, setRightPanel] = useState<'chat' | 'brand' | null>('chat');  // 默认展开AI对话  // right side panel
  const [chatAssetContext, setChatAssetContext] = useState<ChatAssetContext | null>(null);
  const [genTaskId, setGenTaskId] = useState<string | null>(null);
  const [canvasRefreshNonce, setCanvasRefreshNonce] = useState(0);
  const [pendingSkillPrompt, setPendingSkillPrompt] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);
  const [qualityReport, setQualityReport] = useState<any>(null);
  // Day 1: Quick mode — skip form, go directly to canvas
  const [quickMode, setQuickMode] = useState(
    (location.state as any)?.quickMode || false
  );
  const [quickTaskId, setQuickTaskId] = useState<string | null>(
    (location.state as any)?.taskId || null
  );
  const [promptTemplate, setPromptTemplate] = useState<string | null>(null);
  const [quickPrompt, setQuickPrompt] = useState<string>('');
  const [quickBrief, setQuickBrief] = useState<Record<string, unknown> | null>(null);
  // Day 3.3: Reference image drag-and-drop
  const [refImage, setRefImage] = useState<{url: string; filename: string} | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadingRef, setUploadingRef] = useState(false);
  const [modelPanelOpen, setModelPanelOpen] = useState(false);
  const [activeModelKind, setActiveModelKind] = useState<'image' | 'video' | '3d'>('image');
  const [autoModel, setAutoModel] = useState(true);
  const [selectedImageModel, setSelectedImageModel] = useState<string | null>(null);
  const { data: modelOptions } = useQuery({ queryKey: ['generation', 'models', 'catalog'], queryFn: () => api.generation.catalog() });

  const addCanvasAssetToChat = (asset: ChatAssetContext) => {
    setChatAssetContext(asset);
    setRightPanel('chat');
  };

  const editPromptFromHistory = (prompt: string) => {
    setQuickPrompt(prompt);
    setMode('quick');
    setPanelOpen(true);
    setQuickMode(false);
    setViewMode('canvas');
  };

    useEffect(() => {
    const st = (window as any).__reactRouterState || history.state?.usr || {};
    if (st.images) setImages(st.images);
    if (st.result) {
      setResult(st.result);
      if (st.brief) setBrief(st.brief);
    }
    if (st.promptTemplate) {
      setPromptTemplate(st.promptTemplate);
    }
    // Brief 页(图四)带入:始终预填 prompt;全自动模式才自动生成
    if (st.prompt) {
      setQuickPrompt(st.prompt);
      if (st.brief) setQuickBrief(st.brief);
    }
    if (st.quickMode && st.prompt) {
      setQuickMode(true);
      setViewMode('canvas');
      setPanelOpen(false);
      setRightPanel('chat');
    }
  }, []);

  // Day 1: Auto-start quick generation when entering from + new
  const quickGenStarted = useRef(false);
  useEffect(() => {
    if (quickMode && quickPrompt.trim() && !quickGenStarted.current && !result && !isGenerating) {
      quickGenStarted.current = true;
      startQuickGen();
    }
  }, [quickMode, quickPrompt, result, isGenerating]);

  const { data: saved } = useQuery({ queryKey: ['brief', pid], queryFn: () => getProjectBrief(pid) });
  const briefLoaded = useRef(false);
  useEffect(() => { if (saved?.brief && !briefLoaded.current) { setBrief(saved.brief); briefLoaded.current = true; } }, [saved]);

  // Async generation with polling (no timeout)
  const startGen = async () => {
    setIsGenerating(true);
    setGenError(null);
    setStartTime(Date.now());
    try {
      const formData = new FormData();
      formData.append('parsed_brief_json', JSON.stringify(brief));
      formData.append('project_id', String(pid));
      formData.append('skip_review', 'true');
      if (promptTemplate) {
        formData.append('prompt_template', promptTemplate);
      }
      const { task_id } = await api.generation.generateAsync(formData);
      setGenTaskId(task_id);
      const poll = setInterval(async () => {
        try {
          const task = await api.generation.pollTask(task_id);
          if (task.status === 'complete') {
            clearInterval(poll);
            setIsGenerating(false);
            const data = task.generation;
            setResult(data);
            setGenTaskId(null);
            if (task.quality_report) setQualityReport(task.quality_report);
            // T3: 生成完成后自动切换到画布全幅展示
            setViewMode('canvas');
            setPanelOpen(false);
            try { await saveBrief(pid, brief); } catch(e) {}
          } else if (task.status === 'error') {
            clearInterval(poll);
            setIsGenerating(false);
            setGenError(task.error || '生成失败');
            setGenTaskId(null);
          }
        } catch(e) {}
      }, 3000);
    } catch(e: any) {
      setIsGenerating(false);
      setGenError(e?.message || '启动生成失败');
    }
  };

  // T5: Quick generate from prompt only
  const startQuickGen = async () => {
    if (!quickPrompt.trim()) {
      setGenError('请输入prompt');
      return;
    }
    setResult(null);
    setIsGenerating(true);
    setGenError(null);
    setStartTime(Date.now());
    setViewMode('canvas');
    setPanelOpen(false);
    try {
      const { task_id } = await api.generation.quickGenerate({
        prompt: quickPrompt,
        project_id: pid,
        prompt_template: promptTemplate || undefined,
        brief: quickBrief || undefined,
        reference_image_url: refImage?.url || undefined,  // Day 3.3
        image_provider: 'dataeyes',
        image_model: autoModel ? undefined : selectedImageModel || undefined,
        auto_model: autoModel,
      });
      setGenTaskId(task_id);
      const poll = setInterval(async () => {
        try {
          const task = await api.generation.pollTask(task_id);
          if (task.status === 'complete') {
            clearInterval(poll);
            setIsGenerating(false);
            const data = task.generation;
            setResult(data);
            setGenTaskId(null);
            // Auto-switch to full canvas view
            setViewMode('canvas');
            setPanelOpen(false);
          } else if (task.status === 'error') {
            clearInterval(poll);
            setIsGenerating(false);
            setGenError(task.error || '生成失败');
            setGenTaskId(null);
          }
        } catch(e) {}
      }, 3000);
    } catch(e: any) {
      setIsGenerating(false);
      setGenError(e?.message || '启动快速生成失败');
    }
  };

  // Day 3.3: Handle reference image drop
  const isExternalFileDrag = (e: React.DragEvent) => e.dataTransfer.types.includes('Files');

  const handleRefDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (!isExternalFileDrag(e)) return;
    const file = e.dataTransfer.files[0];
    if (!file || !file.type.startsWith('image/')) return;
    setUploadingRef(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/v1/upload/image', { method: 'POST', body: formData });
      const data = await res.json();
      setRefImage({ url: data.url, filename: data.filename });
    } catch(e) {
      console.error('Upload failed:', e);
    } finally {
      setUploadingRef(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    if (!isExternalFileDrag(e)) return;
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => setIsDragOver(false);

  const copy = async () => { try { const { markdown } = await exportMarkdown(pid); await navigator.clipboard.writeText(markdown); setCopied(true); setTimeout(()=>setCopied(false),2000); } catch(e){} };
  const ready = brief.product_name && brief.selling_points.length > 0;
  const btnClass = ready && !isGenerating ? 'bg-orange-500 hover:bg-orange-400 text-white shadow-lg shadow-orange-500/20' : 'bg-white/5 text-gray-500 cursor-not-allowed';

  // When canvas is showing, use full-width layout
  const isCanvas = viewMode === "canvas";
  const isFullCanvas = isCanvas;

  return (
    <div className="liquid-page min-h-screen">
      {/* Glass header — compact when canvas */}
      <header className={`sticky top-0 z-50 border-b border-white/5 bg-black/20 backdrop-blur-2xl flex items-center justify-between transition-all ${isFullCanvas ? 'px-4 py-2' : 'px-8 py-4'}`}>
        <div className="flex items-center gap-3">
          <ThemeToggle isLight={isLight} toggle={toggleTheme} />
          <a href="/" className="text-gray-400 hover:text-gray-200 mr-2 text-sm transition-colors">← 返回</a>
          <a href="/video-edit" className="text-xs px-3 py-1 rounded bg-purple-500/10 text-purple-400 hover:bg-purple-500/20 transition-colors border border-purple-500/20">🎬 视频编辑</a>
          {!isFullCanvas && <img src="/logo.png" alt="Logo" className="w-10 h-10 rounded-lg object-contain" />}
          {!isFullCanvas && <span className="font-semibold text-lg text-white tracking-tight">视觉 Agent</span>}
        </div>
        <div className="flex items-center gap-3">
          {result && <span className="text-xs text-gray-400">耗时 {formatElapsedSeconds(startTime, Date.now())}</span>}
          {result && <button onClick={copy} className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs text-gray-300 transition-all">{copied?'已复制':'复制 Markdown'}</button>}
          {result && (
            <button onClick={() => setViewMode(m => m === 'canvas' ? 'tabs' : 'canvas')}
              className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs text-gray-300 transition-all">
              {viewMode === 'canvas' ? '📋 标签视图' : '🎨 画布视图'}
            </button>
          )}
          {promptTemplate && (
            <span className="text-xs text-orange-400 bg-orange-500/10 px-2 py-0.5 rounded border border-orange-500/20 max-w-[200px] truncate" title={promptTemplate}>
              🎨 风格参考已加载
            </span>
          )}
        </div>
      </header>

      {showReview ? (
        <main className="max-w-6xl mx-auto px-8 py-10">
          <div className="opacity-0 animate-[fadeIn_0.5s_ease-out_forwards] translate-y-5 animate-[slideUp_0.5s_ease-out_forwards]">
            <BriefReviewPanel
              brief={brief}
              missing={missing}
              onConfirm={(updatedBrief) => {
                setBrief(updatedBrief);
                setShowReview(false);
                setMode('manual');
              }}
              onReupload={() => {
                setShowReview(false);
                setBrief(DF);
              }}
            />
          </div>
        </main>
      ) : isFullCanvas ? (
        /* ── Full-screen canvas layout ── */
        <main className="flex h-[calc(100vh-44px)] overflow-hidden">
          {/* Canvas fills remaining space */}
          <div
            className={`flex-1 overflow-hidden relative ${isDragOver ? 'ring-2 ring-purple-500 ring-inset' : ''}`}
            onDrop={handleRefDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            {/* Day 3.3: Drop zone overlay */}
            {isDragOver && (
              <div className="absolute inset-0 z-50 bg-purple-500/10 backdrop-blur-sm flex items-center justify-center pointer-events-none">
                <div className="text-center">
                  <span className="text-4xl">🖼️</span>
                  <p className="text-purple-300 text-sm mt-2 font-medium">释放以添加参考图</p>
                  <p className="text-purple-400/60 text-xs mt-1">AI 将分析风格并生成同风格素材</p>
                </div>
              </div>
            )}
            {modelPanelOpen && (
              <div className="absolute left-3 top-16 z-40 w-80">
            <ModelPreferencePanel
              isOpen={modelPanelOpen}
              onToggle={() => setModelPanelOpen(!modelPanelOpen)}
              modelsData={modelOptions}
              activeKind={activeModelKind}
              setActiveKind={setActiveModelKind}
              autoModel={autoModel}
              setAutoModel={setAutoModel}
              selectedModel={selectedImageModel}
              setSelectedModel={setSelectedImageModel}
            />
              </div>
            )}
            {/* Day 3.3: Reference image preview badge */}
            {refImage && (
              <div className="absolute top-2 right-2 z-40 bg-black/80 backdrop-blur rounded-lg border border-purple-500/30 p-2 flex items-center gap-2">
                <img src={refImage.url} alt="参考图" className="w-10 h-10 rounded object-cover" />
                <div>
                  <p className="text-xs text-purple-300 font-medium">参考风格</p>
                  <button onClick={() => setRefImage(null)} className="text-[10px] text-gray-500 hover:text-red-400 transition-colors">移除</button>
                </div>
              </div>
            )}
            {uploadingRef && (
              <div className="absolute inset-0 z-50 bg-black/50 flex items-center justify-center">
                <div className="text-center">
                  <div className="w-8 h-8 border-2 border-purple-500/20 border-t-purple-500 rounded-full animate-spin mx-auto" />
                  <p className="text-gray-400 text-xs mt-2">上传参考图...</p>
                </div>
              </div>
            )}
            {panelOpen && (
              <div data-brief-panel-overlay className="absolute left-3 top-3 bottom-3 z-50 w-[300px] overflow-y-auto rounded-2xl border border-white/10 bg-black/70 p-3 shadow-2xl backdrop-blur-xl">
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center gap-2"><span className="text-lg">📋</span><h2 className="text-base font-semibold text-white">产品资料</h2></div>
                  <button data-brief-panel-close onClick={() => setPanelOpen(false)} title="关闭产品资料" className="rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-xs text-gray-400 hover:text-white">✕</button>
                </div>
                <div className="space-y-3">
                  <div className="flex gap-1.5">
                    <button onClick={()=>setMode('quick')} className={`flex-1 py-1.5 text-[11px] rounded-lg transition-colors ${mode==='quick'?'bg-purple-600 text-white':'bg-white/5 text-gray-400 hover:text-gray-200 border border-white/10'}`}>⚡ 快速</button>
                    <button onClick={()=>setMode('manual')} className={`flex-1 py-1.5 text-[11px] rounded-lg transition-colors ${mode==='manual'?'bg-orange-500 text-white':'bg-white/5 text-gray-400 hover:text-gray-200 border border-white/10'}`}>手动</button>
                    <button onClick={()=>setMode('parse')} className={`flex-1 py-1.5 text-[11px] rounded-lg transition-colors ${mode==='parse'?'bg-blue-600 text-white':'bg-white/5 text-gray-400 hover:text-gray-200 border border-white/10'}`}>解析</button>
                    <button onClick={()=>setMode('doc')} className={`flex-1 py-1.5 text-[11px] rounded-lg transition-colors ${mode==='doc'?'bg-green-600 text-white':'bg-white/5 text-gray-400 hover:text-gray-200 border border-white/10'}`}>文档</button>
                  </div>
                  {mode==='quick' && (
                    <div className="space-y-3">
                      <textarea
                        value={quickPrompt}
                        onChange={(e) => setQuickPrompt(e.target.value)}
                        placeholder="例如：一款智能手表，心率监测，运动模式，黑色外观"
                        className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50 resize-none"
                        rows={4}
                      />
                      <ModelPreferencePanel
                        isOpen={modelPanelOpen}
                        onToggle={() => setModelPanelOpen(!modelPanelOpen)}
                        modelsData={modelOptions}
                        activeKind={activeModelKind}
                        setActiveKind={setActiveModelKind}
                        autoModel={autoModel}
                        setAutoModel={setAutoModel}
                        selectedModel={selectedImageModel}
                        setSelectedModel={setSelectedImageModel}
                      />
                      <button
                        onClick={startQuickGen}
                        disabled={!quickPrompt.trim() || isGenerating}
                        className={`w-full py-2.5 rounded-xl font-semibold text-sm transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed ${quickPrompt.trim() && !isGenerating ? 'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-600/20' : 'bg-white/5 text-gray-500 cursor-not-allowed'}`}
                      >
                        {isGenerating ? '快速生成中...' : '⚡ 快速生成'}
                      </button>
                    </div>
                  )}
                  {mode==='parse' && <BriefParsePanel onParsed={(p,m)=>{setBrief(p);setMissing(m);setShowReview(true);}} />}
                  {mode==='doc' && <DocumentUploader onParsed={(p,m,_preview)=>{setBrief(p);setMissing(m);setShowReview(true);}} />}
                  <MissingFieldsAlert fields={missing} onDismiss={()=>setMissing([])} />
                  {mode === 'manual' && <BriefForm value={brief} onChange={setBrief} />}
                  {mode === 'manual' && <ImageUploader images={uploadedImages} onChange={setUploadedImages} />}
                  {mode === 'manual' && (
                    <button onClick={startGen} disabled={!ready||isGenerating} className={`w-full py-2.5 rounded-xl font-semibold text-sm transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed ${btnClass}`}>
                      {isGenerating ? '并行生成中...' : '一键生成六类素材'}
                    </button>
                  )}
                  {genError && <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">{genError}</div>}
                </div>
              </div>
            )}
            <div className="absolute right-3 top-3 z-50 flex gap-2">
              <button data-right-panel-trigger="chat" onClick={() => setRightPanel(rightPanel === 'chat' ? null : 'chat')} title="打开AI对话" className={`rounded-xl border px-3 py-2 text-xs shadow-lg backdrop-blur transition-all ${rightPanel === 'chat' ? 'border-purple-400 bg-purple-500/15 text-purple-300' : 'border-gray-200 bg-white/90 text-gray-700 hover:bg-white'}`}>💬 AI</button>
              <button data-right-panel-trigger="library" onClick={() => setRightPanel(rightPanel === 'library' ? null : 'library')} title="打开资料库" className={`rounded-xl border px-3 py-2 text-xs shadow-lg backdrop-blur transition-all ${rightPanel === 'library' ? 'border-orange-400 bg-orange-500/15 text-orange-300' : 'border-gray-200 bg-white/90 text-gray-700 hover:bg-white'}`}>🎨 资料库</button>
            </div>
            {rightPanel && (
              <div data-right-panel-overlay className="absolute right-0 top-0 bottom-0 z-50 w-[399px] bg-white shadow-2xl border-l border-gray-200 flex flex-col">
                <div className="flex items-center justify-between border-b border-gray-200 px-4 py-2">
                  <div className="flex gap-2">
                    <button onClick={() => setRightPanel('chat')} className={`rounded-lg px-3 py-1.5 text-xs ${rightPanel === 'chat' ? 'bg-purple-50 text-purple-600' : 'text-gray-500 hover:bg-gray-50'}`}>💬 AI对话</button>
                    <button onClick={() => setRightPanel('library')} className={`rounded-lg px-3 py-1.5 text-xs ${rightPanel === 'library' ? 'bg-orange-50 text-orange-600' : 'text-gray-500 hover:bg-gray-50'}`}>🎨 资料库</button>
                  </div>
                  <button data-right-panel-close onClick={() => setRightPanel(null)} title="关闭右侧面板" className="rounded-lg border border-gray-200 bg-white px-2 py-1 text-xs text-gray-500 hover:text-gray-900">✕</button>
                </div>
                {rightPanel === 'chat' && (
                  <div className="flex-1 overflow-hidden">
                    <AIChatPanel
                      taskId={genTaskId}
                      isLight={isLight}
                      projectName={brief.product_name || '未命名'}
                      projectId={pid}
                      chatAssetContext={chatAssetContext}
                      onTaskStarted={(taskId) => {
                        setGenTaskId(taskId);
                        setIsGenerating(true);
                        setGenError(null);
                      }}
                      onGenerationComplete={(generation) => {
                        setResult(generation as VisualAssetPlan);
                        setCanvasRefreshNonce(n => n + 1);
                        setGenTaskId(null);
                        setIsGenerating(false);
                        setViewMode('canvas');
                        setPanelOpen(false);
                      }}
                      skillPromptSelected={pendingSkillPrompt}
                      onSkillPromptConsumed={() => setPendingSkillPrompt(null)}
                    />
                  </div>
                )}
                {rightPanel === 'library' && (
                  <div className="flex-1 overflow-auto">
                    <LibraryPanel
                      projectId={Number(pid)}
                      hasUploadedPdf={false}
                      onClose={() => setRightPanel(null)}
                    />
                  </div>
                )}
              </div>
            )}
            {(quickMode || isGenerating) && !result ? (
            <div className="relative w-full h-full">
              <CanvasView
                isLight={isLight}
                projectId={pid}
                canvasRefreshNonce={canvasRefreshNonce}
                generationTaskId={genTaskId}
                qualityReport={qualityReport}
                onAddToChat={addCanvasAssetToChat}
                onEditPrompt={editPromptFromHistory}
              />
              {/* B 联动:生成中在画布上浮层展示具名子 Agent 状态流 */}
              {isGenerating && (
                <div className="pointer-events-none absolute left-1/2 top-6 z-30 w-[min(92%,32rem)] -translate-x-1/2">
                  <AgentProgress active={isGenerating} />
                </div>
              )}
            </div>
          ) : isGenerating && !result ? (
              <div className="h-full flex flex-col items-center justify-center gap-4">
                <div className="relative">
                  <div className="w-16 h-16 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl">⚡</span>
                  </div>
                </div>
                <div className="text-center space-y-2">
                  <p className="text-gray-300 text-sm font-medium">AI 正在生成中...</p>
                  <p className="text-gray-500 text-xs">{quickPrompt?.slice(0, 40) || "处理中"}</p>
                </div>
                <div className="flex gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style={{animationDelay:"0ms"}} />
                  <div className="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style={{animationDelay:"150ms"}} />
                  <div className="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style={{animationDelay:"300ms"}} />
                </div>
              </div>
            ) : (
            <CanvasView
              isLight={isLight}
              mainImage={result?.main_image}
              whiteBg={result?.white_bg}
              sceneImages={result?.scene_images}
              sellingPoints={result?.selling_points}
              videoScripts={result?.video_scripts}
              projectId={pid}
              canvasRefreshNonce={canvasRefreshNonce}
              generationTaskId={genTaskId}
              qualityReport={qualityReport}
              onAddToChat={addCanvasAssetToChat}
              onEditPrompt={editPromptFromHistory}
              adMaterial={result?.ad_material}
              brief={brief}
            />
            )}
          </div>
        </main>
      ) : (
        /* ── Normal layout (form + canvas/tabs side by side) ── */
        <main className={`${result ? 'max-w-full' : 'max-w-7xl'} mx-auto px-8 py-10`}>
          {/* Platform/scene bar — hide when canvas but panel open */}
          {!isCanvas && (
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/5">
              <span className="text-xs text-gray-500">平台:</span>
              {['taobao','douyin','jd','xiaohongshu'].map(p => (
                <button key={p} className="px-2 py-0.5 text-xs rounded border border-white/10 text-gray-400 hover:text-white hover:border-white/20 transition-colors">{p}</button>
              ))}
              <span className="text-xs text-gray-700 mx-2">|</span>
              <span className="text-xs text-gray-500">场景:</span>
              {['电商主图','详情页','直播间','短视频'].map(s => (
                <button key={s} className="px-2 py-0.5 text-xs rounded border border-white/10 text-gray-400 hover:text-white hover:border-white/20 transition-colors">{s}</button>
              ))}
            </div>
          )}

          <div className={`grid gap-6 transition-all duration-300 ${isCanvas ? 'grid-cols-[1fr]' : 'grid-cols-[420px_1fr]'}`}>
            {/* Left: input area */}
            <div className="space-y-4">
              <div className="liquid-card p-4">
                <div className="flex items-center gap-2 mb-3"><span className="text-lg">📋</span><h2 className="text-base font-semibold text-white">产品资料</h2></div>
                <div className="flex gap-1.5">
                  <button onClick={()=>setMode('quick')} className={`flex-1 py-1.5 text-[11px] rounded-lg transition-colors ${mode==='quick'?'bg-purple-600 text-white':'bg-white/5 text-gray-400 hover:text-gray-200 border border-white/10'}`}>⚡ 快速</button>
                  <button onClick={()=>setMode('manual')} className={`flex-1 py-1.5 text-[11px] rounded-lg transition-colors ${mode==='manual'?'bg-orange-500 text-white':'bg-white/5 text-gray-400 hover:text-gray-200 border border-white/10'}`}>手动填写</button>
                  <button onClick={()=>setMode('parse')} className={`flex-1 py-1.5 text-[11px] rounded-lg transition-colors ${mode==='parse'?'bg-blue-600 text-white':'bg-white/5 text-gray-400 hover:text-gray-200 border border-white/10'}`}>智能解析</button>
                  <button onClick={()=>setMode('doc')} className={`flex-1 py-1.5 text-[11px] rounded-lg transition-colors ${mode==='doc'?'bg-green-600 text-white':'bg-white/5 text-gray-400 hover:text-gray-200 border border-white/10'}`}>上传文档</button>
                </div>
              </div>
              {mode==='quick' && (
                <div className="liquid-card p-4 space-y-3">
                  <div>
                    <label className="block text-xs text-gray-400 mb-2">输入 prompt，直接生成画布</label>
                    <textarea
                      value={quickPrompt}
                      onChange={(e) => setQuickPrompt(e.target.value)}
                      placeholder="例如：一款智能手表，心率监测，运动模式，黑色外观"
                      className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50 resize-none"
                      rows={4}
                    />
                  </div>
                  <ModelPreferencePanel
                    isOpen={modelPanelOpen}
                    onToggle={() => setModelPanelOpen(!modelPanelOpen)}
                    modelsData={modelOptions}
                    activeKind={activeModelKind}
                    setActiveKind={setActiveModelKind}
                    autoModel={autoModel}
                    setAutoModel={setAutoModel}
                    selectedModel={selectedImageModel}
                    setSelectedModel={setSelectedImageModel}
                  />
                  <button
                    onClick={startQuickGen}
                    disabled={!quickPrompt.trim() || isGenerating}
                    className={`w-full py-3 rounded-xl font-semibold text-sm transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed ${
                      quickPrompt.trim() && !isGenerating
                        ? 'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-600/20'
                        : 'bg-white/5 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    {isGenerating
                      ? <span className="flex items-center justify-center gap-2"><svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>快速生成中...</span>
                      : '⚡ 快速生成'}
                  </button>
                  <p className="text-[10px] text-gray-500 text-center">跳过解析和字段填写，2步直达画布</p>
                </div>
              )}
              {mode==='parse' && <BriefParsePanel onParsed={(p,m)=>{setBrief(p);setMissing(m);setShowReview(true);}} />}
              {mode==='doc' && <DocumentUploader onParsed={(p,m,_preview)=>{setBrief(p);setMissing(m);setShowReview(true);}} />}
              <MissingFieldsAlert fields={missing} onDismiss={()=>setMissing([])} />
              {mode === 'manual' && <div className="liquid-card p-4"><BriefForm value={brief} onChange={setBrief} /></div>}
              {mode === 'manual' && <ImageUploader images={uploadedImages} onChange={setUploadedImages} />}
              {mode === 'manual' && (
                <button onClick={startGen} disabled={!ready||isGenerating} className={`w-full py-3 rounded-xl font-semibold text-sm transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed ${btnClass}`}>
                  {isGenerating
                    ? <span className="flex items-center justify-center gap-2"><svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>并行生成中...</span>
                    : '一键生成六类素材'}
                </button>
              )}
              {genError && <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">{genError}</div>}
            </div>

            {/* Right: results */}
            {isCanvas ? (
              <div className="h-[calc(100vh-180px)] overflow-hidden rounded-xl border border-white/5">
                <CanvasView
                  mainImage={result?.main_image}
                  isLight={isLight}
                  whiteBg={result?.white_bg}
                  sceneImages={result?.scene_images}
                  sellingPoints={result?.selling_points}
                  videoScripts={result?.video_scripts}
                  projectId={pid}
                  canvasRefreshNonce={canvasRefreshNonce}
                  onAddToChat={addCanvasAssetToChat}
                  onEditPrompt={editPromptFromHistory}
                  adMaterial={result?.ad_material}
                  brief={brief}
                />
              </div>
            ) : (
              <div className="liquid-card p-6 min-h-[600px]">
                {result ? (
                  <ResultTabs plan={result} images={images} productName={brief.product_name} projectId={parseInt(pid, 10)} uploadedProductUrl={uploadedImages?.[0]?.url} />
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-gray-500">
                    <div className="text-5xl mb-5">✨</div>
                    <p className="text-lg mb-2">准备好开始了吗？</p>
                    <p className="text-sm">填写左侧产品资料，点击生成按钮</p>
                  </div>
                )}
              </div>
            )}

            {result && !isCanvas && <CopywritingPanel brief={brief} />}
          </div>
        </main>
      )}

</div>
  );
}
