import type { ChatAssetEvent, ChatLifecycleEvent } from './sseTypes';

export type ChatPhase = 'idle' | 'submitting' | 'thinking' | 'streaming' | 'evaluating' | 'completed' | 'error';

export type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  step: string;
  content: string;
  status: string;
  percent: number;
  assets: ChatAssetEvent[];
};

export type ChatState = {
  phase: ChatPhase;
  percent: number;
  messages: ChatMessage[];
  error: string | null;
};

export type ChatAction =
  | { type: 'submit'; prompt: string }
  | { type: 'assistantStatus'; step: string; content: string; status: ChatPhase | 'user'; percent: number; assets?: ChatAssetEvent[] }
  | { type: 'sse'; event: ChatLifecycleEvent }
  | { type: 'reset' };

export const initialChatState: ChatState = {
  phase: 'idle',
  percent: 0,
  messages: [],
  error: null,
};

function nextId(messages: ChatMessage[]) {
  return String(messages.length + 1);
}

function toChatPhase(phase: string): ChatPhase {
  if (phase === 'completed') return 'completed';
  if (phase === 'error') return 'error';
  if (phase === 'thinking') return 'thinking';
  if (phase === 'evaluating') return 'evaluating';
  return 'streaming';
}

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  if (action.type === 'reset') return initialChatState;

  if (action.type === 'submit') {
    return {
      phase: 'submitting',
      percent: 0,
      error: null,
      messages: [
        ...state.messages,
        {
          id: nextId(state.messages),
          role: 'user',
          step: '用户指令',
          content: action.prompt,
          status: 'user',
          percent: 0,
          assets: [],
        },
      ],
    };
  }


  if (action.type === 'assistantStatus') {
    const status = action.status === 'user' ? 'streaming' : action.status;
    return {
      phase: status === 'completed' || status === 'error' || status === 'thinking' || status === 'evaluating' ? status : 'streaming',
      percent: action.percent,
      error: action.status === 'error' ? action.content : null,
      messages: [
        ...state.messages,
        {
          id: nextId(state.messages),
          role: 'assistant',
          step: action.step,
          content: action.content,
          status: action.status,
          percent: action.percent,
          assets: action.assets || [],
        },
      ],
    };
  }

  const event = action.event;
  if (event.phase === 'heartbeat') return state;

  const phase = toChatPhase(event.phase);
  const message: ChatMessage = {
    id: nextId(state.messages),
    role: 'assistant',
    step: event.step || (phase === 'completed' ? '完成' : phase === 'error' ? '出错' : 'AI'),
    content: event.message || (phase === 'completed' ? '生成完成' : ''),
    status: phase,
    percent: event.percent,
    assets: event.assets,
  };

  return {
    phase,
    percent: phase === 'completed' ? 100 : event.percent,
    error: phase === 'error' ? event.message : null,
    messages: [...state.messages, message],
  };
}
