import { useMemo, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Excalidraw, convertToExcalidrawElements } from '@excalidraw/excalidraw';
import '@excalidraw/excalidraw/index.css';
import { api } from '../../api/client';

// Excalidraw 小样(spike):验证「Excalidraw 当画布引擎」是否可行——
//   ① 全套原生设计工具(选择/抓手/形状/箭头/线/自由画/文字/图片)开箱即用
//   ② 持久化(这里用 localStorage 验证 save/load 往返;全量迁移再换 MOYAG 后端)
//   ③ 复用 MOYAG 现有后端生成(quickGenerate→轮询 getState)把结果图「落到」Excalidraw 画布
// 独立路由 /excali/:projectId,完全不碰现有 React Flow 画布。
// 注:Excalidraw 类型很深且随版本变化,spike 里对其元素/文件做局部 as-cast,保证 tsc 通过即可。

const SCENE_KEY = (pid: string) => `moyag-excali-scene-${pid}`;

export default function ExcaliCanvas() {
  const { projectId } = useParams();
  const pid = projectId || '2';
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const apiRef = useRef<any>(null);
  const saveTimer = useRef<number | null>(null);
  const [prompt, setPrompt] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');

  const initialData = useMemo(() => {
    try {
      const raw = localStorage.getItem(SCENE_KEY(pid));
      if (!raw) return null;
      const d = JSON.parse(raw);
      return { elements: d.elements ?? [], appState: { ...(d.appState ?? {}), collaborators: undefined }, files: d.files ?? undefined };
    } catch {
      return null;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pid]);

  // 把一张图片 URL 落到 Excalidraw 画布(fetch→dataURL→image 元素)
  const placeImage = async (url: string) => {
    const ex = apiRef.current;
    if (!ex) return;
    const resp = await fetch(url, { mode: 'cors' });
    if (!resp.ok) throw new Error('fetch ' + resp.status);
    const blob = await resp.blob();
    const dataURL: string = await new Promise((res, rej) => {
      const r = new FileReader();
      r.onload = () => res(String(r.result));
      r.onerror = rej;
      r.readAsDataURL(blob);
    });
    const dim = await new Promise<{ w: number; h: number }>((res) => {
      const img = new Image();
      img.onload = () => res({ w: img.naturalWidth || 512, h: img.naturalHeight || 512 });
      img.onerror = () => res({ w: 512, h: 512 });
      img.src = dataURL;
    });
    const maxW = 480;
    const scale = dim.w > maxW ? maxW / dim.w : 1;
    const w = Math.round(dim.w * scale);
    const h = Math.round(dim.h * scale);
    const fileId = 'gen_' + Date.now();
    const st = ex.getAppState();
    const cx = -st.scrollX + st.width / 2 / st.zoom.value;
    const cy = -st.scrollY + st.height / 2 / st.zoom.value;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ex.addFiles([{ id: fileId, dataURL, mimeType: blob.type || 'image/png', created: Date.now() } as any]);
    const els = convertToExcalidrawElements([
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      { type: 'image', fileId, x: cx - w / 2, y: cy - h / 2, width: w, height: h } as any,
    ]);
    ex.updateScene({ elements: [...ex.getSceneElements(), ...els] });
  };

  // 生成:复用 MOYAG quickGenerate + 轮询 getState diff(与 Phase A 同一管线)
  const generate = async () => {
    const text = prompt.trim();
    if (!text || busy) return;
    setBusy(true);
    setNotice('正在生成图片(走 MOYAG 后端)…');
    try {
      const before = new Set<string>();
      const cur = await api.atelierCanvas.getState(Number(pid)).catch(() => null);
      (cur?.elements || []).forEach((e: { id: string }) => before.add(String(e.id)));
      await api.generation.quickGenerate({ prompt: text, project_id: Number(pid), agent_mode: 'image-gen', auto_model: true });
      let placed = false;
      for (let i = 0; i < 16; i += 1) {
        await new Promise((r) => window.setTimeout(r, 3000));
        const data = await api.atelierCanvas.getState(Number(pid)).catch(() => null);
        const fresh = (data?.elements || []).filter((e: { id: string }) => !before.has(String(e.id)));
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const hit = fresh.find((e: any) => e.thumbnail_url || e?.asset_ref?.url);
        if (hit) {
          const u = hit.thumbnail_url || hit.asset_ref?.url;
          try {
            await placeImage(u);
            setNotice('已生成并落到 Excalidraw 画布 ✓');
          } catch (err) {
            setNotice('已生成但落图失败(可能图片跨域 CORS)：' + (err instanceof Error ? err.message : ''));
          }
          placed = true;
          break;
        }
      }
      if (!placed) setNotice('后端仍在生成,稍后重试');
    } catch (e) {
      setNotice('生成失败：' + (e instanceof Error ? e.message : '未知错误'));
    } finally {
      setBusy(false);
      window.setTimeout(() => setNotice(''), 6000);
    }
  };

  return (
    <div style={{ position: 'relative', height: '100vh', width: '100%' }}>
      {/* spike 浮条:生成入口(走 MOYAG 真后端) */}
      <div style={{ position: 'absolute', top: 12, left: '50%', transform: 'translateX(-50%)', zIndex: 20, display: 'flex', gap: 8, alignItems: 'center', background: 'rgba(255,255,255,0.95)', border: '1px solid rgba(0,0,0,0.1)', borderRadius: 12, padding: '6px 8px', boxShadow: '0 8px 24px rgba(0,0,0,0.12)' }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: '#7c3aed' }}>Excalidraw 小样</span>
        <input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') generate(); }}
          placeholder="描述要生成的图片…"
          style={{ width: 240, height: 30, borderRadius: 8, border: '1px solid #e5e7eb', padding: '0 10px', fontSize: 13, outline: 'none', color: '#111' }}
        />
        <button
          onClick={generate}
          disabled={busy || !prompt.trim()}
          style={{ height: 30, padding: '0 12px', borderRadius: 8, border: 'none', background: busy ? '#c4b5fd' : 'linear-gradient(90deg,#f97316,#f43f5e)', color: '#fff', fontSize: 13, fontWeight: 500, cursor: busy ? 'default' : 'pointer' }}
        >
          {busy ? '生成中…' : '✨ AI 生成图'}
        </button>
        {notice && <span style={{ fontSize: 12, color: '#374151', maxWidth: 320 }}>{notice}</span>}
      </div>

      <Excalidraw
        excalidrawAPI={(a) => { apiRef.current = a; }}
        initialData={initialData}
        onChange={(elements, appState, files) => {
          if (saveTimer.current) window.clearTimeout(saveTimer.current);
          const snapshot = JSON.stringify({ elements, appState: { ...appState, collaborators: undefined }, files });
          saveTimer.current = window.setTimeout(() => {
            try { localStorage.setItem(SCENE_KEY(pid), snapshot); } catch { /* quota */ }
          }, 800);
        }}
      />
    </div>
  );
}
