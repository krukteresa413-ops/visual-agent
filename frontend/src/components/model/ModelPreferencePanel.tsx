import { SegmentedControl, Switch } from '../common/primitives';
import { selectableModels, type ProviderInventoryItem } from '../../lib/models/selectableModels';

type ModelKind = 'image' | 'video' | '3d';

type CatalogModel = {
  id: string;
  name: string;
  category: ModelKind;
  format?: string;
  vendor?: string;
  async?: boolean;
  params?: string[];
  tags?: string[];
  enabled?: boolean;
};

type ModelsData = {
  tabs?: Array<{ kind: ModelKind; label: string }>;
  models?: ProviderInventoryItem[];
  image?: CatalogModel[];
  video?: CatalogModel[];
};

type Props = {
  isOpen: boolean;
  onToggle: () => void;
  modelsData?: ModelsData;
  activeKind: ModelKind;
  setActiveKind: (kind: ModelKind) => void;
  autoModel: boolean;
  setAutoModel: (value: boolean) => void;
  selectedModel: string | null;
  setSelectedModel: (modelKey: string) => void;
};

const fallbackTabs: Array<{ kind: ModelKind; label: string }> = [
  { kind: 'image', label: '图片' },
  { kind: 'video', label: '视频' },
];

const catalogLabels: Record<ModelKind, string> = {
  image: '图片',
  video: '视频',
  '3d': '3D',
};

const PARAM_LABELS: Record<string, string> = {
  size: 'size',
  n: 'n',
  resolution: 'resolution',
  ratio: 'ratio',
  duration: 'duration',
  first_frame_url: 'first_frame_url',
};

function catalogModels(data: ModelsData | undefined, kind: ModelKind): CatalogModel[] {
  if (kind === 'image') return Array.isArray(data?.image) ? data.image : [];
  if (kind === 'video') return Array.isArray(data?.video) ? data.video : [];
  return [];
}

function catalogTabs(data: ModelsData | undefined): Array<{ kind: ModelKind; label: string }> {
  const entries = Object.entries(data || {}).filter((entry): entry is [ModelKind, CatalogModel[]] => {
    const [kind, models] = entry;
    return ['image', 'video', '3d'].includes(kind) && Array.isArray(models) && models.length > 0;
  });
  return entries.map(([kind]) => ({ kind, label: catalogLabels[kind] }));
}

export default function ModelPreferencePanel({
  isOpen,
  onToggle,
  modelsData,
  activeKind,
  setActiveKind,
  autoModel,
  setAutoModel,
  selectedModel,
  setSelectedModel,
}: Props) {
  const visibleCategories = catalogTabs(modelsData);
  const tabs = visibleCategories.length > 0 ? visibleCategories : (modelsData?.tabs || fallbackTabs);
  const currentKind = tabs.some((tab) => tab.kind === activeKind) ? activeKind : tabs[0]?.kind || 'image';
  const catalog = catalogModels(modelsData, currentKind);
  const inventoryModels = selectableModels(modelsData?.models || [], currentKind === 'video' ? 'video' : 'image');
  const options = tabs.map((tab) => ({ value: tab.kind, label: tab.label || catalogLabels[tab.kind] }));
  const hasCatalog = catalog.length > 0;

  return (
    <div data-model-preference-panel className="overflow-hidden rounded-lo border border-black/10 bg-white text-[#2F3640] shadow-lo-elevation-100">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between px-3 py-2 text-xs text-[#2F3640] transition-colors hover:bg-[#F1F3F5]"
      >
        <span>模型偏好</span>
        <span className="text-[#4A535F]">{isOpen ? '收起' : '展开'}</span>
      </button>
      {isOpen && (
        <div className="space-y-3 border-t border-black/10 p-3">
          <div data-model-category-menu>
            <SegmentedControl options={options} value={currentKind} onChange={setActiveKind} />
          </div>
          <label className="flex items-center justify-between text-xs text-[#2F3640]">
            <span>自动选择模型</span>
            <Switch checked={autoModel} onCheckedChange={setAutoModel} label="自动选择模型" />
          </label>
          {autoModel && (
            <p className="rounded-md bg-orange-50 px-2 py-1 text-[10px] text-orange-600">
              已开启自动选择，系统将按任务自动挑选模型。
            </p>
          )}
          <div className="max-h-56 space-y-2 overflow-y-auto pr-1">
            {hasCatalog ? catalog.slice(0, 12).map((model) => {
              const isVideo = currentKind === 'video';
              const disabled = !model.enabled;
              const selected = selectedModel === model.id;
              return (
                <button
                  key={model.id}
                  data-model-card={model.id}
                  data-model-catalog-card={model.id}
                  data-model-unavailable={!model.enabled}
                  type="button"
                  disabled={disabled || autoModel}
                  onClick={() => setSelectedModel(model.id)}
                  className={`w-full rounded-md border p-2 text-left text-[11px] transition-colors ${selected && !autoModel ? 'border-[#2F3640] bg-[#E5E6EC] text-[#2F3640]' : 'border-black/10 bg-white text-[#2F3640]'} ${disabled || autoModel ? 'cursor-not-allowed opacity-60' : 'hover:bg-[#F1F3F5]'}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate">{model.name || model.id}</span>
                    {isVideo && <span className="text-[10px] text-orange-500">视频</span>}
                  </div>
                  <p className="mt-1 truncate text-[10px] text-[#4A535F]">{(model.tags || []).join(' · ') || model.vendor || model.format}</p>
                  {Array.isArray(model.params) && model.params.length > 0 && (
                    <p className="mt-1 truncate text-[10px] text-[#7A828C]">参数: {model.params.map((param) => PARAM_LABELS[param] || param).join(' / ')}</p>
                  )}
                </button>
              );
            }) : inventoryModels.slice(0, 12).map((model) => {
              const modelId = model.modelKey;
              const disabled = !model.available || !model.productionUsable;
              const selected = selectedModel === modelId;
              return (
                <button
                  key={modelId}
                  data-model-card={modelId}
                  data-model-unavailable={!model.available}
                  type="button"
                  disabled={disabled || autoModel}
                  onClick={() => setSelectedModel(modelId)}
                  className={`w-full rounded-md border p-2 text-left text-[11px] transition-colors ${selected && !autoModel ? 'border-[#2F3640] bg-[#E5E6EC] text-[#2F3640]' : 'border-black/10 bg-white text-[#2F3640]'} ${disabled || autoModel ? 'cursor-not-allowed opacity-60' : 'hover:bg-[#F1F3F5]'}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate">{model.displayName || modelId}</span>
                    {!model.available && <span className="text-[#4A535F]">未接入</span>}
                  </div>
                  <p className="mt-1 truncate text-[10px] text-[#4A535F]">{model.notes || model.provider}</p>
                </button>
              );
            })}
            {!hasCatalog && inventoryModels.length === 0 && <p className="text-[11px] text-[#4A535F]">未接入</p>}
          </div>
        </div>
      )}
    </div>
  );
}
