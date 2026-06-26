export type MoyagProgressStatus = 'thinking' | 'generating' | 'evaluating' | 'done' | 'error' | string;

export type MoyagProgressEvent = {
  type?: 'progress' | 'heartbeat' | 'done' | 'error' | string;
  step?: string;
  percent?: number;
  status?: MoyagProgressStatus;
  message?: string;
  detail?: Record<string, unknown>;
};

export type ChatLifecyclePhase =
  | 'thinking'
  | 'streaming'
  | 'evaluating'
  | 'completed'
  | 'error'
  | 'heartbeat'
  | string;

export type ChatAssetEvent = {
  type: 'image' | 'video' | 'asset';
  url: string;
};

export type ChatLifecycleEvent = {
  type: string;
  phase: ChatLifecyclePhase;
  step: string;
  percent: number;
  status: MoyagProgressStatus;
  message: string;
  detail: Record<string, unknown>;
  assets: ChatAssetEvent[];
  terminalOnly?: boolean;
};
