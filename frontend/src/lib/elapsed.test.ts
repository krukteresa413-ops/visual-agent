import { describe, expect, it } from 'vitest';
import { formatElapsedSeconds } from './elapsed';

describe('formatElapsedSeconds', () => {
  it('formats elapsed duration instead of returning a Unix timestamp', () => {
    const now = 1_781_969_391_000;

    expect(formatElapsedSeconds(now - 44_000, now)).toBe('44s');
    expect(formatElapsedSeconds(0, now)).not.toBe('1781969391s');
  });
});
