import { describe, expect, it } from 'vitest';
import {
  TEMPLATE_QUESTIONS,
  normalizeAnswer,
  isBlank,
  answerDisplay,
  buildBriefFromAnswers,
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
});
