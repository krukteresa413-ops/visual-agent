import { useCallback, useRef, useState } from 'react';
import type { Edge, Node, Viewport } from '@xyflow/react';
import { api } from '../api/client';
import { flowToLegacyCanvas } from './canvasAdapters';
import type { FlowCanvasEdgeData, FlowCanvasNodeData } from './canvasTypes';

type SaveStatus = 'idle' | 'saving' | 'saved' | 'error';

interface SaveCanvasArgs {
  nodes: Array<Node<FlowCanvasNodeData>>;
  edges: Array<Edge<FlowCanvasEdgeData>>;
  viewport: Viewport;
}

export function useCanvasPersistence(projectId: number) {
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle');
  const lastPayloadRef = useRef('');

  const saveCanvas = useCallback(async ({ nodes, edges, viewport }: SaveCanvasArgs) => {
    const legacy = flowToLegacyCanvas({ nodes, edges, viewport });
    const payload = JSON.stringify(legacy);
    if (payload === lastPayloadRef.current) {
      setSaveStatus('saved');
      return legacy;
    }

    setSaveStatus('saving');
    try {
      await api.atelierCanvas.saveState(projectId, legacy as unknown as Record<string, unknown>);
      lastPayloadRef.current = payload;
      setSaveStatus('saved');
      return legacy;
    } catch (error) {
      setSaveStatus('error');
      throw error;
    }
  }, [projectId]);

  const rememberSavedCanvas = useCallback(({ nodes, edges, viewport }: SaveCanvasArgs) => {
    lastPayloadRef.current = JSON.stringify(flowToLegacyCanvas({ nodes, edges, viewport }));
    setSaveStatus('saved');
  }, []);

  return { saveCanvas, saveStatus, rememberSavedCanvas };
}
