import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const source = fs.readFileSync(path.resolve(__dirname, 'primitives.tsx'), 'utf8');
const radixSwitch = fs.readFileSync(path.resolve(__dirname, '../ui/switch.tsx'), 'utf8');

describe('common primitives contract', () => {
  it('Switch delegates to radix with orange track', () => {
    expect(source).toContain('import { Switch as RadixSwitch }');
    expect(radixSwitch).toContain('bg-orange-500');
    expect(radixSwitch).toContain('bg-[#E5E7EB]');
  });

  it('SegmentedControl positions the indicator by selected index', () => {
    expect(source).toContain('export function SegmentedControl');
    expect(source).toContain('translateX(${selectedIndex * 100}%)');
  });

  it('Checkbox flips classes based on checked state', () => {
    expect(source).toContain('export function Checkbox');
    expect(source).toContain('aria-checked={checked}');
    expect(source).toContain("checked ? 'border-[#2F3640] bg-[#2F3640]'");
  });

  it('IconButton keeps icon-only controls accessible', () => {
    expect(source).toContain('export function IconButton');
    expect(source).toContain('aria-label={label}');
  });
});
