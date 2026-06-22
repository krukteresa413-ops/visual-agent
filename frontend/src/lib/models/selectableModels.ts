export type ProviderInventoryItem = {
  modelKey: string;
  provider: string;
  modality: 'image' | 'video';
  displayName?: string;
  notes?: string | null;
  available: boolean;
  configured?: boolean;
  source: 'production' | 'benchmark' | 'experimental' | 'local';
  productionUsable: boolean;
};

export function selectableModels(items: ProviderInventoryItem[] = [], modality?: 'image' | 'video') {
  return items.filter((item) => {
    if (modality && item.modality !== modality) return false;
    return item.source === 'production' && item.available && item.productionUsable;
  });
}
