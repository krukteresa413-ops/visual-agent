import { describe, expect, it } from 'vitest';
import { loTokens } from './tokens';

describe('loTokens', () => {
  it('exposes LS2 shell color tokens', () => {
    expect(loTokens.colors.title).toBe('#2F3640');
    expect(loTokens.colors.canvas).toBe('#F5F5F5');
    expect(loTokens.colors.cardDescription).toBe('#4A535F');
    expect(loTokens.colors.tabBackground).toBe('#F1F3F5');
    expect(loTokens.colors.selected).toBe('#E5E6EC');
  });

  it('exposes shell dimensions and elevation', () => {
    expect(loTokens.layout.rightPanelWidth).toBe(399);
    expect(loTokens.layout.topbarHeight).toBe(48);
    expect(loTokens.shadow.elevation100).toBe('0 2px 8px rgba(0,0,0,.15)');
  });
});
