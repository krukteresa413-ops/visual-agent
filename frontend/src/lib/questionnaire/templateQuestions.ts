// 图一:AI 追问问卷 — 复用「商业图视频」brief 模板字段(见 BriefReviewPanel 的 FIELD_CONFIG)。
// 纯数据 + 纯函数,便于单测。UI 在 QuestionnairePanel / AIChatPanel。

export type QuestionType = 'text' | 'single' | 'multi' | 'tags' | 'date';

export interface TemplateQuestion {
  key: string;
  label: string;
  icon: string;
  type: QuestionType;
  prompt: string;        // AI 追问语
  options?: string[];    // single / multi 的快选项(小弹窗)
  optional?: boolean;
}

export type AnswerValue = string | string[];

// 全量 12 字段,顺序即追问顺序
export const TEMPLATE_QUESTIONS: TemplateQuestion[] = [
  { key: 'product_name', label: '产品名', icon: '📦', type: 'text',
    prompt: '我们先从产品开始 —— 这次要做的产品叫什么名字?' },
  { key: 'brand_name', label: '品牌名', icon: '🏢', type: 'text', optional: true,
    prompt: '品牌名是什么?(没有可跳过)' },
  { key: 'category', label: '品类', icon: '🏷️', type: 'single', optional: true,
    options: ['美妆护肤', '食品饮料', '3C数码', '服饰鞋包', '家居家电', '母婴亲子', '宠物用品', '其他'],
    prompt: '它属于哪个品类?' },
  { key: 'target_audience', label: '目标受众', icon: '👥', type: 'single', optional: true,
    options: ['年轻女性', '年轻男性', '亲子家庭', 'Z世代', '职场白领', '银发族', '学生党'],
    prompt: '主要想打动哪类人群?' },
  { key: 'usage_scenarios', label: '使用场景', icon: '🎯', type: 'multi', optional: true,
    options: ['居家', '通勤', '旅行', '办公', '运动健身', '送礼', '节日', '户外'],
    prompt: '主要的使用场景有哪些?(可多选,也可输入)' },
  { key: 'selling_points', label: '核心卖点', icon: '💎', type: 'tags', optional: true,
    prompt: '核心卖点有哪些?用逗号或空格分隔输入。' },
  { key: 'brand_style', label: '品牌风格', icon: '🎨', type: 'single', optional: true,
    options: ['简约', '高级质感', '可爱', '科技感', '国潮', '复古', '自然清新', '轻奢'],
    prompt: '想要什么样的画面风格?' },
  { key: 'target_country', label: '目标国家/地区', icon: '🌍', type: 'single', optional: true,
    options: ['中国', '美国', '日本', '东南亚', '欧洲', '中东'],
    prompt: '主要投放到哪个国家或地区?' },
  { key: 'cultural_taboos', label: '文化禁忌', icon: '⚠️', type: 'text', optional: true,
    prompt: '有需要规避的文化禁忌或敏感点吗?(可跳过)' },
  { key: 'publish_platform', label: '发布平台', icon: '📱', type: 'multi', optional: true,
    options: ['抖音', '淘宝', '京东', '小红书', '拼多多', '微信', '美团', '亚马逊', '国际站'],
    prompt: '打算发布在哪些平台?' },
  { key: 'scheduled_date', label: '预发布日期', icon: '📅', type: 'date', optional: true,
    prompt: '计划什么时候发布?(可跳过)' },
  { key: 'promotional_event', label: '促销活动', icon: '🎉', type: 'single', optional: true,
    options: ['618', '双11', '双12', '年货节', '情人节', '日常', '无'],
    prompt: '是否配合某个促销节点?' },
];

const MULTI = (t: QuestionType) => t === 'multi' || t === 'tags';

/** 把原始输入(字符串或数组)规整为该题的标准答案。 */
export function normalizeAnswer(q: TemplateQuestion, raw: AnswerValue): AnswerValue {
  if (Array.isArray(raw)) return raw.filter(Boolean);
  const s = (raw ?? '').toString().trim();
  if (!s) return MULTI(q.type) ? [] : '';
  if (MULTI(q.type)) return s.split(/[,，\s]+/).filter(Boolean);
  return s;
}

/** 答案是否为空(用于「跳过」判定)。 */
export function isBlank(v: AnswerValue | undefined): boolean {
  if (v === undefined) return true;
  if (Array.isArray(v)) return v.length === 0;
  return v.trim() === '';
}

export function answerDisplay(v: AnswerValue | undefined): string {
  if (isBlank(v)) return '已跳过';
  return Array.isArray(v) ? v.join('、') : (v ?? '');
}

export interface BuiltBrief {
  brief: Record<string, AnswerValue>;
  prompt: string;
}

/** 把收集到的答案组装成 brief + 生成用的自然语言 prompt。 */
export function buildBriefFromAnswers(
  answers: Record<string, AnswerValue>,
  seed: string,
): BuiltBrief {
  const a: Record<string, AnswerValue> = { ...answers };
  if (isBlank(a.product_name)) a.product_name = seed.trim();

  const brief: Record<string, AnswerValue> = {};
  for (const q of TEMPLATE_QUESTIONS) {
    const v = a[q.key];
    if (!isBlank(v)) brief[q.key] = v as AnswerValue;
  }
  // 给编排/十 Agent 兼容的数组键
  if (Array.isArray(a.publish_platform) && a.publish_platform.length) {
    brief.target_platforms = a.publish_platform;
  }

  const j = (v: AnswerValue | undefined) => (Array.isArray(v) ? v.join('、') : (v || ''));
  const pn = j(a.product_name) || seed.trim();
  const parts: string[] = [`为「${pn}」生成营销视觉素材`];
  if (!isBlank(a.category)) parts.push(`品类:${j(a.category)}`);
  if (!isBlank(a.target_audience)) parts.push(`目标受众:${j(a.target_audience)}`);
  if (!isBlank(a.selling_points)) parts.push(`核心卖点:${j(a.selling_points)}`);
  if (!isBlank(a.brand_style)) parts.push(`风格:${j(a.brand_style)}`);
  if (!isBlank(a.usage_scenarios)) parts.push(`场景:${j(a.usage_scenarios)}`);
  if (!isBlank(a.publish_platform)) parts.push(`投放平台:${j(a.publish_platform)}`);
  if (!isBlank(a.target_country)) parts.push(`目标地区:${j(a.target_country)}`);
  if (!isBlank(a.promotional_event)) parts.push(`促销:${j(a.promotional_event)}`);

  return { brief, prompt: parts.join(',') + '。' };
}
