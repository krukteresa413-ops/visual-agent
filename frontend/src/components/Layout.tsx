/**
 * Global layout — top navigation bar.
 * Button structure modeled on the MOYAG reference top bar
 * (logo · tabs · new-project · credits · theme · avatar).
 * Colors reuse the existing dark shell; the global nav stays hidden inside the canvas workspace.
 */
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import ThemeToggle, { useTheme } from './ThemeToggle';
import { api } from '../api/client';

const NAV = [
  { to: '/', label: '首页' },
  { to: '/projects', label: '项目库' },
  { to: '/brands', label: '品牌库' },
  { to: '/prompts', label: '创意脚本库' },
  { to: '/inspiration', label: '灵感源' },
  { to: '/dashboard', label: '数据看板' },
  { to: '/copywriting', label: 'AI 文案助手' },
  { to: '/video-edit', label: '视频剪辑' },
  { to: '/profile', label: '个人中心' },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { isLight, toggle } = useTheme();
  const [creating, setCreating] = useState(false);
  // Mock 数据(暂无后端积分/头像接口):随机一次,保持本次会话稳定
  const [credits] = useState(() => 800 + Math.floor(Math.random() * 4200));
  const [avatar] = useState(() => {
    const letters = ['M', 'A', 'Y', 'G', 'Z', 'L', 'K'];
    const grads = [
      'from-orange-500 to-rose-500',
      'from-sky-500 to-indigo-500',
      'from-emerald-500 to-teal-500',
      'from-fuchsia-500 to-purple-500',
      'from-amber-500 to-orange-600',
    ];
    return {
      letter: letters[Math.floor(Math.random() * letters.length)],
      grad: grads[Math.floor(Math.random() * grads.length)],
    };
  });

  const isActive = (path: string) =>
    pathname === path || (path !== '/' && pathname.startsWith(path));
  const isCanvasWorkspace = pathname.startsWith('/generate/');

  const handleNewProject = async () => {
    if (creating) return;
    setCreating(true);
    try {
      const project = await api.projects.create('未命名项目', '');
      navigate(`/generate/${project.id}`);
    } catch {
      // surface failure silently for now; the project list stays reachable
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="text-white">
      {!isCanvasWorkspace && (
        <header className={`sticky top-0 z-50 w-full border-b border-gray-800 backdrop-blur-md ${isLight ? 'bg-white/80' : 'bg-black/80'}`}>
          <div className="flex h-14 items-center gap-2 px-4">
            {/* Logo -> home (PNG 字标,日间黑色 / 夜间反色为白) */}
            <Link to="/" className="flex items-center gap-2 shrink-0 pr-2" aria-label="MOYAG 首页">
              <img src="/logo-wordmark.png" alt="MOYAG" className="logo-img h-6 w-auto sm:h-7" />
            </Link>

            {/* Nav tabs (desktop) */}
            <nav className="hidden md:flex items-center gap-1 ml-3">
              {NAV.map((n) => {
                const active = isActive(n.to);
                return (
                  <Link
                    key={n.to}
                    to={n.to}
                    className={
                      'relative px-3 py-2 text-sm font-medium rounded-lg transition-colors ' +
                      (active
                        ? 'text-white'
                        : 'text-gray-500 hover:text-gray-300 hover:bg-white/5')
                    }
                  >
                    {n.label}
                    {active && (
                      <span className="absolute -bottom-px left-3 right-3 h-0.5 rounded-full bg-orange-500" />
                    )}
                  </Link>
                );
              })}
            </nav>

            <div className="flex-1" />

            {/* Nav (mobile select) */}
            <select
              className={`md:hidden h-9 rounded-lg border border-gray-800 text-sm text-gray-300 px-2 ${isLight ? 'bg-white' : 'bg-black'}`}
              value={NAV.find((n) => isActive(n.to))?.to ?? '/'}
              onChange={(e) => navigate(e.target.value)}
              aria-label="导航"
            >
              {NAV.map((n) => (
                <option key={n.to} value={n.to}>{n.label}</option>
              ))}
            </select>

            {/* New project -> create an empty project, then open its canvas */}
            <button
              onClick={handleNewProject}
              disabled={creating}
              className="hidden sm:inline-flex items-center gap-1.5 h-9 px-3 rounded-lg bg-gradient-to-r from-orange-500 to-rose-500 text-[#fff] text-sm font-medium transition-transform hover:scale-[1.03] disabled:opacity-50"
            >
              <svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 5v14M5 12h14" />
              </svg>
              {creating ? '创建中…' : '新建项目'}
            </button>

            {/* Credits (no backend credits API yet — placeholder) */}
            <div className="hidden lg:flex items-center gap-1.5 h-9 px-3 rounded-lg bg-white/5 border border-white/10 text-gray-300">
              <svg viewBox="0 0 24 24" className="size-4 text-orange-400" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="8" />
                <path d="M12 8v8M9.5 10.5h3a1.5 1.5 0 0 1 0 3h-3" />
              </svg>
              <span className="text-sm font-semibold tabular-nums">{credits.toLocaleString()}</span>
            </div>

            {/* Theme toggle (reuse existing component — contract) */}
            <ThemeToggle isLight={isLight} toggle={toggle} />

            {/* Avatar (mock) */}
            <span className={`grid place-items-center size-8 rounded-full bg-gradient-to-br ${avatar.grad} text-[#fff] text-sm font-semibold shrink-0`}>
              {avatar.letter}
            </span>
          </div>
        </header>
      )}
      {children}
    </div>
  );
}
