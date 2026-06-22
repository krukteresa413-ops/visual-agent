import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const panel = fs.readFileSync(path.resolve(__dirname, 'ModelPreferencePanel.tsx'), 'utf8');

describe('ModelPreferencePanel catalog fix contract', () => {
  it('keeps only the segmented tab control and removes duplicate static category chips', () => {
    expect(panel).toContain('data-model-category-menu');
    expect(panel).not.toContain('mt-2 flex gap-1.5 text-[10px] text-[#4A535F]');
    expect(panel).not.toContain('data-model-category-item');
  });

  it('derives visible categories from catalog keys with non-empty arrays', () => {
    expect(panel).toContain('visibleCategories');
    expect(panel).toContain('Object.entries');
    expect(panel).toContain('Array.isArray(models) && models.length > 0');
  });

  it('does not hard-code the 3D tab into fallback tabs', () => {
    expect(panel).toContain("{ kind: 'image', label: '图片' }");
    expect(panel).toContain("{ kind: 'video', label: '视频' }");
    expect(panel).not.toContain("{ kind: '3d', label: '3D' }");
  });
});
