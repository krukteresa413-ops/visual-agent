import { describe, expect, it } from 'vitest';
import { canRedo, canUndo, createHistory, record, redo, undo } from './history';

describe('canvas undo/redo history', () => {
  it('starts with the initial snapshot as present and nothing to undo/redo', () => {
    const h = createHistory('a');
    expect(h.present).toBe('a');
    expect(canUndo(h)).toBe(false);
    expect(canRedo(h)).toBe(false);
  });

  it('records snapshots and undoes back through them', () => {
    let h = createHistory('a');
    h = record(h, 'b');
    h = record(h, 'c');
    expect(h.present).toBe('c');
    expect(canUndo(h)).toBe(true);

    h = undo(h);
    expect(h.present).toBe('b');
    h = undo(h);
    expect(h.present).toBe('a');
    expect(canUndo(h)).toBe(false);
  });

  it('redoes after undo', () => {
    let h = createHistory('a');
    h = record(h, 'b');
    h = undo(h);
    expect(h.present).toBe('a');
    expect(canRedo(h)).toBe(true);

    h = redo(h);
    expect(h.present).toBe('b');
    expect(canRedo(h)).toBe(false);
  });

  it('clears the redo branch when a new snapshot is recorded after undo', () => {
    let h = createHistory('a');
    h = record(h, 'b');
    h = record(h, 'c');
    h = undo(h); // present = b, future = [c]
    expect(canRedo(h)).toBe(true);

    h = record(h, 'd'); // 分叉:future 被清空
    expect(h.present).toBe('d');
    expect(canRedo(h)).toBe(false);
    h = undo(h);
    expect(h.present).toBe('b');
  });

  it('ignores a snapshot that is reference-equal to the current present', () => {
    const obj = { n: 1 };
    let h = createHistory(obj);
    h = record(h, obj); // 同引用,不入栈
    expect(canUndo(h)).toBe(false);
    expect(h.past).toHaveLength(0);
  });

  it('drops the oldest snapshots beyond the limit', () => {
    let h = createHistory('s0', 3); // 最多保留 3 个历史(past)
    for (let i = 1; i <= 5; i += 1) h = record(h, `s${i}`);
    expect(h.present).toBe('s5');
    expect(h.past).toHaveLength(3);
    expect(h.past).toEqual(['s2', 's3', 's4']); // s0/s1 被丢弃

    h = undo(h); h = undo(h); h = undo(h);
    expect(h.present).toBe('s2');
    expect(canUndo(h)).toBe(false);
  });

  it('is a no-op when undoing with empty past or redoing with empty future', () => {
    const h = createHistory('a');
    expect(undo(h)).toBe(h);
    expect(redo(h)).toBe(h);
  });
});
