import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const panel = fs.readFileSync(path.resolve(__dirname, 'ModelPreferencePanel.tsx'), 'utf8');
const radixSwitch = fs.readFileSync(path.resolve(__dirname, '../ui/switch.tsx'), 'utf8');
const registry = fs.readFileSync(path.resolve(__dirname, '../../../../app/backend/app/config/model_registry.py'), 'utf8');

describe('ModelPreferencePanel round 2 fixes', () => {
  it('uses orange switch track for auto model on state and grey for off state', () => {
    expect(radixSwitch).toContain('bg-orange-500');
    expect(radixSwitch).toContain('bg-[#E5E7EB]');
    expect(radixSwitch).not.toContain("checked ? 'bg-[#2F3640]'");
  });

  it('shows auto mode explanation when model cards are disabled by auto selection', () => {
    expect(panel).toContain('已开启自动选择');
    expect(panel).toContain('系统将按任务自动挑选模型');
  });

  it('deduplicates GPT image variants in enabled catalog', () => {
    expect(registry).toContain('"id": "gpt-image-2"');
    expect(registry).toContain('"id": "gpt-image-1-sp"');
    expect(registry).toContain('"id": "gpt-image-1.5-sp"');
    expect(registry).toContain('"enabled": False');
    expect(registry).toContain('"id": "gpt-image-2-sp"');
  });
});
