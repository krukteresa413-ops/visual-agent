import { useEffect } from 'react';

interface MenuItem {
  label: string;
  icon: string;
  divider?: boolean;
  action: string;
  shortcut?: string;
  danger?: boolean;
  implemented?: boolean;
}

const IMPLEMENTED_ACTIONS = new Set(['cutout', 'generate_font', 'add_chat', 'copy', 'delete', 'front', 'back', 'download']);

const MENU_ITEMS: MenuItem[] = [
  { label: '抠图', icon: '✂', action: 'cutout', implemented: true },
  { label: 'AI 翻译', icon: '🌐', action: 'ai_translate' },
  { label: 'AI 去水印', icon: '💧', action: 'ai_dewatermark' },
  { label: '生成字体', icon: '🔤', action: 'generate_font', divider: true, implemented: true },
  { label: '添加到聊天', icon: '💬', action: 'add_chat', implemented: true },
  { label: '复制', icon: '📋', shortcut: 'Ctrl+C', action: 'copy', implemented: true },
  { label: '删除', icon: '🗑', action: 'delete', danger: true, implemented: true },
  { label: '置顶', icon: '⬆', action: 'front', implemented: true },
  { label: '置底', icon: '⬇', action: 'back', implemented: true },
  { label: '下载', icon: '⬇', shortcut: 'Ctrl+E', action: 'download', implemented: true },
];

interface ContextMenuProps {
  x: number;
  y: number;
  elId: string;
  onClose: () => void;
  onAction: (action: string, elId: string) => void;
}

export default function ContextMenu({ x, y, elId, onClose, onAction }: ContextMenuProps) {
  // Close menu on any click outside
  useEffect(() => {
    const handle = () => onClose();
    // Delay to avoid closing immediately from the right-click event
    setTimeout(() => document.addEventListener('click', handle), 0);
    return () => document.removeEventListener('click', handle);
  }, [onClose]);

  // Adjust position to stay within viewport
  const adjX = Math.min(x, window.innerWidth - 200);
  const adjY = Math.min(y, window.innerHeight - MENU_ITEMS.length * 38);

  return (
    <div className="fixed z-[9999] min-w-[180px] bg-white rounded-xl shadow-2xl border border-gray-200 py-1.5 animate-fadeIn"
      style={{ left: adjX, top: adjY }}
      onClick={e => e.stopPropagation()}>
      {MENU_ITEMS.map((item, i) => {
        const implemented = item.implemented ?? IMPLEMENTED_ACTIONS.has(item.action);
        return (
        <div key={i}>
          {item.divider && i > 0 && <div className="my-1 border-t border-gray-100" />}
          <button
            disabled={!implemented}
            title={implemented ? item.label : '即将支持'}
            onClick={(e) => {
              e.stopPropagation();
              if (!implemented) return;
              onAction(item.action, elId);
              onClose();
            }}
            className={`w-full flex items-center gap-3 px-4 py-2 text-sm transition-colors text-left
              ${!implemented ? 'text-gray-300 cursor-not-allowed bg-white' : item.danger ? 'text-red-500 hover:bg-red-50' : 'text-gray-800 hover:bg-orange-50 hover:text-orange-600'}`}>
            <span className="text-base w-5 text-center">{item.icon}</span>
            <span className="flex-1">{item.label}</span>
            {!implemented && <span className="text-[10px] text-gray-300 ml-2">即将支持</span>}
            {item.shortcut && <span className="text-xs text-gray-400 ml-2">{item.shortcut}</span>}
          </button>
        </div>
        );
      })}
    </div>
  );
}
