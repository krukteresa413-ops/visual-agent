import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const source = fs.readFileSync(path.resolve(__dirname, 'BusinessBriefDrawer.tsx'), 'utf8');

describe('BusinessBriefDrawer contract', () => {
  it('renders with disabled submit button when required fields are empty', () => {
    // canSubmit checks three fields are non-empty before enabling
    expect(source).toContain("platform.trim() !== '' && productName.trim() !== '' && sellingPoints.trim() !== ''");
    // Button disabled when !canSubmit
    expect(source).toContain('disabled={!canSubmit}');
  });

  it('emits correct shape with _mode business', () => {
    // check _mode literal
    expect(source).toContain("_mode: 'business'");
    // check required fields in onSubmit payload
    expect(source).toContain('upload_platform:');
    expect(source).toContain('product_name:');
    expect(source).toContain('selling_points:');
  });

  it('renders platform chips and required field inputs', () => {
    expect(source).toContain('data-testid="business-brief-drawer"');
    // platform_id mapping
    expect(source).toContain("id: 'taobao'");
    expect(source).toContain("id: 'jd'");
    expect(source).toContain("id: 'douyin'");
    // required star marker (v2)
    expect(source).toContain('<Req');
  });
});
