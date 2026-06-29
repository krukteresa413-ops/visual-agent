import { describe, expect, it } from 'vitest';
import {
  TEMPLATE_QUESTIONS,
  normalizeAnswer,
  isBlank,
  answerDisplay,
  buildBriefFromAnswers,
  suggestSellingPoints,
  isBriefSufficient,
} from './templateQuestions';

describe('templateQuestions', () => {
  it('covers all 12 商业图视频 template fields', () => {
    expect(TEMPLATE_QUESTIONS).toHaveLength(12);
    const keys = TEMPLATE_QUESTIONS.map((q) => q.key);
    expect(keys).toContain('publish_platform');
    expect(keys).toContain('promotional_event');
  });

  it('platform question offers quick-pick options incl. 抖音/淘宝', () => {
    const q = TEMPLATE_QUESTIONS.find((x) => x.key === 'publish_platform')!;
    expect(q.type).toBe('multi');
    expect(q.options).toEqual(expect.arrayContaining(['抖音', '淘宝']));
  });

  describe('normalizeAnswer', () => {
    const tags = TEMPLATE_QUESTIONS.find((q) => q.key === 'selling_points')!;
    const single = TEMPLATE_QUESTIONS.find((q) => q.key === 'category')!;

    it('splits tags input on comma/space/全角逗号', () => {
      expect(normalizeAnswer(tags, '保湿, 美白 抗老，提亮')).toEqual(['保湿', '美白', '抗老', '提亮']);
    });
    it('keeps arrays as-is for multi', () => {
      expect(normalizeAnswer(tags, ['a', 'b'])).toEqual(['a', 'b']);
    });
    it('trims single text', () => {
      expect(normalizeAnswer(single, '  美妆护肤 ')).toBe('美妆护肤');
    });
    it('empty -> [] for multi, "" for single', () => {
      expect(normalizeAnswer(tags, '')).toEqual([]);
      expect(normalizeAnswer(single, '   ')).toBe('');
    });
  });

  describe('isBlank / answerDisplay', () => {
    it('treats empty array and empty string as blank', () => {
      expect(isBlank([])).toBe(true);
      expect(isBlank('')).toBe(true);
      expect(isBlank(undefined)).toBe(true);
      expect(isBlank(['x'])).toBe(false);
    });
    it('renders skipped vs joined', () => {
      expect(answerDisplay([])).toBe('已跳过');
      expect(answerDisplay(['抖音', '淘宝'])).toBe('抖音、淘宝');
    });
  });

  describe('buildBriefFromAnswers', () => {
    it('falls back product_name to seed and builds brief + prompt', () => {
      const { brief, prompt } = buildBriefFromAnswers(
        { category: '美妆护肤', publish_platform: ['抖音', '小红书'], selling_points: ['保湿', '美白'] },
        '白色的大象',
      );
      expect(brief.product_name).toBe('白色的大象');
      expect(brief.category).toBe('美妆护肤');
      expect(brief.target_platforms).toEqual(['抖音', '小红书']);
      expect(prompt).toContain('白色的大象');
      expect(prompt).toContain('投放平台:抖音、小红书');
      expect(prompt).toContain('核心卖点:保湿、美白');
    });

    it('omits blank fields from brief', () => {
      const { brief } = buildBriefFromAnswers({ brand_name: '', usage_scenarios: [] }, 'seed');
      expect(brief.brand_name).toBeUndefined();
      expect(brief.usage_scenarios).toBeUndefined();
    });
  });

  describe('isBriefSufficient (需求一 自动判断是否追问)', () => {
    it('够详细:产品名 + ≥2 关键属性 -> 直接出图', () => {
      expect(isBriefSufficient({ product_name: '防晒衣', category: '服饰鞋包', selling_points: ['UPF50+'] })).toBe(true);
    });
    it('只有产品名 -> 不够,需追问', () => {
      expect(isBriefSufficient({ product_name: '防晒衣' })).toBe(false);
    });
    it('产品名 + 仅1项属性 -> 不够', () => {
      expect(isBriefSufficient({ product_name: '防晒衣', category: '服饰鞋包' })).toBe(false);
    });
    it('无产品名 -> 永远不够', () => {
      expect(isBriefSufficient({ category: '服饰鞋包', selling_points: ['x'], brand_style: '简约' })).toBe(false);
    });
    it('空数组/空串不计入关键属性', () => {
      expect(isBriefSufficient({ product_name: 'X', selling_points: [], brand_style: '' })).toBe(false);
    });
  });

  describe('suggestSellingPoints (图一 大胆猜测)', () => {
    it('returns category-specific guesses for known category', () => {
      const s = suggestSellingPoints({ category: '服饰鞋包' });
      expect(s).toEqual(expect.arrayContaining(['显瘦', '百搭']));
      expect(s.length).toBeGreaterThan(0);
      expect(s.length).toBeLessThanOrEqual(10);
    });
    it('falls back to universal guesses for unknown/empty category', () => {
      const s = suggestSellingPoints({});
      expect(s).toEqual(expect.arrayContaining(['高性价比']));
    });
    it('dedupes', () => {
      const s = suggestSellingPoints({ category: '美妆护肤' });
      expect(new Set(s).size).toBe(s.length);
    });
  });
});
