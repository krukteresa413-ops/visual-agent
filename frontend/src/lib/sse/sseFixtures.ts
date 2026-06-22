import type { MoyagProgressEvent } from './sseTypes';

export function progressEvent(overrides: Partial<MoyagProgressEvent> = {}): MoyagProgressEvent {
  return {
    type: 'progress',
    step: '分析需求',
    percent: 12,
    status: 'thinking',
    message: '正在分析',
    detail: {},
    ...overrides,
  };
}

export function doneEvent(overrides: Partial<MoyagProgressEvent> = {}): MoyagProgressEvent {
  return progressEvent({ type: 'done', step: '完成', percent: 100, status: 'done', message: '完成', ...overrides });
}

export function errorEvent(message = '生成失败', overrides: Partial<MoyagProgressEvent> = {}): MoyagProgressEvent {
  return progressEvent({ type: 'error', step: '出错', percent: 0, status: 'error', message, ...overrides });
}

export function heartbeatEvent(overrides: Partial<MoyagProgressEvent> = {}): MoyagProgressEvent {
  return progressEvent({ type: 'heartbeat', step: 'heartbeat', percent: 0, status: 'thinking', message: 'heartbeat', ...overrides });
}
