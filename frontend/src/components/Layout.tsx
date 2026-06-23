/**
 * Global layout — top navigation bar (Phase 1.3).
 * Wraps all pages with consistent Dashboard | History links.
 */
import { Link, useLocation } from 'react-router-dom';
import ThemeToggle, { useTheme } from './ThemeToggle';

export default function Layout({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  const { isLight, toggle } = useTheme();

  const links = [
    { to: '/', label: '首页' },
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/history', label: '历史' },
    { to: '/inspiration', label: '灵感库' },
  ];

  const isActive = (path: string) => pathname === path || (path !== '/' && pathname.startsWith(path));
  const isCanvasWorkspace = pathname.startsWith('/generate/');

  return (
    <div className="text-white">
      {/* Top nav */}
      {!isCanvasWorkspace && (
      <nav className="sticky top-0 z-50 border-b border-gray-800 bg-black/80 backdrop-blur-md px-4 py-1.5 flex items-center justify-between">
        <div className="flex items-center gap-1">
          {links.map(link => (
            <Link
              key={link.to}
              to={link.to}
              className={`px-3 py-1 text-xs rounded transition-colors ${
                isActive(link.to)
                  ? 'bg-white/10 text-white'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-600">MOYAG · Agent Canvas</span>
          <ThemeToggle isLight={isLight} toggle={toggle} />
        </div>
      </nav>
      )}
      {children}
    </div>
  );
}
