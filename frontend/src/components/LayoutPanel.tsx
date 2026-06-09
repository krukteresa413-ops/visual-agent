/**
 * LayoutPanel — 排版布局方案展示。
 * 接收 layout_plan JSON，渲染像素级排版预览。
 */

interface LayoutElement {
  element_type: string;
  content: string;
  x_pct: number;
  y_pct: number;
  width_pct: number;
  height_pct: number;
  font_size_pt: number;
  font_weight: string;
  color: string;
  alignment: string;
  z_index: number;
}

interface MainImageLayout {
  canvas_width: number;
  canvas_height: number;
  background_color: string;
  layout_strategy: string;
  title_hierarchy: string;
  elements: LayoutElement[];
  platform_adaptations?: Record<string, any>;
}

interface DetailPageModule {
  module_name: string;
  height_px: number;
  background_color: string;
  layout_type: string;
  elements: LayoutElement[];
}

interface DetailPageLayout {
  canvas_width: number;
  canvas_height: number;
  module_order: string[];
  modules: DetailPageModule[];
}

interface SellingPointLayout {
  icon_position: string;
  text_alignment: string;
  elements: LayoutElement[];
}

interface LayoutPlan {
  project_id: number;
  platform_id?: string;
  global_style_notes: string;
  typography_rules: string;
  color_system: string;
  main_image_layout?: MainImageLayout;
  detail_page_layout?: DetailPageLayout;
  selling_point_layouts?: SellingPointLayout[];
  scene_image_layouts?: any[];
  social_post_layout?: any;
}

const ELEMENT_COLORS: Record<string, string> = {
  title: '#f59e0b',
  subtitle: '#fbbf24',
  body_text: '#9ca3af',
  cta_button: '#ef4444',
  product_image: '#3b82f6',
  scene_image: '#8b5cf6',
  logo: '#10b981',
  badge: '#ec4899',
  divider: '#6b7280',
  price_tag: '#f97316',
  selling_point_icon: '#06b6d4',
};

const ELEMENT_LABELS: Record<string, string> = {
  title: '标题',
  subtitle: '副标题',
  body_text: '正文',
  cta_button: 'CTA',
  product_image: '产品图',
  scene_image: '场景图',
  logo: 'Logo',
  badge: '标签',
  divider: '分割线',
  price_tag: '价格',
  selling_point_icon: '图标',
};

function MainImageLayoutPreview({ layout }: { layout: MainImageLayout }) {
  const scale = 0.5;
  const w = layout.canvas_width * scale;
  const h = layout.canvas_height * scale;

  return (
    <div className="mb-6">
      <h3 className="text-sm font-medium text-orange-300 mb-2">主图排版</h3>
      <p className="text-xs text-gray-500 mb-2">策略：{layout.layout_strategy}</p>
      <p className="text-xs text-gray-500 mb-3">层级：{layout.title_hierarchy}</p>
      <div
        className="relative border border-gray-700 rounded-lg mx-auto"
        style={{ width: w, height: h, backgroundColor: layout.background_color }}
      >
        {layout.elements.map((el, i) => {
          const color = ELEMENT_COLORS[el.element_type] || '#6b7280';
          return (
            <div
              key={i}
              className="absolute border border-dashed flex items-center justify-center overflow-hidden"
              style={{
                left: `${el.x_pct}%`,
                top: `${el.y_pct}%`,
                width: `${el.width_pct}%`,
                height: `${el.height_pct}%`,
                borderColor: color + '80',
                backgroundColor: color + '15',
                zIndex: el.z_index,
                fontSize: Math.max(8, el.font_size_pt * scale * 0.7),
                fontWeight: el.font_weight === 'bold' ? 700 : 400,
                color: el.color,
                textAlign: el.alignment as any,
              }}
              title={`${ELEMENT_LABELS[el.element_type] || el.element_type}: ${el.content}`}
            >
              {el.content.length > 30 ? el.content.slice(0, 28) + '…' : el.content}
            </div>
          );
        })}
        {layout.elements.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-xs text-gray-400">
            暂无排版元素
          </div>
        )}
      </div>
      <p className="text-[10px] text-gray-600 text-center mt-1">
        {layout.canvas_width}×{layout.canvas_height}px（预览缩放 {Math.round(scale * 100)}%）
      </p>
    </div>
  );
}

function DetailPageLayoutPreview({ layout }: { layout: DetailPageLayout }) {
  return (
    <div className="mb-6">
      <h3 className="text-sm font-medium text-purple-300 mb-3">详情页结构</h3>
      <div className="space-y-1">
        {layout.module_order.map((name, i) => (
          <div key={i} className="flex items-center gap-3 text-xs">
            <span className="text-gray-600 w-6 text-right">{i + 1}.</span>
            <span className="bg-gray-800 px-2 py-1 rounded text-gray-300">{name}</span>
            {layout.modules[i] && (
              <span className="text-gray-600">
                {layout.modules[i].layout_type} · {layout.modules[i].height_px}px
              </span>
            )}
          </div>
        ))}
      </div>
      {layout.modules.length > 0 && (
        <div className="mt-3 space-y-2">
          {layout.modules.map((mod, i) =>
            mod.elements.length > 0 ? (
              <div key={i} className="bg-gray-900 rounded-lg p-3 text-xs">
                <p className="text-gray-400 mb-1">模块 {i + 1}：{mod.module_name}</p>
                <div className="flex flex-wrap gap-1">
                  {mod.elements.map((el, j) => (
                    <span key={j} className="px-1.5 py-0.5 rounded text-[10px]"
                      style={{ backgroundColor: (ELEMENT_COLORS[el.element_type] || '#6b7280') + '30',
                               color: ELEMENT_COLORS[el.element_type] || '#6b7280' }}>
                      {ELEMENT_LABELS[el.element_type] || el.element_type}
                    </span>
                  ))}
                </div>
              </div>
            ) : null
          )}
        </div>
      )}
    </div>
  );
}

function SellingPointLayoutsPreview({ layouts }: { layouts?: SellingPointLayout[] }) {
  if (!layouts?.length) return null;
  return (
    <div className="mb-6">
      <h3 className="text-sm font-medium text-green-300 mb-3">卖点模块排版</h3>
      <div className="grid grid-cols-3 gap-2">
        {layouts.map((sp, i) => (
          <div key={i} className="bg-gray-900 rounded-lg p-3 text-xs">
            <p className="text-gray-400 mb-1">卖点 {i + 1}</p>
            <p className="text-gray-500">图标位置：{sp.icon_position}</p>
            <p className="text-gray-500">文字对齐：{sp.text_alignment}</p>
            {sp.elements.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {sp.elements.map((el, j) => (
                  <span key={j} className="text-[10px] px-1.5 py-0.5 rounded"
                    style={{ backgroundColor: (ELEMENT_COLORS[el.element_type] || '#6b7280') + '30' }}>
                    {ELEMENT_LABELS[el.element_type] || el.element_type}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function LayoutPanel({ layout }: { layout: LayoutPlan }) {
  if (!layout) {
    return <p className="text-gray-500 text-sm text-center py-8">暂无排版方案</p>;
  }

  return (
    <div className="space-y-6">
      {/* 全局排版说明 */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-gray-900 rounded-lg p-3">
          <p className="text-[10px] text-gray-500 mb-1">排版风格</p>
          <p className="text-xs text-gray-200">{layout.global_style_notes || '未指定'}</p>
        </div>
        <div className="bg-gray-900 rounded-lg p-3">
          <p className="text-[10px] text-gray-500 mb-1">字体规则</p>
          <p className="text-xs text-gray-200">{layout.typography_rules || '未指定'}</p>
        </div>
        <div className="bg-gray-900 rounded-lg p-3">
          <p className="text-[10px] text-gray-500 mb-1">配色</p>
          <p className="text-xs text-gray-200">{layout.color_system || '未指定'}</p>
        </div>
      </div>

      {/* 主图排版可视化 */}
      {layout.main_image_layout && (
        <MainImageLayoutPreview layout={layout.main_image_layout} />
      )}

      {/* 详情页结构 */}
      {layout.detail_page_layout && (
        <DetailPageLayoutPreview layout={layout.detail_page_layout} />
      )}

      {/* 卖点模块排版 */}
      {layout.selling_point_layouts && layout.selling_point_layouts.length > 0 && (
        <SellingPointLayoutsPreview layouts={layout.selling_point_layouts} />
      )}

      {/* 场景图布局（简化版） */}
      {layout.scene_image_layouts && layout.scene_image_layouts.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-blue-300 mb-2">场景图排版</h3>
          <div className="flex flex-wrap gap-2">
            {layout.scene_image_layouts.map((sl: any, i: number) => (
              <div key={i} className="bg-gray-900 rounded-lg px-3 py-2 text-xs">
                <span className="text-gray-400">场景 {i + 1}：</span>
                <span className="text-gray-300">{sl.text_overlay_position || '无文字'}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 提示：尺寸适配信息 */}
      {layout.main_image_layout?.platform_adaptations && (
        <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-3 text-xs text-gray-500">
          已包含多平台尺寸适配规则
        </div>
      )}
    </div>
  );
}
