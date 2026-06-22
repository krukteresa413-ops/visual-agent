import { describe, expect, it } from 'vitest';
import { selectableModels, type ProviderInventoryItem } from './selectableModels';

const item = (overrides: Partial<ProviderInventoryItem>): ProviderInventoryItem => ({
  modelKey: 'dataeyes:image',
  provider: 'dataeyes',
  modality: 'image',
  displayName: 'DataEyes',
  available: true,
  configured: true,
  source: 'production',
  productionUsable: true,
  ...overrides,
});

describe('selectableModels', () => {
  it('keeps only available production usable models', () => {
    const result = selectableModels([
      item({ modelKey: 'dataeyes:image' }),
      item({ modelKey: 'lovart:image', provider: 'lovart', source: 'benchmark', productionUsable: false }),
      item({ modelKey: 'mige:image', provider: 'mige', available: false, productionUsable: false }),
    ]);

    expect(result.map((model) => model.modelKey)).toEqual(['dataeyes:image']);
  });

  it('filters by modality', () => {
    const result = selectableModels([
      item({ modelKey: 'dataeyes:image', modality: 'image' }),
      item({ modelKey: 'runway:video', provider: 'runway', modality: 'video' }),
    ], 'video');

    expect(result.map((model) => model.modelKey)).toEqual(['runway:video']);
  });
});
