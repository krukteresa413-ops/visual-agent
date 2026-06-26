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
  { to: '/prompts', label: '创意脚本库' },
  { to: '/inspiration', label: '灵感源' },
  { to: '/history', label: '历史' },
  { to: '/dashboard', label: 'Dashboard' },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { isLight, toggle } = useTheme();
  const [creating, setCreating] = useState(false);

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
            {/* Logo -> home */}
            <Link to="/" className="flex items-center gap-2 shrink-0 pr-2" aria-label="MOYAG 首页">
              <span className="grid place-items-center size-8 rounded-xl bg-gradient-to-br from-orange-500 to-rose-500 shadow-sm">
                <svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 3l1.9 4.6 4.6 1.4-4.6 1.9L12 15.5l-1.9-4.6L5.5 9l4.6-1.4L12 3z" />
                </svg>
              </span>
              <span className="hidden sm:flex flex-col leading-none">
                <span className="text-base font-bold tracking-tight text-white">MOYAG</span>
                <span className="text-[10px] tracking-widest text-gray-500">AGENT CANVAS</span>
              </span>
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
              <span className="text-sm font-semibold tabular-nums">—</span>
            </div>

            {/* Theme toggle (reuse existing component — contract) */}
            <ThemeToggle isLight={isLight} toggle={toggle} />

            {/* Avatar (decorative) */}
            <span className="grid place-items-center size-8 rounded-full bg-gradient-to-br from-orange-500 to-rose-500 text-[#fff] text-sm font-semibold shrink-0">
              M
            </span>
          </div>
        </header>
      )}
      {children}
    </div>
  );
}
