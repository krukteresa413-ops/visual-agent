import { useState, useRef, useCallback } from 'react';

interface CanvasViewProps {
  mainImage: any;
  whiteBg: any;
  sceneImages: any[];
  sellingPoints: any[];
  videoScripts: any[];
  adMaterial: any;
  brief?: any;
}

interface CanvasState {
  x: number;
  y: number;
  scale: number;
}

export default function CanvasView({ mainImage, whiteBg, sceneImages, sellingPoints, videoScripts, adMaterial, brief }: CanvasViewProps) {
  const [canvas, setCanvas] = useState<CanvasState>({ x: 0, y: 0, scale: 1 });
  const [dragging, setDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [selectedAsset, setSelectedAsset] = useState<any>(null);
  const [modifying, setModifying] = useState(false);
  const [chatInput, setChatInput] = useState('');

  const handleModify = async () => {
    if (!chatInput.trim() || !selectedAsset || !brief) return;
    setModifying(true);
    try {
      const resp = await fetch('/api/v1/asset/modify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asset_type: selectedAsset._type,
          original: selectedAsset,
          instruction: chatInput,
          brief: brief,
        }),
      });
      const data = await resp.json();
      if (data.modified && !data.error) {
        setSelectedAsset({ ...data.modified, _type: selectedAsset._type });
        setChatInput('');
      }
    } catch (e) {
      // silent fail, keep original
    }
    finally { setModifying(false); }
  };
  const containerRef = useRef<HTMLDivElement>(null);

  // Pan: mouse drag
  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.asset-card')) return;
    setDragging(true);
    setDragStart({ x: e.clientX - canvas.x, y: e.clientY - canvas.y });
  };
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!dragging) return;
    setCanvas(prev => ({ ...prev, x: e.clientX - dragStart.x, y: e.clientY - dragStart.y }));
  };
  const handleMouseUp = () => setDragging(false);

  // Zoom: scroll wheel
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    setCanvas(prev => ({
      ...prev,
      scale: Math.max(0.2, Math.min(3, prev.scale - e.deltaY * 0.001)),
    }));
  }, []);

  // Zoom buttons
  const zoomIn = () => setCanvas(p => ({ ...p, scale: Math.min(3, p.scale + 0.2) }));
  const zoomOut = () => setCanvas(p => ({ ...p, scale: Math.max(0.2, p.scale - 0.2) }));
  const resetView = () => setCanvas({ x: 0, y: 0, scale: 1 });

  // Group assets
  const groups = [
    { type: '主图', icon: '🖼️', items: mainImage ? [{ ...mainImage, _type: 'main_image' }] : [] },
    { type: '白底图', icon: '⬜', items: whiteBg ? [{ ...whiteBg, _type: 'white_bg' }] : [] },
    { type: '场景图', icon: '🌆', items: (sceneImages || []).map((s: any) => ({ ...s, _type: 'scene_image' })) },
    { type: '卖点模块', icon: '💎', items: (sellingPoints || []).map((s: any) => ({ ...s, _type: 'selling_point' })) },
    { type: '视频脚本', icon: '🎬', items: (videoScripts || []).map((v: any) => ({ ...v, _type: 'video_script' })) },
    { type: '广告素材', icon: '📢', items: adMaterial ? [{ ...adMaterial, _type: 'ad_material' }] : [] },
  ].filter(g => g.items.length > 0);

  const renderAssetPreview = (asset: any) => {
    switch (asset._type) {
      case 'main_image':
        return <div className="text-xs space-y-1"><p className="text-gray-400 font-medium">{asset.goal}</p><p className="text-gray-600 text-[10px]">{asset.composition}</p><p className="text-orange-400/70 text-[10px] font-mono truncate">{asset.prompt?.slice(0, 80)}...</p></div>;
      case 'white_bg':
        return <div className="text-xs space-y-1"><p className="text-gray-400 font-medium">{asset.goal}</p><p className="text-gray-600 text-[10px]">{asset.instructions}</p></div>;
      case 'scene_image':
        return <div className="text-xs space-y-1"><p className="text-gray-400 font-medium">{asset.scene_name}</p><p className="text-gray-600 text-[10px]">{asset.scene_narrative}</p></div>;
      case 'selling_point':
        return <div className="text-xs space-y-1"><p className="text-gray-400 font-medium">{asset.title}</p><p className="text-gray-600 text-[10px]">{asset.description}</p></div>;
      case 'video_script':
        return <div className="text-xs space-y-1"><p className="text-gray-400 font-medium">{asset.video_goal}</p><p className="text-gray-600 text-[10px]">{asset.duration_seconds}s · {asset.pacing}</p></div>;
      case 'ad_material':
        return <div className="text-xs space-y-1"><p className="text-gray-400 font-medium">{asset.ad_goal}</p><p className="text-gray-600 text-[10px]">{asset.hook}</p></div>;
      default:
        return <p className="text-xs text-gray-500">素材</p>;
    }
  };

  return (
    <div className="flex h-[calc(100vh-120px)] gap-0">
      {/* Main canvas area */}
      <div className="flex-1 relative overflow-hidden bg-black/30 rounded-xl border border-white/5"
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        style={{ cursor: dragging ? 'grabbing' : 'grab' }}>

        {/* Toolbar */}
        <div className="absolute top-3 left-3 z-20 flex gap-1.5">
          <button onClick={zoomIn} className="w-7 h-7 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm flex items-center justify-center">+</button>
          <button onClick={zoomOut} className="w-7 h-7 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm flex items-center justify-center">−</button>
          <button onClick={resetView} className="px-2 h-7 rounded-lg bg-white/10 hover:bg-white/20 text-gray-300 text-[10px]">重置</button>
          <span className="text-[10px] text-gray-600 self-center ml-2">{Math.round(canvas.scale * 100)}%</span>
        </div>

        {/* Infinite canvas */}
        <div className="absolute inset-0 transition-transform duration-75"
          style={{
            transform: `translate(${canvas.x}px, ${canvas.y}px) scale(${canvas.scale})`,
            transformOrigin: '0 0',
          }}>
          <div className="p-12 flex flex-wrap gap-16 items-start" style={{ minWidth: '2000px' }}>
            {groups.map((group) => (
              <div key={group.type} className="space-y-3" style={{ minWidth: 220 }}>
                <div className="flex items-center gap-1.5 px-1">
                  <span>{group.icon}</span>
                  <span className="text-xs font-medium text-gray-400">{group.type}</span>
                  <span className="text-[10px] text-gray-600">({group.items.length})</span>
                </div>
                <div className="space-y-3">
                  {group.items.map((asset: any, ai: number) => (
                    <div key={ai}
                      onClick={(e) => { e.stopPropagation(); setSelectedAsset(asset); }}
                      className={`asset-card liquid-card p-3 cursor-pointer transition-all border ${
                        selectedAsset === asset
                          ? 'border-orange-500/40 shadow-lg shadow-orange-500/10'
                          : 'border-white/5 hover:border-white/20'
                      }`}
                      style={{ width: 200 }}>
                      {renderAssetPreview(asset)}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right detail panel */}
      <div className={`transition-all duration-300 overflow-hidden ${selectedAsset ? 'w-80 ml-3' : 'w-0'}`}>
        {selectedAsset && (
          <div className="liquid-card p-4 h-full overflow-y-auto space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-200">素材详情</h3>
              <button onClick={() => setSelectedAsset(null)} className="text-gray-600 hover:text-gray-300">✕</button>
            </div>
            <div className="space-y-2 text-xs">
              {Object.entries(selectedAsset).filter(([k]) => !k.startsWith('_') && k !== 'asset_type').map(([key, value]) => (
                <div key={key}>
                  <span className="text-gray-600">{key}: </span>
                  <span className="text-gray-300">{
                    typeof value === 'object' ? JSON.stringify(value).slice(0, 100) :
                    String(value).slice(0, 200)
                  }</span>
                </div>
              ))}
            </div>

            {/* Chat input for NL modification */}
            <div className="pt-3 border-t border-white/5">
              <p className="text-[10px] text-gray-600 mb-2">自然语言修改此素材</p>
              <div className="flex gap-2">
                <input
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  placeholder="例如：背景换成城市夜景..."
                  className="flex-1 bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-xs text-gray-200 placeholder-gray-600"
                  onKeyDown={e => { if (e.key === 'Enter') handleModify(); }} />
                <button onClick={handleModify}
                  disabled={modifying || !chatInput.trim()}
                  className="px-3 py-1.5 bg-orange-500/20 hover:bg-orange-500/30 disabled:opacity-30 text-orange-300 rounded-lg text-xs">
                  {modifying ? '修改中...' : '修改'}</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
