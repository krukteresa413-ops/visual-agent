import { useEffect, useState } from 'react';
import { api } from '../api/client';

// 空对话起始页(图一):浮现精选技能快捷入口 + 「所有 Skills」。对齐 Lovart 起始页观感。
const CATEGORY_ICONS: Record<string, string> = {
  '视频': '🎬', '社交媒体': '📱', '电商': '🛒', '品牌': '🎨', '营销': '📣', '工作室': '🖼️',
};
// 精选技能(按 docx 起始页挑选)；线上缺失时用其余技能补齐
const FEATURED_IDS = ['seedance', 'one-shot', 'instagram-post', 'cross-platform', 'logo-design', 'ugc-lifestyle', 'ai-stylist'];

type Skill = { id: string; title: string; category: string; prompt: string };

interface Props {
  isLight?: boolean;
  onPick: (prompt: string, category: string) => void;
  onShowAll: () => void;
}

export default function SkillsEmptyState({ isLight, onPick, onShowAll }: Props) {
  const [skills, setSkills] = useState<Skill[]>([]);

  useEffect(() => {
    let cancelled = false;
    api.generation.skills().then((sk: Skill[]) => {
      if (cancelled) return;
      const list = Array.isArray(sk) ? sk : [];
      const byId = new Map(list.map((s) => [s.id, s]));
      const featured = FEATURED_IDS.map((id) => byId.get(id)).filter(Boolean) as Skill[];
      const extra = list.filter((s) => !FEATURED_IDS.includes(s.id));
      setSkills((featured.length >= 4 ? featured : [...featured, ...extra]).slice(0, 7));
    }).catch(() => { /* 拉取失败则不显示空态 */ });
    return () => { cancelled = true; };
  }, []);

  if (!skills.length) return null;

  const titleColor = isLight ? 'text-gray-900' : 'text-white';
  const chip = isLight
    ? 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50'
    : 'border-white/10 bg-white/[0.04] text-gray-200 hover:border-white/25 hover:bg-white/[0.07]';

  return (
    <div data-skills-empty-state className="flex h-full flex-col items-center justify-center px-2">
      <div className={`mb-4 text-sm font-semibold ${titleColor}`}>试试这些 Skills</div>
      <div className="grid w-full max-w-md grid-cols-2 gap-2">
        {skills.map((s) => (
          <button
            key={s.id}
            type="button"
            data-empty-skill={s.id}
            onClick={() => onPick(s.prompt, s.category)}
            className={`flex items-center gap-2 rounded-full border px-3 py-2 text-left text-xs transition-colors ${chip}`}
          >
            <span className="shrink-0 text-sm">{CATEGORY_ICONS[s.category] || '⚡'}</span>
            <span className="truncate">{s.title}</span>
          </button>
        ))}
        <button
          type="button"
          data-empty-skill="__all__"
          onClick={onShowAll}
          className={`col-span-2 flex items-center justify-center gap-2 rounded-full border px-3 py-2 text-xs transition-colors ${chip}`}
        >
          <span className="text-sm">📖</span>
          <span>所有 Skills</span>
        </button>
      </div>
    </div>
  );
}
