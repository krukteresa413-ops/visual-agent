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
import MessageRenderer from './MessageRenderer';
import BusinessBriefDrawer from './BusinessBriefDrawer';
import { chatReducer, initialChatState } from '../lib/sse/chatReducer';
import { sseToChatEventAdapter } from '../lib/sse/sseToChatEventAdapter';

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
  onSkillsOpen?: () => void;
  skillPromptSelected?: string | null;
  onSkillPromptConsumed?: () => void;
  onTaskStarted?: (taskId: string) => void;
  onGenerationComplete?: (generation: unknown) => void;
  projectId?: number;
  projectName?: string;
  chatAssetContext?: ChatAssetContext | null;
}

const idleMessage = '输入你想生成或调整的画面，我会直接执行。生成过程统一在底部 AI创作流程 中展示。';
const runningMessage = '正在生成，详细过程已移到底部 AI创作流程。';

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function AIChatPanel({ taskId, isLight, onComplete, onClose, onProgressUpdate, onSkillsOpen, skillPromptSelected, onSkillPromptConsumed, onTaskStarted, onGenerationComplete, projectId, projectName, chatAssetContext }: Props) {
  const [chatState, dispatch] = useReducer(chatReducer, initialChatState);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentPercent, setCurrentPercent] = useState(0);
  const [showAgentDropdown, setShowAgentDropdown] = useState(false);
  const [showModelPanel, setShowModelPanel] = useState(false);
  const [agentMode, setAgentMode] = useState<AgentMode>('agent');
  const [genMode, setGenMode] = useState<'quick' | 'business'>('quick');
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

  const handleSubmit = async () => {
    const prompt = input.trim();
    if (!prompt || isStreaming) return;
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
        agent_mode: agentMode,
        reference_image_url: refUrl,
      } as Parameters<typeof api.generation.quickGenerate>[0] & { agent_mode: AgentMode });
      onTaskStarted?.(task.task_id);

      const poll = window.setInterval(async () => {
        try {
          const latest = await api.generation.pollTask(task.task_id);
          if (latest.status === 'complete') {
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
  const bubbleAI = isLight ? 'bg-orange-50 border-orange-200' : 'bg-orange-900/30 border-orange-700/50';
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

  return (
    <div data-ai-chat-panel="true" className={`flex flex-col h-full ${bg} border-l ${isLight ? 'border-gray-200' : 'border-white/5'}`}>
      {/* ── Header: project name + action icons ── */}
      <div className="flex items-center justify-between px-5 pt-5 pb-3 shrink-0">
        <span className={`text-sm font-medium ${textColor}`}>{projectName || 'AI 对话'}</span>
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

      {/* ── Mode toggle ── */}
      <div className="px-4 pt-3">
        <div className={`inline-flex gap-1 rounded-lg p-0.5 ${isLight ? 'bg-gray-100' : 'bg-white/5'}`}>
          {(['quick','business'] as const).map((m) => (
            <button key={m} type="button" onClick={() => setGenMode(m)}
              className={`rounded-md px-3 py-1 text-xs ${genMode===m ? (isLight?'bg-white font-medium shadow-sm':'bg-white/10 font-medium') : (isLight?'text-gray-500':'text-gray-400')}`}>
              {m === 'quick' ? '快速出图' : '商务出图'}
            </button>
          ))}
        </div>
      </div>

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

            {renderedMessages.map((msg) => (
              <MessageRenderer key={msg.id} message={msg} isLight={isLight} />
            ))}
          </>
        ) : genMode === 'business' ? (
          <BusinessBriefDrawer
            isLight={isLight ?? false}
            onSubmit={() => {}}
          />
        ) : (
          <div className={`text-sm leading-relaxed rounded-2xl border px-3 py-3 ${bubbleAI}`}>
            <div className={subText}>{idleMessage}</div>
          </div>
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
            placeholder="输入你的想法，Enter 发送，Shift+Enter 换行"
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
              <button data-composer-tool="library" type="button" onClick={onSkillsOpen} className={`${toolIconColor} transition-colors`} title="素材库" aria-label="素材库">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
              </button>
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
              <button data-composer-tool="inspiration" type="button" disabled className={`${toolIconColor} cursor-not-allowed opacity-40`} title="灵感稍后接入" aria-label="灵感">
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
