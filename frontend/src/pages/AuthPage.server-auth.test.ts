import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';

const join = (...parts: string[]) => parts.join('');

describe('AuthPage server-backed auth contract', () => {
  const source = readFileSync(new URL('./AuthPage.tsx', import.meta.url), 'utf8');

  it('does not keep account archives in browser storage', () => {
    expect(source).not.toContain(join('moyag', '_', 'accounts'));
    expect(source).not.toContain(join('moyag', '_', 'current', '_', 'user'));
    expect(source).not.toContain(join('archive', 'Current', 'User', 'Data'));
    expect(source).not.toContain(join('load', 'Accounts'));
    expect(source).not.toContain(join('save', 'Accounts'));
  });

  it('loads current user from backend when a token exists', () => {
    expect(source).toContain(join('api', '.', 'auth', '.', 'me', '()'));
  });
});
