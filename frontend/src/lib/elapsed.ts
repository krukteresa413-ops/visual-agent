export function formatElapsedSeconds(startTimestampMs: number, nowTimestampMs: number): string {
  if (!Number.isFinite(startTimestampMs) || startTimestampMs <= 0) return '?s';
  return `${Math.max(0, Math.floor((nowTimestampMs - startTimestampMs) / 1000))}s`;
}
