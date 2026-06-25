import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

const source = fs.readFileSync(path.resolve(__dirname, 'AIChatPanel.tsx'), 'utf8');
const generatePage = fs.readFileSync(path.resolve(__dirname, '../pages/GeneratePage.tsx'), 'utf8');

describe('AIChatPanel LS2 composer contract', () => {
  it('uses a Lovart-style composer textarea with Enter submit and Shift+Enter newline', () => {
    expect(source).toContain('data-lovart-composer');
    expect(source).toContain('<textarea');
    expect(source).toContain("e.key === 'Enter'");
    expect(source).toContain('!e.shiftKey');
    expect(source).toContain('handleSubmit()');
  });

  it('renders the six composer tool positions', () => {
    for (const marker of [
      'data-composer-tool="upload"',
      'data-composer-tool="library"',
      'data-composer-tool="agent"',
      'data-composer-tool="inspiration"',
      'data-composer-tool="model"',
      'data-composer-tool="send"',
    ]) {
      expect(source).toContain(marker);
    }
    expect(source).toContain('disabled');
  });

  it('opens the LS2 model preference panel from the model tool', () => {
    expect(source).toContain('ModelPreferencePanel');
    expect(source).toContain('setShowModelPanel');
    expect(source).toContain('data-composer-model-panel');
  });

  it('has library tool with onSkillsOpen and inspiration still disabled (Part 2)', () => {
    // library icon opens Skills popup
    expect(source).toContain('data-composer-tool="library"');
    expect(source).toContain('onClick={onSkillsOpen}');
    expect(source).toContain('title="素材库"');
    // inspiration/lightbulb still disabled (Part 2 preserves old state)
    expect(source).toContain('data-composer-tool="inspiration"');
    expect(source).toContain('disabled');
  });

  it('keeps SkillsPopup anchored width isolated', () => {
    const skillsPopup = fs.readFileSync(path.resolve(__dirname, 'SkillsPopup.tsx'), 'utf8');
    expect(skillsPopup).toContain("anchorEl ? 'fixed z-[100] w-[280px]' : 'relative z-30 w-full'");
    expect(skillsPopup).not.toContain('border border-black/10 w-full max-h');
  });

  it('has business mode toggle and runGeneration wired (Part 2)', () => {
    expect(source).toContain("'quick' | 'business'");
    expect(source).toContain('setGenMode');
    expect(source).toContain('runGeneration');
    expect(source).toContain('uploadReferenceImage');
  });

  it('keeps existing agent mode switching behavior', () => {
    expect(source).toContain("type AgentMode = 'agent' | 'image-gen' | 'video-gen'");
    expect(source).toContain('setAgentMode(mode.id as AgentMode)');
  });

  it('does not change the current full-height right panel positioning in GeneratePage', () => {
    expect(generatePage).toContain('data-right-panel-overlay');
    expect(generatePage).toContain('absolute right-0 top-0 bottom-0');
    expect(generatePage).toContain('w-[399px]');
  });

  it('routes existing SSE events through adapter and chatReducer while keeping polling fallback', () => {
    expect(source).toContain('useReducer');
    expect(source).toContain('chatReducer');
    expect(source).toContain('sseToChatEventAdapter');
    expect(source).toContain("dispatch({ type: 'sse'");
    expect(source).toContain('startPolling()');
    expect(source).toContain('api.progress.streamUrl(taskId)');
  });
});
