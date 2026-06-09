import { useState, useEffect } from 'react';

const STORAGE_KEY = 'moyag-theme';

export function useTheme() {
  const [isLight, setIsLight] = useState(() => {
    return localStorage.getItem(STORAGE_KEY) === 'light';
  });

  useEffect(() => {
    const root = document.documentElement;
    if (isLight) {
      root.classList.add('light');
    } else {
      root.classList.remove('light');
    }
    localStorage.setItem(STORAGE_KEY, isLight ? 'light' : 'dark');
  }, [isLight]);

  return { isLight, toggle: () => setIsLight(p => !p) };
}

export default function ThemeToggle({ isLight, toggle }: { isLight: boolean; toggle: () => void }) {
  return (
    <button
      onClick={toggle}
      className="relative flex items-center h-8 px-0.5 rounded-full border transition-all duration-300
        bg-white/5 border-white/10 hover:border-white/20"
      style={{ minWidth: 56 }}
      title={isLight ? '切换夜间模式' : '切换日间模式'}
    >
      {/* Sliding background pill */}
      <span
        className={`absolute top-0.5 h-7 rounded-full transition-all duration-300 ease-out ${
          isLight
            ? 'left-0.5 w-7 bg-amber-400/20'
            : 'left-[27px] w-7 bg-indigo-500/20'
        }`}
      />

      {/* Sun */}
      <span className={`relative z-10 w-7 h-7 flex items-center justify-center text-xs transition-all duration-300 ${
        isLight ? 'scale-110' : 'scale-90 opacity-40'
      }`}>
        ☀️
      </span>

      {/* Moon */}
      <span className={`relative z-10 w-7 h-7 flex items-center justify-center text-xs transition-all duration-300 ${
        !isLight ? 'scale-110' : 'scale-90 opacity-40'
      }`}>
        🌙
      </span>
    </button>
  );
}
