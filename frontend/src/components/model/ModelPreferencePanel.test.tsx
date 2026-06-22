import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const source = fs.readFileSync(path.resolve(__dirname, 'ModelPreferencePanel.tsx'), 'utf8');
const generatePage = fs.readFileSync(path.resolve(__dirname, '../../pages/GeneratePage.tsx'), 'utf8');

describe('ModelPreferencePanel contract', () => {
  it('uses MOYAG inventory through selectableModels and never hardcodes Lovart models', () => {
    expect(source).toContain('selectableModels(models');
    expect(source).not.toMatch(/DEFAULT_MODELS|Lovart|lovart/i);
    expect(source).toContain('data-model-preference-panel');
  });

  it('supports image and video tabs with production inventory props', () => {
    expect(source).toContain("kind: 'image'");
    expect(source).toContain("kind: 'video'");
    expect(source).toContain('value: tab.kind');
    expect(source).toContain('ProviderInventoryItem');
  });

  it('keeps card selection and auto-model toggle controlled by parent state', () => {
    expect(source).toContain('setSelectedModel(modelId)');
    expect(source).toContain('setAutoModel');
    expect(source).toContain('selectedModel === modelId');
  });

  it('GeneratePage imports the extracted panel instead of defining it inline', () => {
    expect(generatePage).toContain("import ModelPreferencePanel from '../components/model/ModelPreferencePanel'");
    expect(generatePage).not.toContain('function ModelPreferencePanel');
  });
});
