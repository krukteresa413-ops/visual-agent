import { describe, expect, it } from 'vitest';
import { absolutePosition, fitFrameToChildren, frameUnderPoint, orderByParent, resolveContainment, type NestBox } from './frameNesting';

const box = (id: string, type: string, x: number, y: number, w = 40, h = 40, parentId?: string): NestBox => ({
  id, type, parentId, position: { x, y }, width: w, height: h,
});

describe('orderByParent', () => {
  it('emits parent before child even when child comes first', () => {
    const items = [{ id: 'child', parentId: 'frame' }, { id: 'frame' }];
    expect(orderByParent(items).map((i) => i.id)).toEqual(['frame', 'child']);
  });

  it('preserves order of unrelated roots', () => {
    const items = [{ id: 'a' }, { id: 'b' }, { id: 'c' }];
    expect(orderByParent(items).map((i) => i.id)).toEqual(['a', 'b', 'c']);
  });

  it('treats a node with a missing parent as a root (no crash)', () => {
    const items = [{ id: 'orphan', parentId: 'gone' }, { id: 'r' }];
    expect(orderByParent(items).map((i) => i.id)).toEqual(['orphan', 'r']);
  });

  it('does not infinite-loop on a parent cycle', () => {
    const items = [{ id: 'a', parentId: 'b' }, { id: 'b', parentId: 'a' }];
    expect(orderByParent(items).map((i) => i.id).sort()).toEqual(['a', 'b']);
  });
});

describe('absolutePosition', () => {
  it('returns position as-is for a top-level node', () => {
    const nodes = [box('n', 'shape', 30, 40)];
    expect(absolutePosition(nodes[0], nodes)).toEqual({ x: 30, y: 40 });
  });

  it('adds the parent position for a child node', () => {
    const nodes = [box('frame', 'frame', 100, 100, 400, 300), box('child', 'shape', 50, 60, 40, 40, 'frame')];
    expect(absolutePosition(nodes[1], nodes)).toEqual({ x: 150, y: 160 });
  });
});

describe('resolveContainment', () => {
  const frame = (): NestBox => box('F', 'frame', 100, 100, 400, 300);

  it('reparents a top-level node dropped inside a frame (abs → relative)', () => {
    const nodes = [frame(), box('A', 'shape', 150, 150)]; // center (170,170) ∈ F
    expect(resolveContainment('A', nodes)).toEqual({ parentId: 'F', position: { x: 50, y: 50 } });
  });

  it('un-parents a child dragged outside its frame (relative → abs)', () => {
    const nodes = [frame(), box('A', 'shape', 500, 500, 40, 40, 'F')]; // abs (600,600), outside F
    expect(resolveContainment('A', nodes)).toEqual({ parentId: null, position: { x: 600, y: 600 } });
  });

  it('returns null when a child stays inside its current frame', () => {
    const nodes = [frame(), box('A', 'shape', 50, 50, 40, 40, 'F')]; // abs (150,150), still ∈ F
    expect(resolveContainment('A', nodes)).toBeNull();
  });

  it('returns null for a top-level node over empty canvas', () => {
    const nodes = [frame(), box('A', 'shape', 2000, 2000)];
    expect(resolveContainment('A', nodes)).toBeNull();
  });

  it('never reparents a frame itself', () => {
    const nodes = [frame(), box('F2', 'frame', 120, 120, 100, 100)]; // F2 center inside F
    expect(resolveContainment('F2', nodes)).toBeNull();
  });

  it('picks the innermost (smallest) frame when frames overlap', () => {
    const outer = box('OUT', 'frame', 0, 0, 800, 600);
    const inner = box('IN', 'frame', 100, 100, 200, 200);
    const node = box('A', 'shape', 150, 150); // center (170,170) ∈ both
    expect(resolveContainment('A', [outer, inner, node])?.parentId).toBe('IN');
  });
});

describe('frameUnderPoint (拖入高亮命中规则)', () => {
  it('命中:点落入画板返回其 id', () => {
    const nodes = [box('F', 'frame', 100, 100, 400, 300)];
    expect(frameUnderPoint(170, 170, nodes)).toBe('F');
  });

  it('未命中:点在画板外返回 null', () => {
    const nodes = [box('F', 'frame', 100, 100, 400, 300)];
    expect(frameUnderPoint(50, 50, nodes)).toBeNull();
  });

  it('重叠取最内层(面积最小)', () => {
    const outer = box('OUT', 'frame', 0, 0, 800, 600);
    const inner = box('IN', 'frame', 100, 100, 200, 200);
    expect(frameUnderPoint(170, 170, [outer, inner])).toBe('IN');
  });

  it('排除 excludeId(拖画板不吸自己)', () => {
    const nodes = [box('F', 'frame', 100, 100, 400, 300)];
    expect(frameUnderPoint(170, 170, nodes, 'F')).toBeNull();
  });

  it('只认 frame 类型(shape 不算画板)', () => {
    const nodes = [box('S', 'shape', 100, 100, 400, 300)];
    expect(frameUnderPoint(170, 170, nodes)).toBeNull();
  });
});

describe('fitFrameToChildren (画板适应内容)', () => {
  it('无子节点返回 null(不改)', () => {
    const nodes = [box('F', 'frame', 100, 100, 400, 300)];
    expect(fitFrameToChildren('F', nodes)).toBeNull();
  });

  it('shrink-wrap 到子包围盒 + padding, 且子视觉位置不动', () => {
    const nodes = [
      box('F', 'frame', 100, 100, 400, 300),
      box('A', 'shape', 50, 60, 40, 40, 'F'), // 相对; 绝对 (150,160)
    ];
    const fit = fitFrameToChildren('F', nodes, 24)!;
    expect(fit.position).toEqual({ x: 126, y: 136 });
    expect(fit.width).toBe(88);
    expect(fit.height).toBe(88);
    const a = fit.children.find((c) => c.id === 'A')!;
    expect(a.position).toEqual({ x: 24, y: 24 });
    // 新父绝对 + 子新相对 = 原子绝对 → 视觉不动
    expect({ x: fit.position.x + a.position.x, y: fit.position.y + a.position.y }).toEqual({ x: 150, y: 160 });
  });

  it('多子节点取整体包围盒', () => {
    const nodes = [
      box('F', 'frame', 0, 0, 500, 500),
      box('A', 'shape', 100, 100, 50, 50, 'F'), // 相对 bbox [100,100]-[150,150]
      box('B', 'shape', 200, 220, 60, 40, 'F'), // 相对 bbox [200,220]-[260,260]
    ];
    const fit = fitFrameToChildren('F', nodes, 10)!;
    expect(fit.position).toEqual({ x: 90, y: 90 }); // 0 + 100 - 10
    expect(fit.width).toBe(180);  // (260-100) + 20
    expect(fit.height).toBe(180); // (260-100) + 20
  });
});
