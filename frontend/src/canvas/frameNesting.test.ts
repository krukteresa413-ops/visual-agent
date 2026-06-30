import { describe, expect, it } from 'vitest';
import { absolutePosition, orderByParent, resolveContainment, type NestBox } from './frameNesting';

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
