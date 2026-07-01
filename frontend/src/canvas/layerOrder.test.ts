import { describe, expect, it } from 'vitest';
import { reorderLayer } from './layerOrder';

// 便捷构造:N(id, zIndex?, parentId?)
const N = (id: string, zIndex?: number, parentId?: string) => ({ id, zIndex, parentId });

describe('reorderLayer — 图层顺序纯逻辑', () => {
  it('置顶:目标获得该组最高秩(稠密重排)', () => {
    const nodes = [N('a'), N('b'), N('c')]; // z 全 undefined → 底→顶 = a,b,c
    const m = reorderLayer(nodes, 'a', 'front');
    expect(m.get('b')).toBe(0);
    expect(m.get('c')).toBe(1);
    expect(m.get('a')).toBe(2);
  });

  it('置底:目标获得该组最低秩', () => {
    const nodes = [N('a'), N('b'), N('c')];
    const m = reorderLayer(nodes, 'c', 'back');
    expect(m.get('c')).toBe(0);
    expect(m.get('a')).toBe(1);
    expect(m.get('b')).toBe(2);
  });

  it('上移一层:与紧邻上方交换', () => {
    const nodes = [N('a'), N('b'), N('c')]; // 底→顶 a,b,c
    const m = reorderLayer(nodes, 'a', 'forward'); // a 上移 → b,a,c
    expect(m.get('b')).toBe(0);
    expect(m.get('a')).toBe(1);
    expect(m.get('c')).toBe(2);
  });

  it('下移一层:与紧邻下方交换', () => {
    const nodes = [N('a'), N('b'), N('c')]; // 底→顶 a,b,c
    const m = reorderLayer(nodes, 'c', 'backward'); // c 下移 → a,c,b
    expect(m.get('a')).toBe(0);
    expect(m.get('c')).toBe(1);
    expect(m.get('b')).toBe(2);
  });

  it('已在顶:置顶/上移为 no-op(空 Map)', () => {
    const nodes = [N('a'), N('b'), N('c')];
    expect(reorderLayer(nodes, 'c', 'front').size).toBe(0);
    expect(reorderLayer(nodes, 'c', 'forward').size).toBe(0);
  });

  it('已在底:置底/下移为 no-op(空 Map)', () => {
    const nodes = [N('a'), N('b'), N('c')];
    expect(reorderLayer(nodes, 'a', 'back').size).toBe(0);
    expect(reorderLayer(nodes, 'a', 'backward').size).toBe(0);
  });

  it('并列 z 与空洞:按 (z, 数组序) 归一后再操作', () => {
    // 数组序 a(z5), c(z undefined→0), b(z5);底→顶 by (z,idx) = c(0,1), a(5,0), b(5,2)
    const nodes = [N('a', 5), N('c'), N('b', 5)];
    const m = reorderLayer(nodes, 'c', 'front'); // c 置顶 → a,b,c
    expect(m.get('a')).toBe(0);
    expect(m.get('b')).toBe(1);
    expect(m.get('c')).toBe(2);
  });

  it('同层作用域:只影响同 parentId 的子节点组', () => {
    const nodes = [
      N('t1'), N('t2'), N('f'),
      N('c1', undefined, 'f'), N('c2', undefined, 'f'),
    ];
    const m = reorderLayer(nodes, 'c1', 'front'); // 仅在 {c1,c2}
    expect([...m.keys()].sort()).toEqual(['c1', 'c2']);
    expect(m.get('c2')).toBe(0);
    expect(m.get('c1')).toBe(1);
    expect(m.has('t1')).toBe(false);
    expect(m.has('f')).toBe(false);
  });

  it('顶层置顶只在顶层组内(不牵动画板子节点)', () => {
    const nodes = [N('t1'), N('t2'), N('f'), N('c1', undefined, 'f')];
    const m = reorderLayer(nodes, 't1', 'front'); // 顶层组 {t1,t2,f}
    expect([...m.keys()].sort()).toEqual(['f', 't1', 't2']);
    expect(m.has('c1')).toBe(false);
  });

  it('目标不存在:空 Map', () => {
    expect(reorderLayer([N('a')], 'zzz', 'front').size).toBe(0);
  });

  it('组内仅 1 个:no-op', () => {
    // solo 是唯一顶层节点(c1 属于画板 f 组) → 顶层组只有 solo,不可再排
    const nodes = [N('solo'), N('c1', undefined, 'f')];
    expect(reorderLayer(nodes, 'solo', 'front').size).toBe(0);
  });
});
