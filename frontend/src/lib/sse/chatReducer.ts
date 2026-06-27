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
  if (event.terminalOnly) {
    return {
      phase,
      percent: phase === 'completed' ? 100 : event.percent,
      error: phase === 'error' ? event.message : null,
      messages: state.messages,
    };
  }

  const message: ChatMessage = {
    id: nextId(state.messages),
    role: 'assistant',
    step: event.step || (phase === 'completed' ? '完成' : phase === 'error' ? '出错' : 'AI'),
    content: event.message || (phase === 'completed' ? '生成完成' : ''),
    status: phase,
    percent: event.percent,
    assets: event.assets,
  };

  // 去重:同一 step 的 assistant 进度合并为一条(running→success 原地更新),
  // 形成简洁的思考链,而非每个 SSE 事件都堆一张卡。
  const dupIdx = state.messages.findIndex(
    (m) => m.role === 'assistant' && m.step === message.step && m.status !== 'completed' && m.status !== 'error',
  );
  const messages = dupIdx >= 0
    ? state.messages.map((m, i) => (i === dupIdx
        ? { ...m, content: message.content || m.content, status: message.status, percent: message.percent, assets: message.assets.length ? message.assets : m.assets }
        : m))
    : [...state.messages, message];

  return {
    phase,
    percent: phase === 'completed' ? 100 : event.percent,
    error: phase === 'error' ? event.message : null,
    messages,
  };
}
