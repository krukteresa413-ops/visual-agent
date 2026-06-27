import { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { toast } from '../components/Toast';
import { videoEdit } from '../api/client';

const PIPELINE = [
  { step: 1, label: '上传素材', icon: '📤' },
  { step: 2, label: '素材扫描', icon: '🔍' },
  { step: 3, label: 'AI 分析', icon: '✦' },
  { step: 4, label: '脚本生成', icon: '📝' },
  { step: 5, label: '剪辑蓝图', icon: '📋' },
  { step: 6, label: '预览渲染', icon: '🎬' },
];

export default function VideoEditPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [projectName, setProjectName] = useState('');
  const [showCreate, setShowCreate] = useState(true);
  const [loading, setLoading] = useState(false);
  const [projectId, setProjectId] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [scanResult, setScanResult] = useState<any>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [scriptResult, setScriptResult] = useState<any>(null);
  const [blueprintResult, setBlueprintResult] = useState<any>(null);
  const [timeline, setTimeline] = useState<any>(null);
  const [renderResult, setRenderResult] = useState<any>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const createProject = async () => {
    if (!projectName.trim()) { toast('请输入项目名称'); return; }
    setLoading(true);
    try {
      const resp = await videoEdit.createProject(projectName);
      setProjectId(resp.data.id);
      setShowCreate(false); setCurrentStep(1);
      toast('项目已创建');
    } catch { toast('创建失败'); }
    finally { setLoading(false); }
  };

  const handleFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    setUploadedFiles(prev => [...prev, ...files]);
  };

  const removeFile = (idx: number) => setUploadedFiles(prev => prev.filter((_, i) => i !== idx));

  const doUpload = async () => {
    if (uploadedFiles.length === 0) { toast('请选择文件'); return; }
    setLoading(true);
    try {
      await videoEdit.uploadFiles(projectId, uploadedFiles);
      toast('上传完成'); setCurrentStep(2); doScan();
    } catch { toast('上传失败'); setLoading(false); }
  };

  const doScan = async () => {
    setLoading(true); setCurrentStep(2);
    try { const r = await videoEdit.scanMedia(projectId); setScanResult(r.data); } catch { toast('扫描失败'); }
    setLoading(false);
  };

  const doAnalyze = async () => {
    setLoading(true); setCurrentStep(3);
    try { const r = await videoEdit.analyzeMedia(projectId); setAnalysisResult(r.data); } catch { toast('AI 分析失败'); }
    setLoading(false);
  };

  const doScript = async () => {
    setLoading(true); setCurrentStep(4);
    try { const r = await videoEdit.generateScript(projectId, projectName); setScriptResult(r.data); } catch { toast('脚本生成失败'); }
    setLoading(false);
  };

  const doBlueprint = async () => {
    setLoading(true); setCurrentStep(5);
    try { const r = await videoEdit.generateBlueprint(projectId); setBlueprintResult(r.data); loadTimeline(); } catch { toast('蓝图生成失败'); }
    setLoading(false);
  };

  const loadTimeline = async () => {
    try { const r = await videoEdit.getTimeline(projectId); setTimeline(r.data); } catch {}
  };

  const doRender = async () => {
    setLoading(true);
    try {
      const r = await videoEdit.renderVideo(projectId);
      setRenderResult(r.data);
      loadTimeline();
      toast('渲染完成！');
    } catch { toast('渲染失败'); }
    setLoading(false);
  };

  const Spinner = () => (
    <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-10 text-center space-y-3">
      <div className="animate-spin w-8 h-8 border-2 border-orange-500/30 border-t-orange-500 rounded-full mx-auto" />
      <p className="text-gray-500 text-sm">处理中...</p>
    </div>
  );

  return (
    <div className="liquid-page min-h-screen text-gray-100">
      <header className="sticky top-0 z-10 px-6 py-2 flex items-center justify-between bg-white/5 backdrop-blur border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <Link to="/" className="text-gray-500 hover:text-white transition-colors text-sm">← 返回</Link>
          <span className="text-white/20">|</span>
          <span className="text-sm font-medium">✂️ AI 视频剪辑</span>
        </div>
        <span className="text-xs text-gray-600">{projectName || '未命名'}</span>
      </header>
      <main className="max-w-5xl mx-auto px-4 py-8">
        {!showCreate && (
          <div className="flex items-center justify-center gap-1 sm:gap-1.5 mb-8 flex-wrap">
            {PIPELINE.map((p, i) => (
              <div key={p.step} className="flex items-center gap-1 sm:gap-1.5">
                <div className={`flex items-center gap-1 px-2 py-1 sm:px-2.5 sm:py-1.5 rounded-lg text-xs font-medium transition-all ${
                  p.step === currentStep ? 'bg-orange-500/20 border border-orange-500/40 text-orange-300' :
                  p.step < currentStep ? 'bg-green-500/10 border border-green-500/30 text-green-400/80' :
                  'bg-white/[0.03] border border-white/[0.06] text-gray-600'
                }`}>
                  <span className="text-sm">{p.step < currentStep ? '✓' : p.icon}</span>
                  <span className="hidden sm:inline">{p.label}</span>
                </div>
                {i < 5 && <span className="text-gray-800 text-xs">→</span>}
              </div>
            ))}
          </div>
        )}

        {/* Create */}
        {showCreate && (
          <div className="min-h-[60vh] flex items-center justify-center">
            <div className="backdrop-blur-2xl bg-white/[0.04] border border-white/[0.1] rounded-2xl p-8 max-w-md w-full space-y-5">
              <div className="text-center">
                <span className="text-5xl">✂️</span>
                <h2 className="text-lg font-semibold mt-3 text-white">新建视频剪辑项目</h2>
                <p className="text-sm text-gray-500 mt-1">AI 自动分析素材、创作脚本、生成剪辑方案</p>
              </div>
              <input autoFocus className="w-full bg-white/[0.06] border border-white/[0.12] rounded-xl px-4 py-3 text-sm text-gray-100 placeholder-gray-600 focus:border-orange-500/40 focus:ring-2 focus:ring-orange-500/20 transition-all outline-none"
                placeholder="项目名称" value={projectName} onChange={e => setProjectName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && createProject()} />
              <button onClick={createProject} disabled={loading || !projectName.trim()}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-orange-500 to-rose-500 text-white font-medium text-sm hover:shadow-[0_0_30px_rgba(251,146,60,0.3)] transition-all duration-300 disabled:opacity-40">
                {loading ? '创建中...' : '创建项目'}
              </button>
            <button onClick={async () => { setLoading(true); try { const r = await videoEdit.createDemo(); setProjectId(r.projectId); setShowCreate(false); setCurrentStep(1); toast("已加载范例素材"); } catch { toast("加载范例失败"); } finally { setLoading(false); } }} className="w-full py-2.5 rounded-xl border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 text-sm hover:bg-cyan-500/20 transition-all mt-2">🎬 使用内置范例</button>
            </div>
          </div>
        )}

        {/* Step 1: Upload */}
        {!showCreate && currentStep === 1 && (
          <div className="animate-fadeIn space-y-6">
            <div className="backdrop-blur-xl bg-white/[0.03] border border-white/[0.08] rounded-2xl p-8 text-center">
              <span className="text-5xl mb-4 block">📤</span>
              <h2 className="text-xl font-semibold text-white">上传素材</h2>
              <p className="text-gray-500 mt-2 text-sm">支持视频、图片、音频文件</p>
              <div className="mt-6">
                <input ref={fileRef} type="file" multiple className="hidden" accept="video/*,image/*,audio/*" onChange={handleFiles} />
                <button onClick={() => fileRef.current?.click()} className="px-6 py-3 rounded-xl bg-white/[0.06] border border-dashed border-white/[0.2] text-gray-400 hover:text-white hover:border-orange-500/40 hover:bg-orange-500/5 transition-all text-sm">📁 选择文件</button>
              </div>
              {uploadedFiles.length > 0 && (
                <div className="mt-4 space-y-2 max-w-md mx-auto text-left">
                  {uploadedFiles.map((f, i) => (
                    <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-white/[0.03] border border-white/[0.05]">
                      <span className="text-xs text-gray-300 truncate">{f.name}</span>
                      <button onClick={() => removeFile(i)} className="text-gray-600 hover:text-red-400 text-xs ml-2">✕</button>
                    </div>
                  ))}
                </div>
              )}
              {uploadedFiles.length > 0 && (
                <div className="flex justify-center mt-4 gap-3">
                  <button onClick={doUpload} disabled={loading}
                    className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-rose-500 text-white font-medium text-sm hover:shadow-[0_0_30px_rgba(251,146,60,0.3)] transition-all disabled:opacity-40">
                    {loading ? '上传中...' : '上传并开始扫描 →'}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 2: Scan */}
        {!showCreate && currentStep === 2 && (
          <div className="animate-fadeIn space-y-6">
            <div className="backdrop-blur-xl bg-white/[0.03] border border-white/[0.08] rounded-2xl p-8">
              <h2 className="text-lg font-semibold text-white mb-2">🔍 素材扫描</h2>
              {loading ? <Spinner /> : scanResult ? (
                <div>
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    {(['video', 'audio', 'image'] as const).map(t => (
                      <div key={t} className="bg-white/[0.03] rounded-xl p-4 text-center border border-white/[0.06]">
                        <div className="text-2xl font-bold text-white">{scanResult.by_type?.[t] || 0}</div>
                        <div className="text-xs text-gray-500 mt-1">{t==='video'?'视频':t==='audio'?'音频':'图片'}</div>
                      </div>
                    ))}
                  </div>
                  <div className="space-y-2">
                    {scanResult.files?.slice(0, 10).map((f: any, i: number) => {
                      const dur = f.probe?.format?.duration;
                      const res = f.probe?.streams?.[0];
                      return (
                        <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-white/[0.02] border border-white/[0.04] text-xs">
                          <span>{f.media_type==='video'?'🎬':f.media_type==='audio'?'🎵':'🖼'}</span>
                          <span className="text-gray-300 truncate flex-1">{f.filename}</span>
                          {dur && <span className="text-gray-500">{Number(dur).toFixed(1)}s</span>}
                          {res?.width && <span className="text-gray-600">{res.width}×{res.height}</span>}
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex justify-end mt-4 gap-3">
                    <button onClick={() => setCurrentStep(1)} className="px-4 py-2 text-sm text-gray-500 hover:text-white transition-colors">上一步</button>
                    <button onClick={doAnalyze} className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-rose-500 text-white font-medium text-sm hover:shadow-[0_0_30px_rgba(251,146,60,0.3)] transition-all">AI 分析 →</button>
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-500 py-10">
                  <button onClick={doScan} className="px-5 py-2.5 rounded-xl bg-orange-500/20 border border-orange-500/40 text-orange-300 text-sm hover:bg-orange-500/30 transition-all">开始扫描</button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 3: Analyze */}
        {!showCreate && currentStep === 3 && (
          <div className="animate-fadeIn space-y-6">
            <div className="backdrop-blur-xl bg-white/[0.03] border border-white/[0.08] rounded-2xl p-8">
              <h2 className="text-lg font-semibold text-white mb-2">AI 素材分析</h2>
              {loading ? <Spinner /> : analysisResult ? (
                <div>
                  <div className="bg-white/[0.03] rounded-xl p-4 border border-white/[0.06] space-y-3 text-sm">
                    <div><span className="text-gray-500">概览：</span><p className="text-white mt-1">{analysisResult.overview}</p></div>
                    {analysisResult.strongest && (
                      <div><span className="text-orange-400">亮点：</span>
                        <ul className="list-disc list-inside text-gray-300 mt-1 space-y-1">
                          {(Array.isArray(analysisResult.strongest) ? analysisResult.strongest : []).map((s: any, i: number) => (
                            <li key={i}>{typeof s === 'string' ? s : s.reason || s.filename}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {analysisResult.risks && (
                      <div><span className="text-red-400">风险：</span>
                        <ul className="list-disc list-inside text-gray-300 mt-1">
                          {(Array.isArray(analysisResult.risks) ? analysisResult.risks : []).slice(0, 3).map((r: string, i: number) => (
                            <li key={i}>{r}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                  <div className="flex justify-end mt-4 gap-3">
                    <button onClick={() => setCurrentStep(2)} className="px-4 py-2 text-sm text-gray-500 hover:text-white transition-colors">上一步</button>
                    <button onClick={doScript} className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-rose-500 text-white font-medium text-sm hover:shadow-[0_0_30px_rgba(251,146,60,0.3)] transition-all">生成脚本 →</button>
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-500 py-10">
                  <button onClick={doAnalyze} className="px-5 py-2.5 rounded-xl bg-orange-500/20 border border-orange-500/40 text-orange-300 text-sm hover:bg-orange-500/30 transition-all">开始 AI 分析</button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 4: Script */}
        {!showCreate && currentStep === 4 && (
          <div className="animate-fadeIn space-y-6">
            <div className="backdrop-blur-xl bg-white/[0.03] border border-white/[0.08] rounded-2xl p-8">
              <h2 className="text-lg font-semibold text-white mb-2">📝 AI 脚本</h2>
              {loading ? <Spinner /> : scriptResult ? (
                <div>
                  <div className="bg-gradient-to-r from-orange-500/10 to-transparent rounded-xl p-4 mb-4">
                    <p className="text-sm text-gray-400">核心理念</p>
                    <p className="text-white text-lg mt-1">{scriptResult.core_idea}</p>
                  </div>
                  {scriptResult.structures?.map((s: any, i: number) => (
                    <div key={i} className={`mb-3 p-4 rounded-xl border ${i===scriptResult.recommended?'border-orange-500/30 bg-orange-500/5':'border-white/[0.06] bg-white/[0.02]'}`}>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-bold text-white">结构 {i+1}</span>
                        <span className="text-sm text-gray-300">{s.name}</span>
                        {i===scriptResult.recommended && <span className="text-xs px-1.5 py-0.5 rounded bg-orange-500/30 text-orange-300">推荐</span>}
                      </div>
                      <p className="text-xs text-gray-500 mb-2">{s.hook}</p>
                      <div className="space-y-1">
                        {(s.scenes||[]).map((sc:any,j:number)=>(
                          <div key={j} className="flex gap-2 text-xs"><span className="text-gray-600 w-5">{j+1}.</span><span className="text-gray-400">{typeof sc==='string'?sc:sc.description||sc.purpose}</span></div>
                        ))}
                      </div>
                    </div>
                  ))}
                  {Array.isArray(scriptResult.titles) && scriptResult.titles.length > 0 && (
                    <div className="mt-4 p-3 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                      <p className="text-xs text-gray-500 mb-2">标题方案</p>
                      {scriptResult.titles.slice(0,5).map((t:string,i:number)=>(<p key={i} className="text-xs text-gray-300 py-0.5">{i+1}. {t}</p>))}
                    </div>
                  )}
                  <div className="flex justify-end mt-4 gap-3">
                    <button onClick={()=>setCurrentStep(3)} className="px-4 py-2 text-sm text-gray-500 hover:text-white transition-colors">上一步</button>
                    <button onClick={doBlueprint} className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-rose-500 text-white font-medium text-sm hover:shadow-[0_0_30px_rgba(251,146,60,0.3)] transition-all">生成蓝图 →</button>
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-500 py-10">
                  <button onClick={doScript} className="px-5 py-2.5 rounded-xl bg-orange-500/20 border border-orange-500/40 text-orange-300 text-sm hover:bg-orange-500/30 transition-all">生成脚本</button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 5: Blueprint */}
        {!showCreate && currentStep === 5 && (
          <div className="animate-fadeIn space-y-6">
            <div className="backdrop-blur-xl bg-white/[0.03] border border-white/[0.08] rounded-2xl p-8">
              <h2 className="text-lg font-semibold text-white mb-2">📋 剪辑蓝图</h2>
              {loading ? <Spinner /> : blueprintResult ? (
                <div>
                  <div className="flex items-center gap-4 mb-4 text-sm">
                    <span className="text-gray-500">目标时长：<span className="text-white">{blueprintResult.project?.target_duration_seconds}s</span></span>
                    <span className="text-gray-500">镜头数：<span className="text-white">{blueprintResult.clips?.length||0}</span></span>
                  </div>
                  <div className="space-y-3">
                    {(blueprintResult.clips||[]).map((c:any,i:number)=>(
                      <div key={i} className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.04] flex gap-4 items-start">
                        <div className="w-10 h-10 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-sm font-bold text-orange-400 shrink-0">{String(i+1).padStart(2,'0')}</div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-white">{c.purpose}</p>
                          <div className="flex gap-3 mt-1 text-xs text-gray-500">
                            <span>⏱ {((c.timeline_out_seconds||0)-(c.timeline_in_seconds||0)).toFixed(1)}s</span>
                            <span>📁 {c.filename}</span>
                            <span>🎯 {Math.round((c.confidence||0)*100)}%</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-end mt-4 gap-3">
                    <button onClick={()=>setCurrentStep(4)} className="px-4 py-2 text-sm text-gray-500 hover:text-white transition-colors">上一步</button>
                    <button onClick={()=>{loadTimeline();setCurrentStep(6);}} className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-rose-500 text-white font-medium text-sm hover:shadow-[0_0_30px_rgba(251,146,60,0.3)] transition-all">预览与渲染 →</button>
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-500 py-10">
                  <button onClick={doBlueprint} className="px-5 py-2.5 rounded-xl bg-orange-500/20 border border-orange-500/40 text-orange-300 text-sm hover:bg-orange-500/30 transition-all">生成蓝图</button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 6: Preview & Render */}
        {!showCreate && currentStep === 6 && (
          <div className="animate-fadeIn space-y-6">
            <div className="backdrop-blur-xl bg-white/[0.03] border border-white/[0.08] rounded-2xl p-8">
              <h2 className="text-lg font-semibold text-white mb-2">🎬 预览与渲染</h2>

              {/* Visual Timeline */}
              {timeline && (
                <div className="mb-6">
                  <p className="text-xs text-gray-500 mb-3">时间线总览（{timeline.total_duration}s · {timeline.clip_count} 个镜头）</p>
                  <div className="relative h-16 bg-white/[0.03] rounded-xl border border-white/[0.06] overflow-hidden">
                    {timeline.clips.map((c: any, i: number) => (
                      <div key={i} className="absolute h-full flex items-center px-2 overflow-hidden hover:z-10 group cursor-default"
                        style={{ left: `${c.start_pct}%`, width: `${Math.max(c.width_pct, 2)}%` }}>
                        <div className="w-full h-10 rounded-lg bg-gradient-to-r from-orange-500/40 to-rose-500/30 border border-orange-400/20 flex items-center px-2 group-hover:from-orange-500/60 group-hover:to-rose-500/50 transition-all">
                          <span className="text-[10px] text-white font-bold truncate">{String(i+1).padStart(2,'0')} {c.duration}s</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  {/* Clip Cards */}
                  <div className="mt-3 space-y-2">
                    {timeline.clips.map((c: any, i: number) => (
                      <div key={i} className="flex items-center gap-3 p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04] text-xs">
                        <span className="w-6 h-6 rounded-md bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-orange-400 font-bold shrink-0">{i+1}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-gray-300 truncate">{c.purpose}</p>
                          <span className="text-gray-600">{c.duration}s · {c.filename}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Render */}
              {renderResult ? (
                <div className="bg-green-500/5 border border-green-500/20 rounded-xl p-6 text-center">
                  <span className="text-4xl mb-3 block">✅</span>
                  <h3 className="text-lg font-semibold text-white">渲染完成</h3>
                  <p className="text-gray-500 text-sm mt-1">时长 {renderResult.duration_seconds?.toFixed(1)}s · {renderResult.clip_count} 个镜头</p>
                  {renderResult.preview_url && (
                    <div className="mt-4">
                      <video controls className="w-full max-w-lg mx-auto rounded-xl border border-white/[0.1]"
                        src={renderResult.preview_url.startsWith('http') ? renderResult.preview_url : `/api/v1/video-edit/projects/${projectId}/video`}>
                      </video>
                    </div>
                  )}
                  <div className="flex justify-center gap-3 mt-4">
                    <a href={renderResult.preview_url?.startsWith('http') ? renderResult.preview_url : `/api/v1/video-edit/projects/${projectId}/video`}
                      download className="px-4 py-2 rounded-lg bg-white/[0.06] border border-white/[0.1] text-sm text-gray-300 hover:text-white transition-colors">
                      ⬇ 下载视频
                    </a>
                    <Link to="/" className="px-4 py-2 rounded-lg bg-gradient-to-r from-orange-500 to-rose-500 text-white text-sm hover:shadow-[0_0_30px_rgba(251,146,60,0.3)] transition-all">
                      返回首页
                    </Link>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500 text-sm mb-4">方案已就绪，点击渲染生成最终视频</p>
                  <button onClick={doRender} disabled={loading}
                    className="px-8 py-3 rounded-xl bg-gradient-to-r from-orange-500 to-rose-500 text-white font-medium hover:shadow-[0_0_30px_rgba(251,146,60,0.4)] transition-all disabled:opacity-40">
                    {loading ? '正在渲染...' : '🎬 开始渲染'}
                  </button>
                </div>
              )}
              <div className="flex justify-start mt-4">
                <button onClick={() => setCurrentStep(5)} className="px-4 py-2 text-sm text-gray-500 hover:text-white transition-colors">← 返回蓝图</button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
