import type { ChatAssetEvent, ChatLifecycleEvent, ChatLifecyclePhase, MoyagProgressEvent } from './sseTypes';

function parseEvent(input: MoyagProgressEvent | string): MoyagProgressEvent | null {
  if (typeof input !== 'string') return input;
  try {
    return JSON.parse(input) as MoyagProgressEvent;
  } catch {
    return null;
  }
}

function phaseFor(event: MoyagProgressEvent): ChatLifecyclePhase {
  const detailPhase = typeof event.detail?.phase === 'string' ? event.detail.phase : '';
  if (detailPhase) return detailPhase;
  if (event.type === 'heartbeat') return 'heartbeat';
  if (event.type === 'done' || event.status === 'done') return 'completed';
  if (event.type === 'error' || event.status === 'error') return 'error';
  if (event.status === 'thinking') return 'thinking';
  if (event.status === 'evaluating') return 'evaluating';
  return 'streaming';
}

function assetTypeFrom(url: string, explicit?: unknown): ChatAssetEvent['type'] {
  if (explicit === 'image' || explicit === 'video' || explicit === 'asset') return explicit;
  if (/\.(mp4|webm|mov)(\?|$)/i.test(url)) return 'video';
  if (/\.(png|jpe?g|webp|gif)(\?|$)/i.test(url)) return 'image';
  return 'asset';
}

function extractAssets(detail: Record<string, unknown>): ChatAssetEvent[] {
  const url = detail.assetUrl || detail.asset_url || detail.url;
  if (typeof url !== 'string' || !url) return [];
  return [{ type: assetTypeFrom(url, detail.assetType || detail.asset_type), url }];
}

export function sseToChatEventAdapter(input: MoyagProgressEvent | string): ChatLifecycleEvent | null {
  const event = parseEvent(input);
  if (!event) return null;
  const detail = event.detail || {};
  return {
    type: String(event.type || 'progress'),
    phase: phaseFor(event),
    step: String(event.step || ''),
    percent: typeof event.percent === 'number' ? event.percent : 0,
    status: event.status || 'generating',
    message: String(event.message || ''),
    detail,
    assets: extractAssets(detail),
    terminalOnly: (event.type === 'done' || event.status === 'done') && !event.message && !event.step && extractAssets(detail).length === 0,
  };
}
