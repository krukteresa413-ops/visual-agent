import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('./CanvasViewLegacy.tsx', import.meta.url), 'utf8');

describe('CanvasViewLegacy prompt history trace contract', () => {
  it('turns the bottom trace into prompt history with edit reuse actions', () => {
    expect(source).toContain('data-prompt-history-panel="true"');
    expect(source).toContain('Prompt历史');
    expect(source).toContain('onEditPrompt');
    expect(source).toContain('record.prompt');
    expect(source).toContain('二次修改');
  });

  it('wires prompt history edits back into the canvas page quick prompt input', () => {
    expect(source).toContain('onEditPrompt?: (prompt: string) => void');
    expect(source).toContain('onEditPrompt?.(record.prompt)');
  });
});
