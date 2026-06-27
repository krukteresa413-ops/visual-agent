import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { Project } from '../api/client';

// 与首页「项目陈列柜」保持同一套封面渐变语言
const PROJECT_COVER_GRADIENTS = [
  'from-orange-500/30 via-rose-400/14 to-white/[0.03]',
  'from-sky-400/22 via-orange-400/12 to-white/[0.03]',
  'from-emerald-400/18 via-orange-300/14 to-white/[0.03]',
  'from-violet-400/20 via-orange-400/12 to-white/[0.03]',
];

export default function ProjectsLibraryPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);

  const load = () => {
    setLoading(true);
    api.projects.list()
      .then((items) => setProjects(items))
      .catch(() => setProjects([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const openProject = (id: number) => navigate(`/generate/${id}`);

  const createProject = async () => {
    try {
      const project = await api.projects.create('未命名项目', '');
      navigate(`/generate/${project.id}`);
    } catch {
      /* 静默失败，列表仍可用 */
    }
  };

  const removeProject = async (id: number) => {
    if (!window.confirm('删除这个项目？此操作不可撤销。')) return;
    setBusyId(id);
    try {
      await api.projects.delete(id);
      setProjects((p) => p.filter((x) => x.id !== id));
    } catch {
      /* 忽略，保留原列表 */
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="min-h-[60vh] px-6 py-8 text-white">
      <div className="mx-auto w-full max-w-6xl">
        {/* 标题区 */}
        <div className="mb-6 flex items-end justify-between gap-4">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-orange-400/20 bg-orange-500/10 px-3 py-1 text-[11px] font-medium tracking-[0.18em] text-orange-200/90 uppercase">
              Project Gallery
            </div>
            <h1 className="text-2xl font-bold tracking-tight md:text-3xl">项目库</h1>
            <p className="mt-1 text-sm text-gray-400">过往项目存档，可继续编辑、复用或导出 · 以作品封面陈列</p>
          </div>
          <button
            onClick={createProject}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-gradient-to-r from-orange-500 to-rose-500 px-3 py-2 text-sm font-medium text-white transition-transform hover:scale-[1.03]"
          >
            <svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 5v14M5 12h14" />
            </svg>
            新建项目
          </button>
        </div>

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="h-56 animate-pulse rounded-3xl bg-white/[0.06]" />
            ))}
          </div>
        ) : projects.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {projects.map((project, i) => (
              <div
                key={project.id}
                className="project-gallery-card group overflow-hidden rounded-3xl border border-white/[0.12] bg-white/[0.055] transition-all duration-500 hover:-translate-y-1 hover:border-orange-400/45 hover:bg-white/[0.08] hover:shadow-[0_24px_70px_rgba(251,146,60,0.16)]"
              >
                <button onClick={() => openProject(project.id)} className="block w-full text-left">
                  <div className={`relative h-32 bg-gradient-to-br ${PROJECT_COVER_GRADIENTS[i % PROJECT_COVER_GRADIENTS.length]}`}>
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_28%_22%,rgba(255,255,255,0.28),transparent_30%),radial-gradient(circle_at_76%_70%,rgba(251,146,60,0.22),transparent_34%)]" />
                    <div className="absolute left-4 top-4 rounded-full border border-white/15 bg-black/20 px-2 py-1 text-[10px] text-white/70 backdrop-blur-md">项目封面</div>
                    <div className="absolute bottom-3 right-3 h-10 w-10 rounded-2xl border border-white/15 bg-white/10 backdrop-blur-md transition-transform duration-300 group-hover:rotate-6 group-hover:scale-110" />
                  </div>
                  <div className="p-4">
                    <h3 className="truncate text-sm font-semibold text-white">{project.name || '未命名项目'}</h3>
                    <p className="mt-1 line-clamp-2 min-h-[32px] text-xs leading-4 text-gray-500">{project.description || '空白画布 · 等待第一轮创作'}</p>
                  </div>
                </button>
                <div className="flex items-center justify-between border-t border-white/[0.06] px-4 py-2.5 text-[11px]">
                  <span className="rounded-full bg-white/[0.06] px-2 py-0.5 text-gray-400">{project.generation_count || 0} 次生成</span>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">{project.created_at ? new Date(project.created_at).toLocaleDateString('zh-CN') : ''}</span>
                    <button
                      onClick={() => removeProject(project.id)}
                      disabled={busyId === project.id}
                      className="rounded-md px-1.5 py-1 text-gray-500 transition-colors hover:text-rose-400 disabled:opacity-50"
                      title="删除项目"
                    >
                      <svg viewBox="0 0 24 24" className="size-3.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-3xl border border-dashed border-white/[0.14] bg-white/[0.04] px-6 py-12 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-3xl border border-orange-400/20 bg-orange-500/10 text-3xl">📁</div>
            <h3 className="text-sm font-semibold">还没有项目</h3>
            <p className="mx-auto mt-2 max-w-sm text-xs leading-5 text-gray-500">从一个空白画布或一份产品资料开始，项目会以作品封面的形式陈列在这里。</p>
            <button onClick={createProject} className="mt-5 rounded-full bg-white px-4 py-2 text-xs font-semibold text-black transition-transform hover:scale-105">新建项目</button>
          </div>
        )}
      </div>
    </div>
  );
}
