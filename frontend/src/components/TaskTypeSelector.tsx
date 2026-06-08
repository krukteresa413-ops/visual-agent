// Part C: Task Type Selector
const TASKS = [
  { key: 'main_image', label: '主图', icon: '🖼️', desc: '电商主图方案 + Prompt' },
  { key: 'white_bg', label: '白底图', icon: '⬜', desc: '纯白背景产品图' },
  { key: 'scene_images', label: '场景图', icon: '🏪', desc: '1-3个使用场景+Prompt' },
  { key: 'selling_points', label: '卖点图', icon: '⭐', desc: '3-5个卖点模块' },
  { key: 'video_scripts', label: '视频脚本', icon: '🎬', desc: '15+30秒分镜脚本' },
  { key: 'ad_material', label: '广告素材', icon: '📢', desc: '广告方案+CTA' },
];

interface Props { selected: string[]; onChange: (t: string[]) => void; }
export default function TaskTypeSelector({ selected, onChange }: Props) {
  const toggle = (k: string) => selected.includes(k) ? onChange(selected.filter(x=>x!==k)) : onChange([...selected, k]);
  const all = selected.length === TASKS.length;
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <label className="text-xs font-medium text-gray-400">生成类型</label>
        <button onClick={() => onChange(all ? [] : TASKS.map(t=>t.key))} className="text-xs text-orange-400 hover:text-orange-300">{all?'取消全选':'全选'}</button>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {TASKS.map(t => { const sel = selected.includes(t.key); return (
          <button key={t.key} onClick={() => toggle(t.key)} className={`text-left p-3 rounded-lg border text-xs transition-all ${sel?'border-orange-500 bg-orange-950/30 text-orange-200':'border-gray-800 bg-gray-900 text-gray-500 hover:border-gray-600'}`}>
            <div className="flex items-center gap-2 mb-1"><span>{t.icon}</span><span className="font-medium">{t.label}</span></div>
            <p className="text-gray-600 leading-tight">{t.desc}</p>
          </button>
        )})}
      </div>
    </div>
  );
}
