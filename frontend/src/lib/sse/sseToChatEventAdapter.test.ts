import { describe, expect, it } from 'vitest';
import { sseToChatEventAdapter } from './sseToChatEventAdapter';
import { progressEvent, doneEvent, errorEvent, heartbeatEvent } from './sseFixtures';

describe('sseToChatEventAdapter', () => {
  it('maps thinking progress to lifecycle thinking', () => {
    expect(sseToChatEventAdapter(progressEvent({ status: 'thinking' })).phase).toBe('thinking');
  });

  it('maps generating progress to streaming', () => {
    expect(sseToChatEventAdapter(progressEvent({ status: 'generating' })).phase).toBe('streaming');
  });

  it('maps evaluating progress to evaluating', () => {
    expect(sseToChatEventAdapter(progressEvent({ status: 'evaluating' })).phase).toBe('evaluating');
  });

  it('maps done event to completed', () => {
    const event = sseToChatEventAdapter(doneEvent());
    expect(event.phase).toBe('completed');
    expect(event.percent).toBe(100);
  });

  it('maps error event to error phase', () => {
    expect(sseToChatEventAdapter(errorEvent('bad')).phase).toBe('error');
  });

  it('maps heartbeat to heartbeat phase', () => {
    expect(sseToChatEventAdapter(heartbeatEvent()).phase).toBe('heartbeat');
  });

  it('preserves detail.phase when provided', () => {
    expect(sseToChatEventAdapter(progressEvent({ detail: { phase: 'routing' } })).phase).toBe('routing');
  });

  it('preserves step, message and percent', () => {
    const event = sseToChatEventAdapter(progressEvent({ step: '策略规划', percent: 33, message: '规划中' }));
    expect(event.step).toBe('策略规划');
    expect(event.message).toBe('规划中');
    expect(event.percent).toBe(33);
  });

  it('extracts image asset urls from detail', () => {
    const event = sseToChatEventAdapter(progressEvent({ detail: { assetUrl: '/uploads/a.png', assetType: 'image' } }));
    expect(event.assets).toEqual([{ type: 'image', url: '/uploads/a.png' }]);
  });

  it('extracts video asset urls from detail', () => {
    const event = sseToChatEventAdapter(progressEvent({ detail: { assetUrl: '/uploads/a.mp4', assetType: 'video' } }));
    expect(event.assets).toEqual([{ type: 'video', url: '/uploads/a.mp4' }]);
  });

  it('normalizes unknown status to streaming for progress events', () => {
    expect(sseToChatEventAdapter(progressEvent({ status: 'custom' })).phase).toBe('streaming');
  });

  it('parses raw SSE data JSON strings', () => {
    expect(sseToChatEventAdapter(JSON.stringify(doneEvent())).phase).toBe('completed');
  });

  it('returns null for invalid JSON strings', () => {
    expect(sseToChatEventAdapter('{bad json')).toBeNull();
  });
});
