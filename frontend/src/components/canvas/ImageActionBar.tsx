type Action = { id: string; label: string };

// 仅保留:下载 / 抠图 / 置顶 / 置底 / 删除
const ACTIONS: Action[] = [
  { id: 'download', label: '下载' },
  { id: 'cutout', label: '抠图' },
  { id: 'front', label: '置顶' },
  { id: 'back', label: '置底' },
  { id: 'delete', label: '删除' },
];

type Props = {
  left: number;
  top: number;
  onAction?: (id: string) => void;
  busy?: string | null;
  elementType?: string;
};

export default function ImageActionBar({ left, top, onAction, busy, elementType }: Props) {
  // 视频不需要「抠图」(仅对图片有意义)
  const actions = elementType === 'video' ? ACTIONS.filter((a) => a.id !== 'cutout') : ACTIONS;
  return (
    <div
      data-lovart-image-action-bar
      className="pointer-events-auto absolute z-50 flex h-11 -translate-x-1/2 items-center gap-1 rounded-[14px] border border-black/10 bg-white px-2 shadow-lo-elevation-100"
      style={{ left, top }}
    >
      {actions.map((action) => (
        <button
          key={action.id}
          data-image-action={action.id}
          type="button"
          onMouseDown={(e) => e.stopPropagation()}
          onClick={(e) => { e.stopPropagation(); onAction?.(action.id); }}
          disabled={busy === action.id}
          className={
            'h-8 rounded-md px-2 text-[11px] transition-colors disabled:opacity-40 ' +
            (action.id === 'delete'
              ? 'text-[#2F3640] hover:bg-rose-50 hover:text-rose-500'
              : 'text-[#2F3640] hover:bg-[#F1F3F5]')
          }
        >
          {busy === action.id ? '…' : action.label}
        </button>
      ))}
    </div>
  );
}
