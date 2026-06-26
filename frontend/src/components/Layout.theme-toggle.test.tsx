import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const source = fs.readFileSync(path.resolve(__dirname, 'Layout.tsx'), 'utf8');

describe('Layout global top nav contract', () => {
  it('reuses the existing ThemeToggle hook/component in the global non-canvas nav', () => {
    expect(source).toContain("import ThemeToggle, { useTheme } from './ThemeToggle'");
    expect(source).toContain('const { isLight, toggle } = useTheme();');
    expect(source).toContain('<ThemeToggle isLight={isLight} toggle={toggle} />');
  });

  it('keeps the canvas workspace nav hidden', () => {
    expect(source).toContain("const isCanvasWorkspace = pathname.startsWith('/generate/')");
  });

  it('renders the reference-style brand logo and the mapped tabs', () => {
    expect(source).toContain('MOYAG');
    expect(source).toContain('AGENT CANVAS');
    expect(source).toContain("{ to: '/prompts', label: '创意脚本库' }");
    expect(source).toContain("{ to: '/inspiration', label: '灵感源' }");
  });

  it('wires the new-project button to create a project then open its canvas', () => {
    expect(source).toContain("api.projects.create('未命名项目', '')");
    expect(source).toContain('navigate(`/generate/${project.id}`)');
  });
});
