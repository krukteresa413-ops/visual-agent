/**
 * useGenerationTask hook — unified async generation with SSE + polling fallback (Phase 0.4).
 *
 * Contract:
 *   1. Call generate() → get task_id
 *   2. Hook subscribes to SSE progress (preferred)
 *   3. Falls back to polling /unified/generation/task/{task_id} if SSE fails
 *   4. Returns { progress, status, result, error, generate }
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { api, getToken } from '../api/client';

export interface TaskProgress {
  percent: number;
  step: string;
  total_steps: number;
  done: boolean;
}

export interface TaskResult {
  status: 'idle' | 'processing' | 'complete' | 'error';
  progress: number;
  currentStep: string;
  result: Record<string, unknown> | null;
  error: string | null;
}

export function useGenerationTask() {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [state, setState] = useState<TaskResult>({
    status: 'idle',
    progress: 0,
    currentStep: '',
    result: null,
    error: null,
  });
  const abortRef = useRef<AbortController | null>(null);
  const pollRef = useRef<number | null>(null);

  // SSE subscription
  useEffect(() => {
    if (!taskId) return;

    const token = getToken();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setState(s => ({ ...s, status: 'processing', progress: 0 }));

    // Try SSE first
    const sseUrl = api.progress.streamUrl(taskId);

    fetch(sseUrl, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      signal: ctrl.signal,
    })
      .then(async (response) => {
        if (!response.ok || !response.body) throw new Error('SSE unavailable');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6)) as TaskProgress;
                setState(s => ({
                  ...s,
                  progress: data.percent,
                  currentStep: data.step,
                }));
              } catch { /* ignore parse errors */ }
            }
            if (line.startsWith('event: complete')) {
              setState(s => ({ ...s, status: 'complete', progress: 100 }));
              return;
            }
            if (line.startsWith('event: error')) {
              throw new Error('SSE error event');
            }
          }
        }
      })
      .catch(() => {
        // SSE failed → fallback to polling
        startPolling();
      });

    return () => {
      ctrl.abort();
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [taskId]);

  const startPolling = useCallback(() => {
    if (!taskId) return;

    pollRef.current = window.setInterval(async () => {
      try {
        const task = await api.generation.pollTask(taskId);
        if (task.status === 'complete') {
          setState(s => ({
            ...s,
            status: 'complete',
            progress: 100,
            result: task.generation || null,
          }));
          if (pollRef.current) clearInterval(pollRef.current);
        } else if (task.status === 'error') {
          setState(s => ({
            ...s,
            status: 'error',
            error: task.error || 'Unknown error',
          }));
          if (pollRef.current) clearInterval(pollRef.current);
        }
        // else: still processing, keep polling
      } catch {
        // polling error, keep retrying
      }
    }, 2000);
  }, [taskId]);

  const generate = useCallback(async (formData: FormData) => {
    setState({ status: 'processing', progress: 0, currentStep: '', result: null, error: null });
    try {
      const resp = await api.generation.generateAsync(formData);
      if (resp.task_id) {
        setTaskId(resp.task_id);
      }
      return resp;
    } catch (e) {
      setState(s => ({ ...s, status: 'error', error: String(e) }));
      throw e;
    }
  }, []);

  const reset = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
    if (pollRef.current) clearInterval(pollRef.current);
    setTaskId(null);
    setState({ status: 'idle', progress: 0, currentStep: '', result: null, error: null });
  }, []);

  return { ...state, generate, reset, taskId };
}
