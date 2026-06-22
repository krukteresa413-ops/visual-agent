// @ts-nocheck
import { useMemo, useRef, useState } from 'react';
import type { VisualAssetPlan } from '../types';
import LayoutPanel from './LayoutPanel';
import { api } from '../api/client';

const TABS = [
  { key: 'main_image', label: '主图方案', icon: '🖼️' },
  { key: 'white_bg', label: '白底图', icon: '⬜' },
  { key: 'scene_images', label: '场景图', icon: '🏪' },
  { key: 'selling_points', label: '卖点图', icon: '⭐' },
  { key: 'video_scripts', label: '视频脚本', icon: '🎬' },
  { key: 'ad_material', label: '广告素材', icon: '📢' },
  { key: 'layout', label: '排版', icon: '📐' },
];

const IMAGE_TABS = new Set(['main_image', 'white_bg', 'scene_images', 'selling_points', 'ad_material', 'layout']);

type ImageInfo = { url: string; width?: number; height?: number };

type OneClickResult = {
  type: 'image' | 'text';
  url?: string;
  width?: number;
  height?: number;
  text?: string;
};

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

type RefSource = 'uploaded_product' | 'generated_main_image' | 'none';

function OneClickGeneratedPreview({ result, addState, onAddToCanvas }: {
  result?: OneClickResult;
  addState?: { added: boolean; adding: boolean };
  onAddToCanvas?: () => void;
}) {
  const isAdded = addState?.added;
  const isAdding = addState?.adding;
  return (
    <div data-oneclick-result className="mb-4 rounded-xl border border-orange-500/25 bg-orange-500/5 p-3">
      {result && (
        <>
          <div className="mb-2 flex items-center justify-between">
            <p className="text-xs font-medium text-orange-300">生成结果</p>
            {result.type === 'image' && onAddToCanvas && (
              <button
                onClick={onAddToCanvas}
                disabled={isAdded || isAdding}
                className={`rounded px-2 py-1 text-[10px] transition-colors ${
                  isAdded
                    ? 'cursor-default bg-green-500/15 text-green-400'
                    : 'bg-orange-500/15 text-orange-300 hover:bg-orange-500/25'
                }`}
              >
                {isAdding ? '加入中…' : isAdded ? '✓ 已加入' : '加入画布'}
              </button>
            )}
          </div>
          {result.type === 'image' && result.url && <ImagePreview image={{ url: result.url, width: result.width, height: result.height }} />}
          {result.type === 'text' && <pre className="whitespace-pre-wrap rounded-lg bg-gray-950 p-3 text-xs text-gray-200">{result.text}</pre>}
        </>
      )}
    </div>
  );
}

function MainImagePanel({ data, image }: { data: any; image?: ImageInfo | null }) {
  return <div>
    <ImagePreview image={image} />
    <Field label="主图目标" value={data?.goal} />
    <Field label="构图方案" value={data?.composition} />
    <Field label="背景风格" value={data?.background} />
    <Field label="光影方案" value={data?.lighting} />
    <Field label="文案建议" value={data?.copywriting} />
    <PromptBlock value={data?.prompt} />
    <Field label="禁用项" value={data?.negative_prompt} />
    <Field label="适配平台" value={data?.platform} />
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
  return <div><Field label="目标" value={data?.goal} /><Field label="处理指令" value={data?.instructions} />{data?.quality_checklist && <div><p className="text-xs text-gray-500 mb-2">质量检查项</p><ul className="space-y-1">{data.quality_checklist.map((item: string, i: number) => <li key={i} className="text-sm text-gray-200 flex items-center gap-2"><span className="text-green-400">✓</span> {item}</li>)}</ul></div>}</div>;
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
  return <div><Field label="广告目标" value={data?.ad_goal} /><Field label="目标人群" value={data?.target_audience} /><Field label="切入角度" value={data?.ad_angle} />{data?.hook && <div className="mb-4"><p className="text-xs text-gray-500 mb-1">开头钩子</p><div className="bg-gray-900 rounded-lg p-3 text-sm text-yellow-300 border border-gray-800">"{data.hook}"</div></div>}{data?.key_selling_points?.length > 0 && <Field label="核心卖点" value={data.key_selling_points.join('、')} />}{data?.material_list?.length > 0 && <Field label="素材清单" value={data.material_list.join('、')} />}<Field label="CTA" value={data?.cta} /><Field label="建议平台" value={data?.platform_suggestion} /></div>;
}

type ImagesData = {
  main_image?: { url: string; width?: number; height?: number } | null;
  scene_images?: ({ url: string; width?: number; height?: number } | null)[];
};

function promptForTab(active: string, plan: VisualAssetPlan, productName: string): string {
  // P2-10: Stronger subject injection for consistency
  const brandName = productName || '产品';
  const mainGoal = plan.main_image?.goal || '';
  const mainStyle = plan.main_image?.composition || plan.main_image?.background || '';
  const subject = `${brandName}（${mainGoal || '高品质'}，${mainStyle || '简洁干净'}）`;
  if (active === 'main_image') return `${subject}，主图特写，${plan.main_image?.prompt || plan.main_image?.goal || ''}`;
  if (active === 'white_bg') return `${subject}，纯白背景棚拍，${brandName}居中，无多余道具，电商白底图标准。${plan.white_bg?.goal || ''}。${plan.white_bg?.instructions || ''}`;
  if (active === 'scene_images') return `${subject}，${brandName}置于真实使用场景中，${plan.scene_images?.[0]?.scene_narrative || ''}。${plan.scene_images?.[0]?.prompt || ''}`;
  if (active === 'selling_points') return `${subject}，${brandName}卖点可视化展示，${plan.selling_points?.map((item: any) => `${item.title}: ${item.visual_representation || item.description}`).join('；') || ''}`;
  if (active === 'ad_material') return `${subject}，${brandName}广告素材，${plan.ad_material?.hook || ''} ${plan.ad_material?.ad_angle || ''} ${plan.ad_material?.key_selling_points?.join(' ') || ''}`.trim();
  if (active === 'layout') return `${subject}，${brandName}电商详情页排版视觉图，${JSON.stringify(plan.layout_plan || {}).slice(0, 500)}`;
  return subject;
}

function generateVideoScriptText(plan: VisualAssetPlan): string {
  const scripts = plan.video_scripts || [];
  if (!scripts.length) return '视频脚本生成完成：请补充产品卖点后继续细化分镜。';
  return scripts.map((script: any, index: number) => {
    const shots = (script.storyboard || []).map((shot: any) => `镜头${shot.shot_number}: ${shot.visual}${shot.subtitle ? `｜字幕：${shot.subtitle}` : ''}`).join('\n');
    return `脚本 ${index + 1}（${script.duration_seconds || 5}秒）\n目标：${script.video_goal || ''}\n节奏：${script.pacing || ''}\nCTA：${script.cta || ''}\n${shots}`;
  }).join('\n\n');
}

function OneClickGenerateButton({ active, plan, generatedByTab, setGeneratedByTab, productName, refSource, projectId }: any) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [added, setAdded] = useState(false);
  const [adding, setAdding] = useState(false);
  const current = generatedByTab[active];

  const generate = async () => {
    setLoading(true);
    setError('');
    try {
      if (active === 'video_scripts') {
        setGeneratedByTab((prev: any) => ({ ...prev, [active]: { type: 'text', text: generateVideoScriptText(plan) } }));
        return;
      }
      const prompt = `${promptForTab(active, plan, productName)}\n品牌色：橙色点缀；风格：高级、清爽、可用于电商素材。`;
      if (!prompt.trim()) throw new Error('当前分类缺少可生成的 prompt');
      const params: any = { provider: 'dataeyes', prompt, width: 1024, height: 1024 };
      if (refSource !== 'none' && refSource) {
        params.reference_image_url = refSource;
      }
      const result = await api.generation.image(params);
      const image = result?.images?.[0];
      if (!image?.url) throw new Error('生成成功但没有返回图片');
      setGeneratedByTab((prev: any) => ({ ...prev, [active]: { type: 'image', url: image.url, width: image.width, height: image.height } }));
    } catch (err: any) {
      setError(err?.message || '生成失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCanvas = async () => {
    if (added || adding || !current?.url) return;
    setAdding(true);
    try {
      await api.asset.addToCanvas({
        project_id: projectId,
        asset_id: current.url,
        asset_type: active,
        url: current.url,
      });
      setAdded(true);
    } catch {
      setError('加入画布失败，请重试');
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="mt-5 border-t border-gray-800 pt-4">
      <OneClickGeneratedPreview result={current} addState={{ added, adding }} onAddToCanvas={current?.url ? handleAddToCanvas : undefined} />
      {error && <p className="mb-2 rounded bg-red-500/10 px-3 py-2 text-xs text-red-300">{error}</p>}
      <button data-oneclick-generate={active} onClick={generate} disabled={loading} className="w-full rounded-xl bg-orange-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-orange-500/20 transition hover:bg-orange-400 disabled:cursor-not-allowed disabled:opacity-60">
        {loading ? '生成中...' : active === 'video_scripts' ? '⚡ 一键生成脚本' : '⚡ 一键生成'}
      </button>
    </div>
  );
}

export default function ResultTabs({ plan, images, productName = '', projectId, uploadedProductUrl }: { plan: VisualAssetPlan; images?: ImagesData | null; productName?: string; projectId?: number; uploadedProductUrl?: string }) {
  const [active, setActive] = useState('main_image');
  const [generatedByTab, setGeneratedByTab] = useState<Record<string, OneClickResult>>({});
  const [refSource, setRefSource] = useState<RefSource>('none');

  // Derive reference image URLs
  const uploadedRefUrl = uploadedProductUrl || '';
  const mainImageRefUrl = images?.main_image?.url || '';
  const effectiveRefUrl = refSource === 'uploaded_product' ? uploadedRefUrl
    : refSource === 'generated_main_image' ? mainImageRefUrl
    : '';
  const activeTab = useMemo(() => TABS.find((tab) => tab.key === active), [active]);
  const render = () => {
    switch (active) {
      case 'main_image': return <MainImagePanel data={plan.main_image} image={images?.main_image} />;
      case 'white_bg': return <WhiteBgPanel data={plan.white_bg} />;
      case 'scene_images': return <ScenesPanel data={plan.scene_images} images={images?.scene_images} />;
      case 'selling_points': return <SellingPointsPanel data={plan.selling_points} />;
      case 'video_scripts': return <VideoScriptsPanel data={plan.video_scripts} />;
      case 'ad_material': return <AdMaterialPanel data={plan.ad_material} />;
      case 'layout': return <LayoutPanel layout={plan.layout_plan as any} />;
      default: return null;
    }
  };
  return (
    <div className="border border-gray-800 rounded-2xl overflow-hidden">
      <div className="flex border-b border-gray-800 bg-gray-900/50">
        {TABS.map(tab => <button key={tab.key} onClick={() => setActive(tab.key)} className={`flex-1 py-3 text-xs font-medium transition-colors ${active === tab.key ? 'text-orange-400 border-b-2 border-orange-500 bg-gray-900' : 'text-gray-500 hover:text-gray-300'}`}><span className="block">{tab.icon}</span>{tab.label}</button>)}
      </div>
      {/** Reference source selector - only for image-type tabs */}
      {activeTab && ['main_image', 'white_bg', 'scene_images', 'selling_points', 'ad_material', 'layout'].includes(active) && (
        <div className="flex items-center gap-2 border-b border-gray-800 bg-gray-900/30 px-4 py-2">
          <span className="text-[10px] text-gray-500 whitespace-nowrap">参考主体来源</span>
          <select
            value={resolvedRef}
            onChange={(e) => setRefSource(e.target.value)}
            className="flex-1 rounded-md border border-gray-700 bg-gray-900 px-2 py-1 text-[11px] text-gray-200 outline-none"
          >
            <option value="uploaded_product" disabled={!uploadedRefUrl}>使用我上传的产品图</option>
            <option value="generated_main_image" disabled={!mainImageRefUrl}>使用已生成的主图</option>
            <option value="none">不使用参考图（纯文本）</option>
          </select>
        </div>
      )}
      <div className="p-6 max-h-[600px] overflow-y-auto">
        {render()}
        {activeTab && <OneClickGenerateButton active={active} plan={plan} generatedByTab={generatedByTab} setGeneratedByTab={setGeneratedByTab} productName={productName} refSource={effectiveRefUrl} projectId={projectId} />}
        <span className="hidden">{TABS.length}</span>
      </div>
    </div>
  );
}
