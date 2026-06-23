import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const indexHtml = fs.readFileSync(path.resolve(__dirname, '../index.html'), 'utf8');

describe('light theme bootstrap contract', () => {
  it('loads theme-light.css and synchronously applies saved light mode before the app bundle', () => {
    const cssIndex = indexHtml.indexOf('id="theme-style"');
    const scriptIndex = indexHtml.indexOf("localStorage.getItem('moyag-theme')");
    const moduleIndex = indexHtml.indexOf('type="module"');

    expect(cssIndex).toBeGreaterThan(-1);
    expect(scriptIndex).toBeGreaterThan(cssIndex);
    expect(scriptIndex).toBeLessThan(moduleIndex);
    expect(indexHtml).toContain("document.documentElement.classList.add('light')");
    expect(indexHtml).not.toContain('data-theme');
  });
});
