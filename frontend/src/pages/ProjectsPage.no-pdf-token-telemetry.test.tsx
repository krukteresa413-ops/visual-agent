import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const source = readFileSync(resolve(__dirname, 'ProjectsPage.tsx'), 'utf-8');

describe('ProjectsPage has no PDF token telemetry in product UI', () => {
  it('does not render developer token-saving badge/state on the homepage', () => {
    expect(source).not.toContain('pdfTokenMetrics');
    expect(source).not.toContain('Token节省');
    expect(source).not.toContain('text_prefilter_metrics');
  });
});
