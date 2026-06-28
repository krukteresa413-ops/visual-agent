/**
 * AIChatPanel — Real-time AI progress panel for the canvas.
 *
 * Shows live generation progress as chat bubbles on the right side
 * of the canvas. Subscribes to SSE progress events or falls back
 * to polling.
 *
 * Usage:
 *   <AIChatPanel
 *     taskId={taskId}
 *     isLight={isLight}
 *     onComplete={(result) => ...}
 *     onClose={() => ...}
 *   />
 */
import { useState, useEffect, useRef, useReducer } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api, getToken } from '../api/client';
import ModelPreferencePanel from './model/ModelPreferencePanel';
import SkillsPopup from './SkillsPopup';
import MessageRenderer from './MessageRenderer';
import QuestionnairePanel from './QuestionnairePanel';
import { chatReducer, initialChatState } from '../lib/sse/chatReducer';
import { sseToChatEventAdapter } from '../lib/sse/sseToChatEventAdapter';
import {
  TEMPLATE_QUESTIONS,
  normalizeAnswer,
  isBlank,
  buildBriefFromAnswers,
  suggestSellingPoints,
  type AnswerValue,
} from '../lib/questionnaire/templateQuestions';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ProgressEvent {
  type: 'progress' | 'heartbeat' | 'done' | 'error';
  step: string;
  percent: number;
  status: 'thinking' | 'generating' | 'evaluating' | 'done' | 'error';
  message: string;
  detail?: Record<string, unknown>;
}

interface ChatMessage {
  id: number;
  step: string;
  message: string;
  status: string;
  percent: number;
  timestamp: number;
}

type AgentMode = 'agent' | 'image-gen' | 'video-gen';

interface ChatAssetContext {
  id: string;
  label: string;
  image_url?: string;
  type?: string;
  metadata?: Record<string, unknown>;
}

interface Props {
  taskId: string | null;
  isLight?: boolean;
  onComplete?: (result: unknown) => void;
  onClose?: () => void;
  onProgressUpdate?: (progress: { step: string; percent: number; status: string; message: string }) => void;
  skillPromptSelected?: string | null;
  onSkillPromptConsumed?: () => void;
  onTaskStarted?: (taskId: string) => void;
  onGenerationComplete?: (generation: unknown) => void;
  /** 对话(Agent)路径出图后,通知父级刷新无限画布(图二:对话生成同步上画布) */
  onCanvasShouldRefresh?: () => void;
  projectId?: number;
  projectName?: string;
  chatAssetContext?: ChatAssetContext | null;
}

const runningMessage = '正在生成，详细过程已移到底部 AI创作流程。';

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function AIChatPanel({ taskId, isLight, onComplete, onClose, onProgressUpdate, skillPromptSelected, onSkillPromptConsumed, onTaskStarted, onGenerationComplete, onCanvasShouldRefresh, projectId, chatAssetContext }: Props) {
  const [chatState, dispatch] = useReducer(chatReducer, initialChatState);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentPercent, setCurrentPercent] = useState(0);
  const [showAgentDropdown, setShowAgentDropdown] = useState(false);
  const [showModelPanel, setShowModelPanel] = useState(false);
  const [showSkills, setShowSkills] = useState(false);
  const [thinkOpen, setThinkOpen] = useState(true);
  // 图生视频:技能选中后挑选源图
  const [skillPicker, setSkillPicker] = useState<{ prompt: string; mode: AgentMode } | null>(null);
  const [skillImages, setSkillImages] = useState<string[]>([]);
  const [agentMode, setAgentMode] = useState<AgentMode>('agent');
  // 图一:AI 追问问卷(前端确定式,基于商业图视频模板字段)
  const [qaActive, setQaActive] = useState(false);
  const [qaIndex, setQaIndex] = useState(0);
  const [qaSeed, setQaSeed] = useState('');
  const [qaAnswers, setQaAnswers] = useState<Record<string, AnswerValue>>({});
  const [qaMulti, setQaMulti] = useState<string[]>([]);
  const [qaDone, setQaDone] = useState(false); // 本会话已走过一次问卷后,后续直接对话
  const [activeModelKind, setActiveModelKind] = useState<'image' | 'video' | '3d'>('image');
  const [autoModel, setAutoModel] = useState(true);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadedFile, setUploadedFile] = useState<{ url: string; name: string; type: string } | null>(null);
  const [uploading, setUploading] = useState(false);
  const [input, setInput] = useState('');

  // P1-9: When a skill prompt is selected externally, inject it
  useEffect(() => {
    if (skillPromptSelected) {
      setInput(skillPromptSelected);
      onSkillPromptConsumed?.();
    }
  }, [skillPromptSelected, onSkillPromptConsumed]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const msgIdRef = useRef(1);
  const { data: modelOptions } = useQuery({ queryKey: ['generation', 'models', 'catalog'], queryFn: () => api.generation.catalog() });


  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      if (file.type.startsWith('image/')) {
        const result = await api.upload.image(form);
        const url = result?.url || '';
        if (url) setUploadedFile({ url, name: file.name, type: 'image' });
      } else {
        const result = await api.upload.documentParse(form);
        const url = result?.parsed_brief?._reference_image_url || result?.url || '';
        setUploadedFile({ url, name: file.name, type: 'document' });
      }
    } catch (err) {
      console.error('upload failed', err);
    } finally {
      setUploading(false);
      if (e.target) e.target.value = '';
    }
  };

  const clearUploadedFile = () => setUploadedFile(null);

  const runChat = async (prompt: string) => {
    const promptWithContext = chatAssetContext?.image_url
      ? `${prompt}\n\n参考图片: ${chatAssetContext.image_url}`
      : prompt;
    const refUrl = chatAssetContext?.image_url
      || (uploadedFile?.type === 'image' ? uploadedFile.url : undefined);
    if (uploadedFile) clearUploadedFile();
    setInput('');
    dispatch({ type: 'submit', prompt });
    setIsStreaming(true);
    setCurrentPercent(10);
    const token = getToken();
    try {
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: promptWithContext, reference_image_url: refUrl, project_id: projectId }),
      });
      if (!response.ok || !response.body) throw new Error('对话服务暂不可用');
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let producedAsset = false; // 图二:对话期间后端已把图 seed 进画布,出图后需刷新画布
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const chatEvent = sseToChatEventAdapter(line.slice(6));
            if (chatEvent) {
              if (chatEvent.assets.length) producedAsset = true;
              dispatch({ type: 'sse', event: chatEvent });
            }
          } catch {
            // skip parse errors
          }
        }
      }
      setCurrentPercent(100);
      // 图二:对话路径生成的图片已落库为画布元素,通知父级刷新无限画布
      if (producedAsset) onCanvasShouldRefresh?.();
    } catch (error) {
      dispatch({ type: 'assistantStatus', step: '出错', content: error instanceof Error ? error.message : '对话失败', status: 'error', percent: 0 });
    } finally {
      setIsStreaming(false);
    }
  };

  const runGeneration = async (prompt: string, brief?: object, modeOverride?: AgentMode, refOverride?: string) => {
    const mode = modeOverride || agentMode;
    if (mode === 'agent' && !brief) { void runChat(prompt); return; }
    const promptWithContext = chatAssetContext?.image_url
      ? `${prompt}\n\n参考图片: ${chatAssetContext.image_url}`
      : prompt;

    setInput('');
    dispatch({ type: 'submit', prompt });
    setIsStreaming(true);
    setCurrentPercent(5);
    setMessages(prev => [...prev, {
      id: msgIdRef.current++,
      step: '用户指令',
      message: prompt,
      status: 'user',
      percent: 0,
      timestamp: Date.now(),
    }, {
      id: msgIdRef.current++,
      step: 'AI',
      message: runningMessage,
      status: 'generating',
      percent: 5,
      timestamp: Date.now(),
    }]);

    try {
      const refUrl = uploadedFile?.type === 'image' ? uploadedFile.url : undefined;
      if (uploadedFile) clearUploadedFile();
      const task = await api.generation.quickGenerate({
        prompt: promptWithContext,
        project_id: projectId,
        image_provider: 'dataeyes',
        image_model: autoModel ? undefined : selectedModel || undefined,
        auto_model: autoModel,
        agent_mode: mode,
        brief,
        // 图生视频/图生图:优先 显式源图 > brief 指定 > 上传图 > 对话关联图
        reference_image_url: refOverride ?? ((brief as any)?.reference_image_url as string | undefined) ?? refUrl ?? chatAssetContext?.image_url,
      } as Parameters<typeof api.generation.quickGenerate>[0] & { agent_mode: AgentMode });
      onTaskStarted?.(task.task_id);

      let finished = false;
      const poll = window.setInterval(async () => {
        try {
          if (finished) return;
          const latest = await api.generation.pollTask(task.task_id);
          if (finished) return;
          if (latest.status === 'complete') {
            finished = true;
            window.clearInterval(poll);
            setCurrentPercent(100);
            setIsStreaming(false);
            dispatch({ type: 'assistantStatus', step: '完成', content: '已生成第一版素材并同步到画布。', status: 'completed', percent: 100 });
            setMessages(prev => [...prev, {
              id: msgIdRef.current++,
              step: '完成',
              message: '已生成第一版素材并同步到画布。',
              status: 'done',
              percent: 100,
              timestamp: Date.now(),
            }]);
            onGenerationComplete?.(latest.generation);
          } else if (latest.status === 'error') {
            finished = true;
            window.clearInterval(poll);
            setIsStreaming(false);
            dispatch({ type: 'assistantStatus', step: '出错', content: latest.error || '生成失败', status: 'error', percent: 0 });
            setMessages(prev => [...prev, {
              id: msgIdRef.current++,
              step: '出错',
              message: latest.error || '生成失败',
              status: 'error',
              percent: 0,
              timestamp: Date.now(),
            }]);
          }
        } catch {
          // keep polling transient failures
        }
      }, 3000);
    } catch (error) {
      setIsStreaming(false);
      setMessages(prev => [...prev, {
        id: msgIdRef.current++,
        step: '出错',
        message: error instanceof Error ? error.message : '启动生成失败',
        status: 'error',
        percent: 0,
        timestamp: Date.now(),
      }]);
    }
  };

  // ── 图一:AI 追问问卷 ──
  const startQuestionnaire = (seed: string) => {
    setQaSeed(seed);
    setQaAnswers({});
    setQaIndex(0);
    setQaMulti([]);
    setQaActive(true);
    setInput('');
  };

  const finishQuestionnaire = (answers: Record<string, AnswerValue>) => {
    setQaActive(false);
    setQaDone(true);
    const { brief, prompt } = buildBriefFromAnswers(answers, qaSeed);
    void runGeneration(prompt, brief, 'image-gen');
  };

  // 记录(或跳过)当前题答案,推进到下一题;走完则组装 brief 自动生成
  const advanceWith = (answers: Record<string, AnswerValue>) => {
    const next = qaIndex + 1;
    if (next < TEMPLATE_QUESTIONS.length) {
      setQaAnswers(answers);
      setQaIndex(next);
      setQaMulti([]);
      setInput('');
    } else {
      finishQuestionnaire(answers);
    }
  };

  const recordAnswer = (raw: AnswerValue) => {
    const q = TEMPLATE_QUESTIONS[qaIndex];
    const val = normalizeAnswer(q, raw);
    const answers = { ...qaAnswers };
    if (!isBlank(val)) answers[q.key] = val;
    advanceWith(answers);
  };

  const skipCurrent = () => advanceWith({ ...qaAnswers });
  const cancelQuestionnaire = () => finishQuestionnaire({ ...qaAnswers });
  const toggleMulti = (opt: string) =>
    setQaMulti((prev) => (prev.includes(opt) ? prev.filter((x) => x !== opt) : [...prev, opt]));

  const handleSubmit = async () => {
    if (isStreaming) return;
    const prompt = input.trim();
    if (qaActive) { recordAnswer(prompt); return; }
    if (!prompt) return;
    // Agent 模式首次创作 -> 进入模板追问;已问过本会话或图生图/视频模式 -> 原行为
    if (agentMode === 'agent' && !qaDone) { startQuestionnaire(prompt); return; }
    runGeneration(prompt);
  };

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Subscribe to SSE progress
  useEffect(() => {
    if (!taskId) return;

    setIsStreaming(true);
    setMessages(prev => {
      const hasRunningHint = prev.some(msg => msg.status === 'generating' && msg.message === runningMessage);
      if (hasRunningHint) return prev;
      return [...prev, {
        id: msgIdRef.current++,
        step: 'AI',
        message: runningMessage,
        status: 'generating',
        percent: 0,
        timestamp: Date.now(),
      }];
    });

    const token = getToken();
    const ctrl = new AbortController();
    const url = api.progress.streamUrl(taskId);

    let pollInterval: number | null = null;

    const connectSSE = () => {
      fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal: ctrl.signal,
      })
        .then(async (response) => {
          if (!response.ok || !response.body) {
            throw new Error('SSE unavailable');
          }

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
              if (!line.startsWith('data: ')) continue;

              try {
                const event: ProgressEvent = JSON.parse(line.slice(6));
                const chatEvent = sseToChatEventAdapter(event);
                if (chatEvent) {
                  dispatch({ type: 'sse', event: chatEvent });
                }
                handleEvent(event);
              } catch {
                // skip parse errors
              }
            }
          }
        })
        .catch(() => {
          // SSE failed → fallback to polling
          if (!ctrl.signal.aborted) {
            startPolling();
          }
        });
    };

    const handleEvent = (event: ProgressEvent) => {
      setCurrentPercent(event.percent);

      if (event.type === 'heartbeat') return;

      // Notify parent for WorkflowSidebar sync
      onProgressUpdate?.({ step: event.step, percent: event.percent, status: event.status, message: event.message });

      if (event.status === 'done') {
        setMessages(prev => [...prev, {
          id: msgIdRef.current++,
          step: event.step,
          message: `生成完成！共生成 6 类素材，耗时约 ${event.detail?.elapsed_seconds || '?'} 秒`,
          status: 'done',
          percent: 100,
          timestamp: Date.now(),
        }]);
        setCurrentPercent(100);
        setIsStreaming(false);
        onComplete?.(event.detail);
        return;
      }

      if (event.status === 'error') {
        setMessages(prev => [...prev, {
          id: msgIdRef.current++,
          step: '出错',
          message: event.message || '生成过程出现错误',
          status: 'error',
          percent: event.percent,
          timestamp: Date.now(),
        }]);
        setIsStreaming(false);
        return;
      }

      setMessages(prev => {
        const next = [...prev];
        const runningIndex = next.findIndex(msg => msg.status === 'generating' && msg.message === runningMessage);
        if (runningIndex >= 0) {
          next[runningIndex] = { ...next[runningIndex], percent: event.percent, timestamp: Date.now() };
          return next;
        }
        return [...next, {
          id: msgIdRef.current++,
          step: 'AI',
          message: runningMessage,
          status: 'generating',
          percent: event.percent,
          timestamp: Date.now(),
        }];
      });
    };

    const startPolling = () => {
      pollInterval = window.setInterval(async () => {
        try {
          const resp = await fetch(`/api/v1/generation/task/${taskId}`);
          const data = await resp.json();
          if (data.status === 'complete') {
            dispatch({ type: 'assistantStatus', step: '完成', content: '生成完成！（通过轮询获取）', status: 'completed', percent: 100 });
            setMessages(prev => [...prev, {
              id: msgIdRef.current++,
              step: '完成',
              message: '生成完成！（通过轮询获取）',
              status: 'done',
              percent: 100,
              timestamp: Date.now(),
            }]);
            setCurrentPercent(100);
            setIsStreaming(false);
            if (pollInterval) clearInterval(pollInterval);
            onComplete?.(data.generation);
          } else if (data.status === 'error') {
            dispatch({ type: 'assistantStatus', step: '出错', content: data.error || '生成失败', status: 'error', percent: 0 });
            setMessages(prev => [...prev, {
              id: msgIdRef.current++,
              step: '出错',
              message: data.error || '生成失败',
              status: 'error',
              percent: 0,
              timestamp: Date.now(),
            }]);
            setIsStreaming(false);
            if (pollInterval) clearInterval(pollInterval);
          }
        } catch {
          // keep polling
        }
      }, 3000);
    };

    connectSSE();

    return () => {
      ctrl.abort();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [taskId, onComplete, onProgressUpdate]);

  const bg = isLight ? 'bg-white border-gray-200' : 'bg-gray-900/95 border-gray-700';
  const textColor = isLight ? 'text-gray-900' : 'text-white';
  const subText = isLight ? 'text-gray-500' : 'text-gray-400';
  const placeholderText = isLight ? 'text-gray-300' : 'text-gray-600';
  const toolIconColor = isLight ? 'text-gray-400 hover:text-gray-700' : 'text-gray-500 hover:text-gray-300';
  const agentChipBg = isLight ? 'bg-gray-100' : 'bg-white/10';
  const dropdownBg = isLight ? 'bg-white border-gray-200' : 'bg-gray-800 border-white/10';

  const renderedMessages = chatState.messages.length > 0 ? chatState.messages : messages.map(msg => ({
    id: String(msg.id),
    role: msg.status === 'user' ? 'user' as const : 'assistant' as const,
    step: msg.step,
    content: msg.message,
    status: msg.status === 'done' ? 'completed' : msg.status,
    percent: msg.percent,
    assets: [],
  }));
  const hasProgressMessages = renderedMessages.length > 0;
  const lifecyclePhase = chatState.phase;

  // 思考链:用户消息常显;中间步骤折叠;完成/出错消息常显。完成后自动收起思考链。
  const userMsgs = renderedMessages.filter((m) => m.role === 'user');
  const stepMsgs = renderedMessages.filter((m) => m.role === 'assistant' && m.status !== 'completed' && m.status !== 'error');
  const finalMsgs = renderedMessages.filter((m) => m.role === 'assistant' && (m.status === 'completed' || m.status === 'error'));
  useEffect(() => { if (lifecyclePhase === 'completed') setThinkOpen(false); }, [lifecyclePhase]);

  return (
    <div data-ai-chat-panel="true" className={`flex flex-col h-full ${bg} border-l ${isLight ? 'border-gray-200' : 'border-white/5'}`}>
      {skillPicker && (
        <div className="fixed inset-0 z-[60] grid place-items-center bg-black/50 p-4" onClick={() => setSkillPicker(null)}>
          <div className={`w-full max-w-md rounded-2xl border p-4 ${isLight ? 'border-gray-200 bg-white' : 'border-white/10 bg-[#15161c]'}`} onClick={(e) => e.stopPropagation()}>
            <div className={`mb-3 text-sm font-semibold ${textColor}`}>
              选择源图{skillPicker.mode === 'video-gen' ? '做「图生视频」' : '应用此技能'}<span className={`ml-1 text-xs font-normal ${subText}`}>(可选)</span>
            </div>
            {skillImages.length > 0 ? (
              <div className="grid max-h-72 grid-cols-3 gap-2 overflow-y-auto">
                {skillImages.map((u, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => { const { prompt: pr, mode } = skillPicker; setSkillPicker(null); setAgentMode(mode); runGeneration(pr, undefined, mode, u); }}
                    className="overflow-hidden rounded-lg border border-black/10 transition hover:border-orange-400/60"
                  >
                    <img src={u} alt="" className="aspect-square w-full object-cover" />
                  </button>
                ))}
              </div>
            ) : (
              <div className={`py-6 text-center text-xs ${subText}`}>画布暂无可用图片,可直接生成</div>
            )}
            <div className="mt-3 flex justify-end gap-2">
              <button type="button" onClick={() => setSkillPicker(null)} className={`rounded-lg px-3 py-1.5 text-xs ${subText}`}>取消</button>
              <button
                type="button"
                onClick={() => { const { prompt: pr, mode } = skillPicker; setSkillPicker(null); setAgentMode(mode); runGeneration(pr, undefined, mode); }}
                className="rounded-lg bg-gradient-to-r from-orange-500 to-rose-500 px-3 py-1.5 text-xs font-medium text-white"
              >
                直接生成
              </button>
            </div>
          </div>
        </div>
      )}
      {/* ── Header: project name + action icons ── */}
      <div className="flex items-center justify-between px-5 pt-5 pb-3 shrink-0">
        <div className="flex items-center gap-3">
          {onClose && (
            <button onClick={onClose} className={`${toolIconColor} transition-colors text-sm`}>✕</button>
          )}
        </div>
      </div>

      <span data-chat-lifecycle-phase={lifecyclePhase} className="sr-only">{lifecyclePhase}</span>

      {/* ── Progress bar ── */}
      {isStreaming && (
        <div className={`h-1 ${isLight ? 'bg-gray-100' : 'bg-gray-800'}`}>
          <div className="h-full bg-gradient-to-r from-orange-400 to-orange-600 transition-all duration-500 ease-out" style={{ width: `${currentPercent}%` }} />
        </div>
      )}

      {/* ── Messages area ── */}
      <div data-ai-chat-messages="true" className={`flex-1 overflow-y-auto px-5 py-2 ${hasProgressMessages ? 'space-y-3' : 'space-y-4'}`}>
        {chatAssetContext && (
          <div data-chat-asset-context="true" className={`rounded-2xl border px-3 py-3 ${isLight ? 'bg-purple-50 border-purple-100' : 'bg-purple-900/20 border-purple-800/30'}`}>
            <div className={`text-xs font-medium ${textColor}`}>已添加图片到对话</div>
            <div className={`mt-1 text-[11px] ${subText}`}>{chatAssetContext.label || '画布图片'}</div>
            {chatAssetContext.image_url && (
              <img src={chatAssetContext.image_url} alt={chatAssetContext.label || '聊天图片上下文'} className="mt-2 h-24 w-full rounded-xl object-cover" />
            )}
          </div>
        )}

        {hasProgressMessages ? (
          <>
            {/* Date separator */}
            <div className="text-center">
              <span className={`text-[11px] ${isLight ? 'text-gray-400' : 'text-gray-600'}`}>
                {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
              </span>
            </div>

            {userMsgs.map((msg) => (
              <MessageRenderer key={msg.id} message={msg} isLight={isLight} />
            ))}
            {stepMsgs.length > 0 && (
              <details
                open={thinkOpen}
                onToggle={(e) => setThinkOpen((e.currentTarget as HTMLDetailsElement).open)}
                className={`rounded-2xl border ${isLight ? 'border-gray-200 bg-gray-50' : 'border-white/10 bg-white/[0.03]'}`}
              >
                <summary className={`cursor-pointer select-none px-3 py-2 text-xs ${isLight ? 'text-gray-500' : 'text-gray-400'}`}>
                  💭 思考过程 · {stepMsgs.length} 步{lifecyclePhase === 'completed' ? '(已折叠,点击展开)' : '…'}
                </summary>
                <div className="space-y-1 px-1 pb-2">
                  {stepMsgs.map((msg) => (
                    <MessageRenderer key={msg.id} message={msg} isLight={isLight} />
                  ))}
                </div>
              </details>
            )}
            {finalMsgs.map((msg) => (
              <MessageRenderer key={msg.id} message={msg} isLight={isLight} />
            ))}
          </>
        ) : null}

        {qaActive && (
          <QuestionnairePanel
            isLight={isLight}
            index={qaIndex}
            question={
              TEMPLATE_QUESTIONS[qaIndex].key === 'selling_points'
                ? { ...TEMPLATE_QUESTIONS[qaIndex], options: suggestSellingPoints(qaAnswers) }
                : TEMPLATE_QUESTIONS[qaIndex]
            }
            answers={qaAnswers}
            multiSelected={qaMulti}
            onPickSingle={(opt) => recordAnswer(opt)}
            onToggleMulti={toggleMulti}
            onCommitMulti={() => recordAnswer(qaMulti)}
            onSubmitDate={(v) => recordAnswer(v)}
            onSkip={skipCurrent}
            onCancel={cancelQuestionnaire}
          />
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Bottom input area ── */}
      <div className="shrink-0 border-t border-white/5 px-4 pb-4 pt-2">
        <div data-lovart-composer className={`relative rounded-3xl border ${isLight ? 'border-gray-200 bg-white shadow-sm' : 'border-white/10 bg-black/20'}`}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            rows={2}
            placeholder={qaActive ? '输入答案,或点选上方选项;Enter 提交,留空跳过' : '输入你的想法，Enter 发送，Shift+Enter 换行'}
            className={`max-h-28 min-h-[56px] w-full resize-none rounded-3xl bg-transparent px-4 py-3 text-sm ${textColor} outline-none placeholder:${placeholderText}`}
          />
          {showModelPanel && (
            <div data-composer-model-panel className="absolute bottom-full left-0 z-30 mb-2 w-80">
              <ModelPreferencePanel
                isOpen={showModelPanel}
                onToggle={() => setShowModelPanel(!showModelPanel)}
                modelsData={modelOptions}
                activeKind={activeModelKind}
                setActiveKind={setActiveModelKind}
                autoModel={autoModel}
                setAutoModel={setAutoModel}
                selectedModel={selectedModel}
                setSelectedModel={setSelectedModel}
              />
            </div>
          )}
          {showSkills && (
            <>
              <div className="fixed inset-0 z-20" onClick={() => setShowSkills(false)} />
              <div className="absolute bottom-full left-0 z-30 mb-2 w-80">
                <SkillsPopup
                  isLight={!!isLight}
                  onClose={() => setShowSkills(false)}
                  onSelectSkill={(p, cat) => {
                    setShowSkills(false);
                    // 所有技能都先让用户挑画布源图(抠图/换色/详情页/图生视频 等均基于已有图);也可不选直接生成
                    const m: AgentMode = cat === 'Video' ? 'video-gen' : 'image-gen';
                    const pid = projectId ?? 2;
                    const pickUrl = (it: any): string | undefined =>
                      it?.url || it?.image_url || it?.preview_url || it?.thumbnail_url || it?.asset_ref?.url;
                    // 图一:资产库 + 画布状态(对话生成的图 seed 在 canvas-state elements)双来源合并
                    Promise.allSettled([api.atelierCanvas.getAssets(pid), api.atelierCanvas.getState(pid)])
                      .then((results) => {
                        const urls: string[] = [];
                        if (results[0].status === 'fulfilled') {
                          const resp: any = results[0].value;
                          const items = Array.isArray(resp) ? resp : (resp?.assets || resp?.elements || resp?.images || []);
                          for (const it of items as any[]) { const u = pickUrl(it); if (u) urls.push(u); }
                        }
                        if (results[1].status === 'fulfilled') {
                          const state: any = results[1].value;
                          for (const el of (state?.elements || []) as any[]) { const u = pickUrl(el); if (u) urls.push(u); }
                        }
                        const valid = urls.filter((u): u is string => typeof u === 'string' && /^(https?:|\/)/.test(u));
                        setSkillImages(Array.from(new Set(valid)));
                        setSkillPicker({ prompt: p, mode: m });
                      });
                  }}
                />
              </div>
            </>
          )}
          <div className="flex items-center justify-between px-3 pb-2.5">
            <div className="flex items-center gap-3">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,.pdf,.ppt,.pptx,.doc,.docx,.md,.txt"
                className="hidden"
                onChange={handleFileUpload}
              />
              <button data-composer-tool="upload" type="button" onClick={() => fileInputRef.current?.click()} disabled={uploading} className={`${toolIconColor} transition-colors hover:opacity-80 disabled:opacity-40`} aria-label="上传文件">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </button>
              {uploadedFile && (
                <div className="flex items-center gap-2 rounded-lg border border-orange-500/20 bg-orange-500/5 px-2 py-1">
                  {uploadedFile.type === 'image' && <img src={uploadedFile.url} alt="" className="h-6 w-6 rounded object-cover" />}
                  <span className="max-w-[120px] truncate text-[10px] text-gray-400">{uploadedFile.name}</span>
                  <button onClick={clearUploadedFile} className="text-[10px] text-gray-500 hover:text-red-400" aria-label="移除">✕</button>
                </div>
              )}
              <div className="relative">
                <button
                  data-composer-tool="agent"
                  type="button"
                  onClick={() => setShowAgentDropdown(!showAgentDropdown)}
                  className={`flex items-center gap-1.5 ${agentChipBg} rounded-full px-2.5 py-1 text-xs ${textColor} transition-colors hover:opacity-80`}
                >
                  <span>Agent</span>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><polyline points="6 9 12 15 18 9"/></svg>
                </button>
                {showAgentDropdown && (
                  <>
                    <div className="fixed inset-0 z-10" onClick={() => setShowAgentDropdown(false)} />
                    <div className={`absolute bottom-full left-0 z-20 mb-2 min-w-[180px] rounded-2xl border py-2 shadow-xl ${dropdownBg}`}>
                      {[
                        { id: 'agent' as AgentMode, label: 'Agent' },
                        { id: 'image-gen' as AgentMode, label: '图像' },
                        { id: 'video-gen' as AgentMode, label: '视频' },
                      ].map((mode) => (
                        <button
                          key={mode.id}
                          type="button"
                          onClick={() => { setAgentMode(mode.id as AgentMode); setShowAgentDropdown(false); }}
                          className={`flex w-full items-center gap-3 px-5 py-3 text-sm transition-colors ${agentMode === mode.id ? `${textColor} ${isLight ? 'bg-gray-50' : 'bg-white/5'}` : `${subText}`}`}
                        >
                          <span className="flex-1 text-left">{mode.label}</span>
                          {agentMode === mode.id && <span>✓</span>}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>
              <button data-composer-tool="skills" type="button" onClick={() => setShowSkills((v) => !v)} className={`${toolIconColor} transition-colors hover:opacity-80`} title="生图 / 生视频技能" aria-label="技能">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/></svg>
              </button>
              <button data-composer-tool="model" type="button" onClick={() => setShowModelPanel(!showModelPanel)} className={`${toolIconColor} transition-colors`} aria-label="模型偏好">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
              </button>
            </div>
            <button
              data-composer-tool="send"
              type="button"
              onClick={handleSubmit}
              disabled={!input.trim() || isStreaming}
              className={`flex size-9 items-center justify-center rounded-full transition-opacity hover:opacity-80 disabled:cursor-not-allowed disabled:opacity-40 ${isLight ? 'bg-gray-900 text-white' : 'bg-white text-gray-900'}`}
              aria-label="发送"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 2 11 13"/><path d="m22 2-7 20-4-9-9-4Z"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
