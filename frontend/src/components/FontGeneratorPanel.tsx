import { useState, useRef } from 'react';
import { api } from '../api/client';

interface FontGeneratorPanelProps {
  projectId: number;
  isOpen: boolean;
  onClose: () => void;
  onFontGenerated?: (fontData: any) => void;
  isLight?: boolean;
}

interface FontItem {
  id: string;
  name: string;
  style_description: string;
  sample_url?: string;
  created_at: string;
  status: 'pending' | 'generating' | 'complete' | 'error';
}

export default function FontGeneratorPanel({
  // projectId 保留在 interface(调用方照传),但后端字体接口非项目维度,组件内不再使用。
  isOpen,
  onClose,
  onFontGenerated,
  isLight = true,
}: FontGeneratorPanelProps) {
  // State
  const [referenceImage, setReferenceImage] = useState<File | null>(null);
  const [referencePreview, setReferencePreview] = useState<string>('');
  const [styleDescription, setStyleDescription] = useState('');
  const [generating, setGenerating] = useState(false);
  const [myFonts, setMyFonts] = useState<FontItem[]>([]);
  const [activeTab, setActiveTab] = useState<'generate' | 'my-fonts'>('generate');
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Handlers ─────────────────────────────────────────────────
  
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setReferenceImage(file);
    const reader = new FileReader();
    reader.onload = (ev) => {
      setReferencePreview(ev.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleGenerate = async () => {
    if (!referenceImage || !styleDescription.trim()) {
      alert('请上传参考图片并填写风格描述');
      return;
    }

    setGenerating(true);
    try {
      // 后端字体生成已改为「文字 + 风格名」JSON 契约(不吃参考图);此旧面板保留兼容,以风格描述作为生成文字。
      // 画布内新版入口见 FontComposer(走同一后端 /font-generate)。
      const result = await api.font.generate({
        text: styleDescription.trim(),
        style_name: styleDescription.trim() || undefined,
        width: 1024,
        height: 1024,
      });

      if (onFontGenerated) onFontGenerated(result);

      // 后端同步执行,结果落 history → 刷新「我的字体」即可见
      await loadMyFonts();

      // Reset form
      setReferenceImage(null);
      setReferencePreview('');
      setStyleDescription('');
      setActiveTab('my-fonts');

      alert('字体生成已提交,请在「我的字体」查看');
    } catch (error: any) {
      console.error('Font generation failed:', error);
      alert(error?.response?.data?.detail || '字体生成失败，请稍后重试');
    } finally {
      setGenerating(false);
    }
  };

  const loadMyFonts = async () => {
    try {
      const data = await api.font.history({ page: 1, page_size: 50 });
      const mapStatus = (s: string): FontItem['status'] =>
        s === 'completed' ? 'complete' : s === 'failed' ? 'error' : s === 'processing' ? 'generating' : 'pending';
      setMyFonts((data?.items || []).map((it: { task_id: string; text: string; style_name?: string | null; image_url?: string | null; created_at: string; status: string }) => ({
        id: it.task_id,
        name: it.text,
        style_description: it.style_name || '',
        sample_url: it.image_url || undefined,
        created_at: it.created_at,
        status: mapStatus(it.status),
      })));
    } catch (error) {
      console.error('Failed to load fonts:', error);
    }
  };

  const handleUseFontInCanvas = (font: FontItem) => {
    if (onFontGenerated) {
      onFontGenerated({
        font_id: font.id,
        font_name: font.name,
        sample_url: font.sample_url,
        style_description: font.style_description,
      });
    }
    onClose();
  };

  // Load fonts when switching to my-fonts tab
  const handleTabChange = (tab: 'generate' | 'my-fonts') => {
    setActiveTab(tab);
    if (tab === 'my-fonts') {
      loadMyFonts();
    }
  };

  if (!isOpen) return null;

  // ── Render ───────────────────────────────────────────────────

  return (
    <div className="fixed inset-0 z-[9998] flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={onClose}>
      <div className={`relative w-[680px] max-h-[85vh] rounded-2xl shadow-2xl overflow-hidden ${
        isLight ? 'bg-white' : 'bg-gray-900'
      }`}
        onClick={e => e.stopPropagation()}>
        
        {/* Header */}
        <div className={`flex items-center justify-between px-6 py-4 border-b ${
          isLight ? 'border-gray-200 bg-gray-50' : 'border-gray-700 bg-gray-800'
        }`}>
          <h2 className={`text-lg font-semibold ${
            isLight ? 'text-gray-800' : 'text-gray-100'
          }`}>
            字体生成器
          </h2>
          <button onClick={onClose}
            className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
              isLight
                ? 'hover:bg-gray-200 text-gray-500 hover:text-gray-700'
                : 'hover:bg-gray-700 text-gray-400 hover:text-gray-200'
            }`}>
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className={`flex border-b ${
          isLight ? 'border-gray-200' : 'border-gray-700'
        }`}>
          <button
            onClick={() => handleTabChange('generate')}
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'generate'
                ? isLight
                  ? 'text-orange-600 border-b-2 border-orange-600'
                  : 'text-orange-400 border-b-2 border-orange-400'
                : isLight
                  ? 'text-gray-500 hover:text-gray-700'
                  : 'text-gray-400 hover:text-gray-200'
            }`}>
            生成新字体
          </button>
          <button
            onClick={() => handleTabChange('my-fonts')}
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'my-fonts'
                ? isLight
                  ? 'text-orange-600 border-b-2 border-orange-600'
                  : 'text-orange-400 border-b-2 border-orange-400'
                : isLight
                  ? 'text-gray-500 hover:text-gray-700'
                  : 'text-gray-400 hover:text-gray-200'
            }`}>
            我的字体 ({myFonts.length})
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto" style={{ maxHeight: 'calc(85vh - 140px)' }}>
          
          {/* Generate Tab */}
          {activeTab === 'generate' && (
            <div className="p-6 space-y-5">
              
              {/* Upload Section */}
              <div>
                <label className={`block text-sm font-medium mb-2 ${
                  isLight ? 'text-gray-700' : 'text-gray-300'
                }`}>
                  参考字体图片
                </label>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageSelect}
                  className="hidden"
                />
                
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className={`relative w-full h-48 rounded-xl border-2 border-dashed cursor-pointer transition-colors flex items-center justify-center overflow-hidden ${
                    isLight
                      ? 'border-gray-300 hover:border-orange-400 bg-gray-50'
                      : 'border-gray-600 hover:border-orange-500 bg-gray-800'
                  }`}>
                  
                  {referencePreview ? (
                    <img src={referencePreview} alt="Preview" className="w-full h-full object-contain" />
                  ) : (
                    <div className="text-center">
                      <div className="text-4xl mb-2">📷</div>
                      <p className={`text-sm ${
                        isLight ? 'text-gray-500' : 'text-gray-400'
                      }`}>
                        点击上传参考图片
                      </p>
                      <p className={`text-xs mt-1 ${
                        isLight ? 'text-gray-400' : 'text-gray-500'
                      }`}>
                        支持 JPG, PNG 格式
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Style Description */}
              <div>
                <label className={`block text-sm font-medium mb-2 ${
                  isLight ? 'text-gray-700' : 'text-gray-300'
                }`}>
                  风格描述
                </label>
                <textarea
                  value={styleDescription}
                  onChange={e => setStyleDescription(e.target.value)}
                  placeholder="描述你想要的字体风格，例如：优雅的宋体风格，笔画细腻，适合标题使用..."
                  rows={4}
                  className={`w-full rounded-xl px-4 py-3 text-sm border transition-colors resize-none ${
                    isLight
                      ? 'border-gray-300 bg-white text-gray-800 placeholder-gray-400 focus:border-orange-400 focus:ring-2 focus:ring-orange-100'
                      : 'border-gray-600 bg-gray-800 text-gray-200 placeholder-gray-500 focus:border-orange-500 focus:ring-2 focus:ring-orange-900'
                  }`}
                />
                <p className={`text-xs mt-1 ${
                  isLight ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  提示：详细的描述有助于生成更符合预期的字体
                </p>
              </div>

              {/* Generate Button */}
              <button
                onClick={handleGenerate}
                disabled={generating || !referenceImage || !styleDescription.trim()}
                className={`w-full py-3 rounded-xl font-medium text-white transition-all ${
                  generating || !referenceImage || !styleDescription.trim()
                    ? 'bg-gray-300 cursor-not-allowed'
                    : 'bg-gradient-to-r from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600 shadow-lg hover:shadow-xl'
                }`}>
                {generating ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin">⏳</span>
                    生成中...
                  </span>
                ) : (
                  '生成字体'
                )}
              </button>

              {/* Info */}
              <div className={`p-4 rounded-xl text-xs ${
                isLight ? 'bg-blue-50 text-blue-700' : 'bg-blue-900/30 text-blue-300'
              }`}>
                <div className="flex items-start gap-2">
                  <span className="text-base">ℹ️</span>
                  <div>
                    <p className="font-medium mb-1">生成说明：</p>
                    <ul className="space-y-0.5 list-disc list-inside">
                      <li>单字生成约需 3-5 秒</li>
                      <li>支持生成中文汉字、数字、英文字母</li>
                      <li>生成的字体可直接应用到画布元素</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* My Fonts Tab */}
          {activeTab === 'my-fonts' && (
            <div className="p-6">
              {myFonts.length === 0 ? (
                <div className="text-center py-16">
                  <div className="text-5xl mb-4">📝</div>
                  <p className={`text-sm ${
                    isLight ? 'text-gray-500' : 'text-gray-400'
                  }`}>
                    还没有生成过字体
                  </p>
                  <button
                    onClick={() => setActiveTab('generate')}
                    className="mt-4 px-6 py-2 rounded-lg bg-orange-500 text-white text-sm font-medium hover:bg-orange-600 transition-colors">
                    开始生成
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-4">
                  {myFonts.map((font) => (
                    <div
                      key={font.id}
                      className={`rounded-xl border p-4 transition-all cursor-pointer ${
                        isLight
                          ? 'border-gray-200 hover:border-orange-400 hover:shadow-lg bg-white'
                          : 'border-gray-700 hover:border-orange-500 hover:shadow-lg bg-gray-800'
                      }`}
                      onClick={() => handleUseFontInCanvas(font)}>
                      
                      {/* Sample Preview */}
                      <div className={`w-full h-32 rounded-lg mb-3 flex items-center justify-center overflow-hidden ${
                        isLight ? 'bg-gray-100' : 'bg-gray-700'
                      }`}>
                        {font.sample_url ? (
                          <img src={font.sample_url} alt={font.name} className="w-full h-full object-cover" />
                        ) : (
                          <span className="text-2xl">🔤</span>
                        )}
                      </div>

                      {/* Font Info */}
                      <h3 className={`font-semibold text-sm mb-1 truncate ${
                        isLight ? 'text-gray-800' : 'text-gray-200'
                      }`}>
                        {font.name}
                      </h3>
                      <p className={`text-xs mb-2 line-clamp-2 ${
                        isLight ? 'text-gray-500' : 'text-gray-400'
                      }`}>
                        {font.style_description}
                      </p>

                      {/* Status Badge */}
                      <div className="flex items-center justify-between">
                        <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                          font.status === 'complete'
                            ? 'bg-green-100 text-green-700'
                            : font.status === 'generating'
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-gray-100 text-gray-600'
                        }`}>
                          {font.status === 'complete' ? '✓ 已完成' : font.status === 'generating' ? '⏳ 生成中' : '等待中'}
                        </span>
                        <span className={`text-[10px] ${
                          isLight ? 'text-gray-400' : 'text-gray-500'
                        }`}>
                          {new Date(font.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
