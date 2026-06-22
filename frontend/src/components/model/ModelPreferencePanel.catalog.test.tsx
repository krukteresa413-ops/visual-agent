import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const panel = fs.readFileSync(path.resolve(__dirname, 'ModelPreferencePanel.tsx'), 'utf8');
const page = fs.readFileSync(path.resolve(__dirname, '../../pages/GeneratePage.tsx'), 'utf8');
const client = fs.readFileSync(path.resolve(__dirname, '../../api/client.ts'), 'utf8');

describe('catalog-driven Lovart style model selector', () => {
  it('fetches the curated models catalog instead of only provider inventory', () => {
    expect(client).toContain("/models/catalog");
    expect(page).toContain('api.generation.catalog');
  });

  it('renders category to model two-level menu tokens', () => {
    expect(panel).toContain('data-model-category-menu');
    expect(panel).not.toContain('data-model-category-item');
    expect(panel).toContain('data-model-catalog-card');
    expect(panel).toContain('model.tags');
  });

  it('renders catalog-driven video params without enabling unavailable providers', () => {
    expect(panel).toContain('resolution');
    expect(panel).toContain('ratio');
    expect(panel).toContain('duration');
    expect(panel).toContain('first_frame_url');
  });
});
