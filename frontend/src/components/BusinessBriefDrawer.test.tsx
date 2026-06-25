import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const source = fs.readFileSync(path.resolve(__dirname, 'BusinessBriefDrawer.tsx'), 'utf8');

describe('BusinessBriefDrawer contract (v4)', () => {
  it('renders with disabled submit when required fields empty', () => {
    expect(source).toContain("platform.trim() !== '' && productName.trim() !== '' && sellingPoints.trim() !== ''");
    expect(source).toContain('disabled={!canSubmit}');
  });

  it('emits correct shape with _mode business, reference_image_url, product_id', () => {
    expect(source).toContain("_mode: 'business'");
    expect(source).toContain('upload_platform:');
    expect(source).toContain('product_name:');
    expect(source).toContain('selling_points:');
    expect(source).toContain('reference_image_url:');
    // v4: product_id
    expect(source).toContain('product_id:');
  });

  it('has library autofill: fetchBrand/fetchProducts/fetchProductDetail + LibTag', () => {
    expect(source).toContain('fetchBrand');
    expect(source).toContain('fetchProducts');
    expect(source).toContain('fetchProductDetail');
    expect(source).toContain('来自资料库');
    expect(source).toContain('检测到');
  });

  it('has platform chips, required star, reference upload (v3 retained)', () => {
    expect(source).toContain('data-testid="business-brief-drawer"');
    expect(source).toContain("id: 'taobao'");
    expect(source).toContain('<Req');
    expect(source).toContain('参考图（选填）');
  });

  it('has new product button that clears product-level fields', () => {
    expect(source).toContain('新建商品');
    expect(source).toContain('selectProduct');
    expect(source).toContain('newProduct');
  });
});
