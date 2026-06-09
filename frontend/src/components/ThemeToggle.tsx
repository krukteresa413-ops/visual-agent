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
      className="w-8 h-8 rounded-lg flex items-center justify-center text-sm transition-all
        hover:bg-white/10 border border-white/10"
      title={isLight ? '切换夜间模式' : '切换日间模式'}
    >
      {isLight ? '☀️' : '🌙'}
    </button>
  );
}
