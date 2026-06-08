import { useState } from 'react';
import type { VisualAssetPlan } from '../api/client';

const TABS = [
  { key: 'main_image', label: '主图方案', icon: '🖼️' },
  { key: 'white_bg', label: '白底图', icon: '⬜' },
  { key: 'scene_images', label: '场景图', icon: '🏪' },
  { key: 'selling_points', label: '卖点图', icon: '⭐' },
  { key: 'video_scripts', label: '视频脚本', icon: '🎬' },
  { key: 'ad_material', label: '广告素材', icon: '📢' },
];

type ImageInfo = { url: string; width?: number; height?: number };

function Field({ label, value }: { label: string; value?: string }) {
  if (!value) return null;
  return <div className="mb-4"><p className="text-xs text-gray-500 mb-1">{label}</p><p className="text-sm text-gray-200">{value}</p></div>;
}

function PromptBlock({ value }: { value?: string }) {
  const [copied, setCopied] = useState(false);
  if (!value) return null;
  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs text-gray-500">图像生成 Prompt</p>
        <button onClick={() => { navigator.clipboard.writeText(value); setCopied(true); setTimeout(() => setCopied(false), 1500); }} className="text-xs text-orange-400 hover:text-orange-300">{copied ? '已复制' : '复制'}</button>
      </div>
      <pre className="bg-gray-900 rounded-lg p-3 text-xs text-green-300 whitespace-pre-wrap break-words border border-gray-800">{value}</pre>
    </div>
  );
}

function ImagePreview({ image }: { image?: ImageInfo | null }) {
  if (!image) return null;
  return (
    <div className="mb-4 rounded-xl overflow-hidden border border-gray-700">
      <img src={image.url} alt="生成图片" className="w-full h-auto" loading="lazy" />
      <div className="bg-gray-900 px-3 py-1.5 text-[10px] text-gray-500">
        {image.width}x{image.height}
      </div>
    </div>
  );
}

function MainImagePanel({ data, image }: { data: any; image?: ImageInfo | null }) {
  return <div>
    <ImagePreview image={image} />
    <Field label="主图目标" value={data.goal} />
    <Field label="构图方案" value={data.composition} />
    <Field label="背景风格" value={data.background} />
    <Field label="光影方案" value={data.lighting} />
    <Field label="文案建议" value={data.copywriting} />
    <PromptBlock value={data.prompt} />
    <Field label="禁用项" value={data.negative_prompt} />
    <Field label="适配平台" value={data.platform} />
  </div>;
}

function ScenesPanel({ data, images }: { data: any[]; images?: (ImageInfo | null)[] }) {
  if (!data?.length) return <p className="text-gray-500 text-sm">暂无场景图方案</p>;
  return <div className="space-y-6">{data.map((scene: any, i: number) => (
    <div key={i} className="border border-gray-800 rounded-xl p-4">
      {images?.[i] && <ImagePreview image={images[i]} />}
      <h3 className="font-medium text-orange-300 mb-3">场景 {i+1}：{scene.scene_name}</h3>
      <Field label="目标用户" value={scene.target_user} />
      <Field label="场景叙事" value={scene.scene_narrative} />
      {scene.visual_elements?.length > 0 && <Field label="画面元素" value={scene.visual_elements.join('、')} />}
      <Field label="产品位置" value={scene.product_position} />
      <PromptBlock value={scene.prompt} />
    </div>
  ))}</div>;
}

function WhiteBgPanel({ data }: { data: any }) {
  return <div><Field label="目标" value={data.goal} /><Field label="处理指令" value={data.instructions} />{data.quality_checklist && <div><p className="text-xs text-gray-500 mb-2">质量检查项</p><ul className="space-y-1">{data.quality_checklist.map((item: string, i: number) => <li key={i} className="text-sm text-gray-200 flex items-center gap-2"><span className="text-green-400">✓</span> {item}</li>)}</ul></div>}</div>;
}

function SellingPointsPanel({ data }: { data: any[] }) {
  if (!data?.length) return <p className="text-gray-500 text-sm">暂无卖点图模块</p>;
  return <div className="space-y-4">{data.map((sp: any, i: number) => <div key={i} className="border border-gray-800 rounded-xl p-4"><h3 className="font-medium text-orange-300 mb-2">{i+1}. {sp.title}</h3><Field label="文案" value={sp.description} /><Field label="视觉表现" value={sp.visual_representation} /><div className="flex gap-4 mt-2"><span className="text-xs bg-gray-800 px-2 py-1 rounded">图标：{sp.icon_suggestion}</span><span className="text-xs bg-gray-800 px-2 py-1 rounded">布局：{sp.layout_suggestion}</span></div></div>)}</div>;
}

function VideoScriptsPanel({ data }: { data: any[] }) {
  if (!data?.length) return <p className="text-gray-500 text-sm">暂无视频脚本</p>;
  return <div className="space-y-6">{data.map((script: any, i: number) => <div key={i} className="border border-gray-800 rounded-xl p-4"><div className="flex items-center gap-3 mb-3"><span className="bg-orange-500 text-white text-xs px-2 py-1 rounded-full">{script.duration_seconds}秒</span><span className="text-sm text-gray-300">{script.video_goal}</span></div><Field label="节奏" value={script.pacing} />{script.material_requirements?.length > 0 && <Field label="所需素材" value={script.material_requirements.join('、')} />}<Field label="CTA" value={script.cta} />{script.storyboard?.length > 0 && <div className="mt-3"><p className="text-xs text-gray-500 mb-2">分镜</p><div className="space-y-2">{script.storyboard.map((shot: any, j: number) => <div key={j} className="bg-gray-900 rounded-lg p-3 text-xs"><span className="text-orange-400">镜头{shot.shot_number} {shot.duration}</span><p className="text-gray-300 mt-1">画面：{shot.visual}</p>{shot.subtitle && <p className="text-blue-300">字幕：{shot.subtitle}</p>}{shot.voiceover && <p className="text-green-300">旁白：{shot.voiceover}</p>}</div>)}</div></div>}</div>)}</div>;
}

function AdMaterialPanel({ data }: { data: any }) {
  return <div><Field label="广告目标" value={data.ad_goal} /><Field label="目标人群" value={data.target_audience} /><Field label="切入角度" value={data.ad_angle} />{data.hook && <div className="mb-4"><p className="text-xs text-gray-500 mb-1">开头钩子</p><div className="bg-gray-900 rounded-lg p-3 text-sm text-yellow-300 border border-gray-800">"{data.hook}"</div></div>}{data.key_selling_points?.length > 0 && <Field label="核心卖点" value={data.key_selling_points.join('、')} />}{data.material_list?.length > 0 && <Field label="素材清单" value={data.material_list.join('、')} />}<Field label="CTA" value={data.cta} /><Field label="建议平台" value={data.platform_suggestion} /></div>;
}

type ImagesData = {
  main_image?: { url: string; width?: number; height?: number } | null;
  scene_images?: ({ url: string; width?: number; height?: number } | null)[];
};

export default function ResultTabs({ plan, images }: { plan: VisualAssetPlan; images?: ImagesData | null }) {
  const [active, setActive] = useState('main_image');
  const render = () => {
    switch (active) {
      case 'main_image': return <MainImagePanel data={plan.main_image} image={images?.main_image} />;
      case 'white_bg': return <WhiteBgPanel data={plan.white_bg} />;
      case 'scene_images': return <ScenesPanel data={plan.scene_images} images={images?.scene_images} />;
      case 'selling_points': return <SellingPointsPanel data={plan.selling_points} />;
      case 'video_scripts': return <VideoScriptsPanel data={plan.video_scripts} />;
      case 'ad_material': return <AdMaterialPanel data={plan.ad_material} />;
      default: return null;
    }
  };
  return (
    <div className="border border-gray-800 rounded-2xl overflow-hidden">
      <div className="flex border-b border-gray-800 bg-gray-900/50">
        {TABS.map(tab => <button key={tab.key} onClick={() => setActive(tab.key)} className={`flex-1 py-3 text-xs font-medium transition-colors ${active === tab.key ? 'text-orange-400 border-b-2 border-orange-500 bg-gray-900' : 'text-gray-500 hover:text-gray-300'}`}><span className="block">{tab.icon}</span>{tab.label}</button>)}
      </div>
      <div className="p-6 max-h-[600px] overflow-y-auto">{render()}</div>
    </div>
  );
}
