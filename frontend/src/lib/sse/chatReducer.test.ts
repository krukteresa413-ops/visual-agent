import { describe, expect, it } from 'vitest';
import { chatReducer, initialChatState, type ChatMessage } from './chatReducer';
import { sseToChatEventAdapter } from './sseToChatEventAdapter';
import { doneEvent, errorEvent, heartbeatEvent, progressEvent } from './sseFixtures';

describe('chatReducer', () => {
  it('starts in idle', () => {
    expect(initialChatState.phase).toBe('idle');
    expect(initialChatState.messages).toEqual([]);
  });

  it('moves to submitting and appends the user prompt', () => {
    const state = chatReducer(initialChatState, { type: 'submit', prompt: '生成一张主图' });
    expect(state.phase).toBe('submitting');
    expect(state.messages.at(-1)?.role).toBe('user');
  });

  it('maps thinking events to an assistant lifecycle message', () => {
    const state = chatReducer(initialChatState, { type: 'sse', event: sseToChatEventAdapter(progressEvent({ status: 'thinking' }))! });
    expect(state.phase).toBe('thinking');
    expect(state.messages.at(-1)?.status).toBe('thinking');
  });

  it('maps generating events to streaming', () => {
    const state = chatReducer(initialChatState, { type: 'sse', event: sseToChatEventAdapter(progressEvent({ status: 'generating', percent: 55 }))! });
    expect(state.phase).toBe('streaming');
    expect(state.percent).toBe(55);
  });

  it('maps evaluating events to evaluating', () => {
    const state = chatReducer(initialChatState, { type: 'sse', event: sseToChatEventAdapter(progressEvent({ status: 'evaluating' }))! });
    expect(state.phase).toBe('evaluating');
  });

  it('maps done events to completed', () => {
    const state = chatReducer(initialChatState, { type: 'sse', event: sseToChatEventAdapter(doneEvent())! });
    expect(state.phase).toBe('completed');
    expect(state.percent).toBe(100);
  });

  it('does not append a synthetic completion bubble for message-less conversational done events', () => {
    const submitted = chatReducer(initialChatState, { type: 'submit', prompt: '只回复一句你好' });
    const state = chatReducer(submitted, { type: 'sse', event: sseToChatEventAdapter({ type: 'done', status: 'done' })! });
    expect(state.phase).toBe('completed');
    expect(state.percent).toBe(100);
    expect(state.messages).toHaveLength(1);
    expect(state.messages.at(-1)?.role).toBe('user');
  });

  it('maps errors to error phase', () => {
    const state = chatReducer(initialChatState, { type: 'sse', event: sseToChatEventAdapter(errorEvent('失败'))! });
    expect(state.phase).toBe('error');
    expect(state.error).toBe('失败');
  });

  it('ignores heartbeat without appending messages', () => {
    const state = chatReducer(initialChatState, { type: 'sse', event: sseToChatEventAdapter(heartbeatEvent())! });
    expect(state.messages).toEqual([]);
  });

  it('attaches assets to assistant messages', () => {
    const state = chatReducer(initialChatState, { type: 'sse', event: sseToChatEventAdapter(progressEvent({ detail: { assetUrl: '/uploads/a.png', assetType: 'image' } }))! });
    expect(state.messages.at(-1)?.assets).toEqual([{ type: 'image', url: '/uploads/a.png' }]);
  });


  it('records explicit assistant status messages for polling fallback', () => {
    const state = chatReducer(initialChatState, { type: 'assistantStatus', step: '完成', content: '通过轮询完成', status: 'completed', percent: 100 });
    expect(state.phase).toBe('completed');
    expect(state.messages.at(-1)?.content).toBe('通过轮询完成');
  });

  it('supports reset', () => {
    const dirty = chatReducer(initialChatState, { type: 'submit', prompt: 'x' });
    expect(chatReducer(dirty, { type: 'reset' })).toEqual(initialChatState);
  });

  it('hydrates persisted history into messages without entering an in-progress phase (图三)', () => {
    const persisted: ChatMessage[] = [
      { id: '1', role: 'user', step: '用户指令', content: '生成一台冰箱', status: 'user', percent: 0, assets: [] },
      { id: '2', role: 'assistant', step: '完成', content: '生成完成', status: 'completed', percent: 100, assets: [{ type: 'image', url: '/uploads/x.png' }] },
    ];
    const state = chatReducer(initialChatState, { type: 'hydrate', messages: persisted });
    expect(state.phase).toBe('idle');
    expect(state.messages).toHaveLength(2);
    expect(state.messages[0].role).toBe('user');
    expect(state.messages.at(-1)?.assets).toEqual([{ type: 'image', url: '/uploads/x.png' }]);
  });
});
