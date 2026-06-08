interface Module { order:number; module_type:string; title:string; content_description:string; visual_suggestion:string; recommended_height_px?:number; copywriting?:string; }
interface Props { data: Record<string,any> | null; }
const ICONS: Record<string,string> = { hero_banner:'🎯', selling_point:'⭐', scene:'🏪', specs:'📋', trust:'🛡️', cta:'📢' };
function Fld({ label, value }: { label:string; value?:string }) {
  if (!value) return null;
  return <div className="mb-3"><p className="text-xs text-gray-500 mb-1">{label}</p><p className="text-sm text-gray-200">{value}</p></div>;
}
export default function DetailPagePanel({ data }: Props) {
  if (!data) return <p className="text-gray-500 text-sm">暂无详情页方案</p>;
  const mods = data.modules || [];
  return (
    <div className="space-y-4">
      <div className="bg-gray-900/50 rounded-lg p-4">
        <Fld label="页面目标" value={data.page_goal} />
        <div className="flex gap-4 text-xs text-gray-400"><span>平台:{data.target_platform}</span><span>受众:{data.target_audience}</span><span>滚动:{data.estimated_scroll_depth}</span><span>模块:{data.total_modules}</span></div>
      </div>
      <div className="relative"><div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-800" />
        {mods.map((m:Module,i:number) => (
          <div key={i} className="relative pl-10 pb-4">
            <div className="absolute left-2.5 w-3 h-3 rounded-full bg-orange-500 border-2 border-gray-900" />
            <div className="border border-gray-800 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2"><span>{ICONS[m.module_type]||'📌'}</span><span className="text-xs bg-gray-800 px-2 py-0.5 rounded-full text-gray-400">#{m.order}</span><h4 className="text-sm font-medium text-orange-300">{m.title}</h4></div>
              <Fld label="内容" value={m.content_description} /><Fld label="视觉" value={m.visual_suggestion} />
              {m.copywriting && <Fld label="文案" value={m.copywriting} />}
              {m.recommended_height_px && <span className="text-xs text-gray-600">~{m.recommended_height_px}px</span>}
            </div>
          </div>
        ))}
      </div>
      {data.design_notes && <div className="bg-gray-900 rounded-lg p-3 text-xs text-gray-400">{data.design_notes}</div>}
    </div>
  );
}
