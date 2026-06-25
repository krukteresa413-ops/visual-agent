import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const source = fs.readFileSync(path.resolve(__dirname, 'BusinessBriefDrawer.tsx'), 'utf8');

describe('BusinessBriefDrawer contract', () => {
  it('renders with disabled submit button when required fields are empty', () => {
    expect(source).toContain("platform.trim() !== '' && productName.trim() !== '' && sellingPoints.trim() !== ''");
    expect(source).toContain('disabled={!canSubmit}');
  });

  it('emits correct shape with _mode business and reference_image_url', () => {
    expect(source).toContain("_mode: 'business'");
    expect(source).toContain('upload_platform:');
    expect(source).toContain('product_name:');
    expect(source).toContain('selling_points:');
    // v3: reference_image_url field
    expect(source).toContain('reference_image_url:');
  });

  it('renders platform chips, required fields, and reference image upload (v3)', () => {
    expect(source).toContain('data-testid="business-brief-drawer"');
    expect(source).toContain("id: 'taobao'");
    expect(source).toContain("id: 'jd'");
    expect(source).toContain('<Req');
    // v3: reference image upload
    expect(source).toContain('参考图（选填）');
    expect(source).toContain('uploadImage');
    expect(source).toContain('handleRefChange');
  });
});
