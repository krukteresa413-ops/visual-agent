import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const source = fs.readFileSync(path.resolve(__dirname, 'Layout.tsx'), 'utf8');

describe('Layout global theme toggle contract', () => {
  it('reuses the existing ThemeToggle hook/component in the global non-canvas nav', () => {
    expect(source).toContain("import ThemeToggle, { useTheme } from './ThemeToggle'");
    expect(source).toContain('const { isLight, toggle } = useTheme();');
    expect(source).toContain('<ThemeToggle isLight={isLight} toggle={toggle} />');
  });

  it('keeps canvas workspace nav hidden while adding the toggle beside the brand label', () => {
    expect(source).toContain("const isCanvasWorkspace = pathname.startsWith('/generate/')");
    expect(source).toMatch(/<span className="text-xs text-gray-600">MOYAG · Agent Canvas<\/span>[\s\S]*?<ThemeToggle isLight=\{isLight\} toggle=\{toggle\} \/>/);
  });
});
