import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';

interface Props {
  isLight: boolean;
  onClose: () => void;
  onSelectSkill?: (prompt: string, category: string) => void;
  anchorEl?: HTMLElement | null;
}

type Skill = {
  id: string;
  title: string;
  description: string;
  category: string;
  prompt: string;
  enabled: boolean;
};

export default function SkillsPopup({ isLight, onClose, onSelectSkill, anchorEl }: Props) {
  const [activeCategory, setActiveCategory] = useState('Video');
  const [skills, setSkills] = useState<Skill[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const popupRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    Promise.all([
      api.generation.skillCategories(),
      api.generation.skills(),
    ]).then(([cats, sk]: [string[], Skill[]]) => {
      setCategories(cats || []);
      setSkills(sk || []);
      if (cats && cats.length > 0 && !cats.includes(activeCategory)) {
        setActiveCategory(cats[0]);
      }
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  // Position popover below anchor; without anchor it is embedded by the caller.
  useEffect(() => {
    if (anchorEl) {
      const rect = anchorEl.getBoundingClientRect();
      setPosition({
        top: rect.bottom + 6,
        left: Math.max(8, rect.left - 180),
      });
    }
    // Close on outside click
    const handler = (e: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(e.target as Node) &&
          anchorEl && !anchorEl.contains(e.target as Node)) {
        onClose();
      }
    };
    setTimeout(() => document.addEventListener('click', handler), 0);
    return () => document.removeEventListener('click', handler);
  }, [anchorEl, onClose]);

  const filtered = skills.filter((s) => s.category === activeCategory);
  const displayCategories = categories.length > 0 ? categories : ['Video', 'Social Media', 'E-Commerce', 'Branding'];

  const bg = isLight ? 'bg-white' : 'bg-gray-900';
  const placementClass = anchorEl ? 'fixed z-[100] w-[280px]' : 'relative z-30 w-full';
  const placementStyle = anchorEl ? { top: position.top, left: position.left } : undefined;
  const textColor = isLight ? 'text-gray-900' : 'text-white';
  const subText = isLight ? 'text-gray-500' : 'text-gray-400';

  return (
    <div
      ref={popupRef}
      className={`${placementClass} ${bg} rounded-xl shadow-2xl border border-black/10 max-h-[420px] flex flex-col overflow-hidden`}
      style={placementStyle}
    >
      {/* Category chips */}
      <div className="px-3 pt-3 pb-2 overflow-x-auto">
        <div className="flex gap-1.5 min-w-max">
          {displayCategories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`whitespace-nowrap text-[10px] transition-colors px-2 py-0.5 rounded-full border ${
                activeCategory === cat
                  ? isLight ? 'bg-gray-900 text-white border-gray-900' : 'bg-white text-gray-900 border-white'
                  : isLight ? 'bg-white text-gray-500 border-gray-200 hover:border-gray-400' : 'bg-gray-900/50 text-gray-400 border-white/10 hover:border-white/30'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Skills list */}
      <div className="flex-1 overflow-y-auto px-3 pb-2 space-y-0.5">
        {loading && <p className="text-[11px] text-gray-400 text-center py-4">加载中...</p>}
        {!loading && filtered.length === 0 && <p className="text-[11px] text-gray-400 text-center py-4">暂无可用</p>}
        {filtered.map((skill) => (
          <button
            key={skill.id}
            onClick={() => {
              if (skill.prompt && onSelectSkill) {
                onSelectSkill(skill.prompt, skill.category);
                onClose();
              }
            }}
            className={`flex items-center gap-2.5 w-full py-2 px-2 rounded-lg transition-colors text-left hover:bg-black/5`}
          >
            <div className={`size-8 rounded-lg flex items-center justify-center shrink-0 ${isLight ? 'bg-gray-100' : 'bg-white/5'}`}>
              <span className="text-sm">⚡</span>
            </div>
            <div className="min-w-0">
              <div className={`text-[11px] font-medium truncate ${textColor}`}>{skill.title}</div>
              <div className={`text-[10px] ${subText} truncate`}>{skill.description}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
