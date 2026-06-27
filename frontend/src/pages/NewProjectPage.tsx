import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { toast } from '../components/Toast';

const EXAMPLE_BRIEFS = [
  '我要上架一款 299 元的女士防晒衣，主打轻薄、防晒、通勤户外都能穿，风格清爽高级，帮我做一套淘宝和小红书的上新素材。',
  '我是一家深圳日式拉面店，周末要做第二碗半价活动，想要小红书、朋友圈和门店立牌。',
  '我要做一个国产香氛品牌，目标用户是 25-35 岁女性，调性是东方、松弛、高级。',
];

const SUB_AGENTS = ['PM', 'Research', 'Brand', 'Copy', 'Visual', 'Image', 'Layout', 'Mockup', 'Compliance', 'Export'];

interface Scene { id: string; name: string; icon: string; desc: string; platforms: string[] }

export default function NewProjectPage() {
  const navigate = useNavigate();
  const [text, setText] = useState('');
  const [scene, setScene] = useState('');
  const [platforms, setPlatforms] = useState<string[]>([]);
  const [mode, setMode] = useState<'auto' | 'director'>('auto');
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [platformList, setPlatformList] = useState<Array<{ id: string; name: string }>>([]);
  const [files, setFiles] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    api.platform.scenes().then((d: { scenes?: Scene[] }) => setScenes(d.scenes || [])).catch(() => {});
    api.platform.list().then((d: { platforms?: string[]; specs?: Record<string, { name?: string }> }) => {
      const ids = d.platforms || [];
      const specs = d.specs || {};
      setPlatformList(ids.map((id) => ({ id, name: specs[id]?.name || id })));
    }).catch(() => {});
  }, []);

  const togglePlatform = (id: string) => setPlatforms((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]));

  const onUpload = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.ppt,.pptx,.doc,.docx,.txt,.md,image/*';
    input.onchange = async () => {
      const f = input.files?.[0];
      if (!f) return;
      setUploading(true);
      const fd = new FormData();
      fd.append('file', f);
      try {
        const data = await api.upload.documentParse(fd) as Record<string, string>;
        const parsed = data.parsed_text || data.text || data.content || '';
        if (parsed) setText((t) => (t ? t + '\n\n' : '') + parsed);
        setFiles((x) => [...x, f.name]);
        toast('已解析参考资料：' + f.name);
      } catch {
        toast('上传失败，请重试');
      } finally {
        setUploading(false);
      }
    };
    input.click();
  };

  const onParse = async () => {
    if (!text.trim()) { toast('请输入产品描述'); return; }
    setLoading(true);
    try {
      const sceneName = scenes.find((s) => s.id === scene)?.name || '通用';
      const project = await api.projects.create(text.trim().slice(0, 20) || sceneName, text.trim().slice(0, 200));
      const brief = { description: text.trim(), scene, scene_name: sceneName, platforms, mode };
      // B 联动:跳进无限画布。全自动→quickMode 自动生成;协作导演→落地画布由用户触发
      navigate(`/generate/${project.id}`, { state: { quickMode: mode === 'auto', prompt: text.trim(), brief } });
    } catch {
      toast('创建项目失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="liquid-page min-h-screen px-6 py-6 text-white">
      <div className="mx-auto w-full max-w-6xl">
        {/* 顶部 */}
        <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <button onClick={() => navigate('/')} className="mt-0.5 rounded-lg border border-white/[0.12] bg-white/[0.04] px-3 py-1.5 text-xs text-gray-300 transition-colors hover:text-white">← 返回</button>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">新建项目</h1>
              <p className="mt-0.5 text-sm text-gray-400">描述你的产品与目标，MOYAG Agent 自动拆解任务</p>
            </div>
          </div>
          <button onClick={onParse} disabled={loading} className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-orange-500 to-rose-500 px-4 py-2 text-sm font-semibold text-white transition-transform hover:scale-[1.03] disabled:opacity-50">
            ✦ {loading ? '解析中…' : '解析 Brief'} {!loading && '→'}
          </button>
        </div>

        <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
          {/* 左 */}
          <div className="space-y-5">
            {/* 产品描述 */}
            <div className="rounded-3xl border border-white/[0.12] bg-white/[0.04] p-5">
              <div className="mb-2 flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm font-semibold"><span className="text-orange-300">📄</span> 产品描述</span>
                <div className="flex gap-1">
                  {EXAMPLE_BRIEFS.map((b, i) => (
                    <button key={i} onClick={() => setText(b)} className="rounded-md px-2 py-1 text-xs text-gray-400 transition-colors hover:bg-white/[0.06] hover:text-white">示例 {i + 1}</button>
                  ))}
                </div>
              </div>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="例如：我要上架一款 299 元的女士防晒衣，主打轻薄、防晒、通勤户外都能穿，风格清爽高级…"
                className="min-h-[150px] w-full resize-y rounded-xl border border-white/[0.1] bg-white/[0.04] px-3 py-2.5 text-sm text-white placeholder:text-gray-600 outline-none transition-colors focus:border-orange-400/40"
              />
              <div className="mt-3 flex items-center justify-between">
                <button onClick={onUpload} disabled={uploading} className="inline-flex items-center gap-1.5 rounded-lg border border-white/[0.12] bg-white/[0.04] px-3 py-1.5 text-xs text-gray-300 transition-colors hover:text-white disabled:opacity-50">
                  ⬆ {uploading ? '解析中…' : '上传参考资料'}
                </button>
                <span className="text-xs text-gray-500">支持 PDF / PPT / Word / 图片</span>
              </div>
              {files.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {files.map((f, i) => <span key={i} className="rounded-full bg-white/[0.06] px-2 py-0.5 text-[11px] text-gray-400">📎 {f}</span>)}
                </div>
              )}
            </div>

            {/* 场景模板 */}
            <div>
              <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold"><span className="text-orange-300">✦</span> 选择场景模板</h3>
              <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
                {scenes.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => { const next = s.id === scene ? '' : s.id; setScene(next); if (next && platforms.length === 0) setPlatforms(s.platforms || []); }}
                    className={'rounded-2xl border p-3 text-left transition-all ' + (scene === s.id ? 'border-orange-400/50 bg-orange-500/[0.1]' : 'border-white/[0.1] bg-white/[0.03] hover:border-white/20')}
                  >
                    <div className="mb-1 flex items-center gap-2"><span className="text-base">{s.icon}</span><span className="text-sm font-semibold text-white">{s.name}</span></div>
                    <p className="line-clamp-2 text-[11px] leading-4 text-gray-500">{s.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* 平台 */}
            <div>
              <h3 className="mb-3 text-sm font-semibold">目标平台（可多选）</h3>
              <div className="flex flex-wrap gap-2">
                {platformList.map((p) => {
                  const active = platforms.includes(p.id);
                  return (
                    <button key={p.id} onClick={() => togglePlatform(p.id)} className={'rounded-full border px-3 py-1.5 text-sm transition-all ' + (active ? 'border-orange-400/50 bg-orange-500/[0.12] text-orange-200' : 'border-white/[0.12] text-gray-400 hover:text-white')}>
                      {p.name}
                    </button>
                  );
                })}
              </div>
              {platforms.length > 0 && <p className="mt-2 text-xs text-gray-500">已选 {platforms.length} 个平台，将自动适配尺寸与规范</p>}
            </div>
          </div>

          {/* 右侧栏 */}
          <div className="h-fit space-y-5 rounded-3xl border border-white/[0.12] bg-white/[0.04] p-5">
            <div>
              <h3 className="mb-3 text-sm font-semibold">Agent 自主程度</h3>
              <div className="space-y-2">
                {[{ k: 'auto', t: '全自动模式', d: 'Agent 自动完成全流程，中间不打断' }, { k: 'director', t: '协作导演模式', d: '落地画布,每个关键阶段由你确认后再继续' }].map((m) => (
                  <button key={m.k} onClick={() => setMode(m.k as 'auto' | 'director')} className={'w-full rounded-xl border p-3 text-left transition-all ' + (mode === m.k ? 'border-orange-400/50 bg-orange-500/[0.1]' : 'border-white/[0.1] hover:border-white/20')}>
                    <div className="text-sm font-semibold text-white">{m.t}</div>
                    <div className="mt-0.5 text-xs text-gray-500">{m.d}</div>
                  </button>
                ))}
              </div>
            </div>
            <div>
              <h3 className="mb-3 text-sm font-semibold">本次将调用</h3>
              <div className="flex flex-wrap gap-1.5">
                {SUB_AGENTS.map((a) => <span key={a} className="rounded-full bg-white/[0.06] px-2 py-0.5 text-[11px] text-gray-300">{a}</span>)}
              </div>
              <p className="mt-2 text-xs text-gray-500">10 个子 Agent 协作完成你的项目</p>
            </div>
            <div className="rounded-xl border border-orange-400/15 bg-orange-500/[0.06] p-3 text-xs leading-relaxed text-gray-400">
              <strong className="text-orange-200">提示</strong>：信息越完整，生成质量越高。Agent 会在下一步追问 1-3 个关键问题，你也可以直接「先帮我生成一版」。
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
