interface Props { data: Record<string,any> | null; }
const PRI: Record<string,string> = { high:'text-red-400 bg-red-950', medium:'text-yellow-400 bg-yellow-950', low:'text-green-400 bg-green-950' };
const LABELS: Record<string,string> = { main_image:'主图',white_bg:'白底图',scene_images:'场景',selling_points:'卖点',video_scripts:'视频',ad_material:'广告',detail_page:'详情页' };
function Fld({ label, value }: { label:string; value?:string }) {
  if (!value) return null;
  return <div className='mb-4'><p className='text-xs text-gray-500 mb-1'>{label}</p><p className='text-sm text-gray-200'>{value}</p></div>;
}
export default function StrategyPanel({ data }: Props) {
  if (!data) return <p className='text-gray-500 text-sm'>暂无策略概览</p>;
  const cls = data.audience_type === 'B2B' ? 'bg-blue-950 text-blue-300' : 'bg-purple-950 text-purple-300';
  return (
    <div className='space-y-5'>
      <div className='flex gap-2'><span className={'text-xs px-3 py-1 rounded-full '+cls}>{data.audience_type||'B2B'}</span></div>
      <Fld label='视觉定位' value={data.visual_positioning} /><Fld label='目标客户分析' value={data.target_customer_analysis} /><Fld label='视觉风格' value={data.visual_style} /><Fld label='品牌调性' value={data.brand_tone} />
      {data.selling_points_priority?.length > 0 && (<div><p className='text-xs text-gray-500 mb-2'>卖点优先级</p><div className='space-y-1'>{data.selling_points_priority.map((sp:string,i:number) => <div key={i} className='flex items-center gap-3 text-sm'><span className='text-orange-400 font-mono text-xs w-5'>{i+1}.</span><span className='text-gray-200'>{sp}</span></div>)}</div></div>)}
      {data.asset_plan_summary?.length > 0 && (<div><p className='text-xs text-gray-500 mb-2'>素材规划</p><div className='space-y-2'>{data.asset_plan_summary.map((item:any,i:number) => { const pc = PRI[item.priority||'medium']||''; return <div key={i} className='border border-gray-800 rounded-lg p-3'><div className='flex items-center justify-between mb-1'><span className='text-sm font-medium text-gray-200'>{LABELS[item.asset_type]||item.asset_type}</span><span className={'text-xs px-2 py-0.5 rounded-full '+pc}>{item.priority}</span></div><p className='text-xs text-gray-400'>{item.purpose}</p><p className='text-xs text-gray-600 mt-1'>{item.platform_suggestion}</p></div>; })}</div></div>)}
      {data.key_differentiators?.length > 0 && (<div><p className='text-xs text-gray-500 mb-2'>关键差异点</p><div className='flex flex-wrap gap-2'>{data.key_differentiators.map((d:string,i:number) => <span key={i} className='text-xs bg-gray-800 text-gray-300 px-2 py-1 rounded-lg'>{d}</span>)}</div></div>)}
    </div>
  );
}
