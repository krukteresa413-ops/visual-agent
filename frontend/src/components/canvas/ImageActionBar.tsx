type Action = { id: string; label: string; enabled: boolean };

const actions: Action[] = [
  { id: 'download', label: '下载', enabled: true },
  { id: 'edit', label: '编辑', enabled: true },
  { id: 'variant', label: '变体', enabled: true },
  { id: 'cutout', label: '抠图', enabled: true },
  { id: 'upscale', label: '高清', enabled: false },
  { id: 'layer', label: '分层', enabled: false },
  { id: 'copy', label: '复制', enabled: false },
  { id: 'replace', label: '替换', enabled: false },
  { id: 'pin', label: '固定', enabled: false },
  { id: 'delete', label: '删除', enabled: false },
];

type Props = {
  left: number;
  top: number;
};

export default function ImageActionBar({ left, top }: Props) {
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
          disabled={!action.enabled}
          className="h-8 rounded-md px-2 text-[11px] text-[#2F3640] hover:bg-[#F1F3F5] disabled:cursor-not-allowed disabled:opacity-35"
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}
