import { describe, expect, it } from 'vitest';
import { getHelperLines, type SnapRect } from './helperLines';

const D = 6; // 默认阈值

describe('getHelperLines 对齐吸附纯几何', () => {
  it('无其他矩形时不吸附', () => {
    const dragged: SnapRect = { x: 100, y: 100, width: 50, height: 40 };
    expect(getHelperLines(dragged, [], D)).toEqual({});
  });

  it('左-左对齐:被拖拽的左边接近目标左边则吸到目标左', () => {
    const dragged: SnapRect = { x: 103, y: 500, width: 50, height: 40 }; // 左=103
    const other: SnapRect = { x: 100, y: 0, width: 80, height: 60 };     // 左=100,gap=3
    const r = getHelperLines(dragged, [other], D);
    expect(r.snapX).toBe(100);      // 新左=100
    expect(r.vertical).toBe(100);   // 参考线在 x=100
    expect(r.snapY).toBeUndefined();
    expect(r.horizontal).toBeUndefined();
  });

  it('中-中对齐:水平中线接近则吸中', () => {
    // 目标中心 x=140;被拖拽宽 50,若要中心=140 则左=115。给左=112(中心137,gap3)
    const dragged: SnapRect = { x: 112, y: 500, width: 50, height: 40 };
    const other: SnapRect = { x: 100, y: 0, width: 80, height: 60 }; // 中心 x=140
    const r = getHelperLines(dragged, [other], D);
    expect(r.snapX).toBe(115);    // 115+25=140=目标中心
    expect(r.vertical).toBe(140);
  });

  it('右-右对齐:右边接近目标右边则吸右', () => {
    const other: SnapRect = { x: 100, y: 0, width: 80, height: 60 }; // 右=180
    const dragged: SnapRect = { x: 128, y: 500, width: 50, height: 40 }; // 右=178,gap2
    const r = getHelperLines(dragged, [other], D);
    expect(r.snapX).toBe(130);    // 130+50=180
    expect(r.vertical).toBe(180);
  });

  it('右贴左:被拖拽右边接近目标左边(相邻贴合)', () => {
    const other: SnapRect = { x: 300, y: 0, width: 80, height: 60 }; // 左=300
    const dragged: SnapRect = { x: 248, y: 500, width: 50, height: 40 }; // 右=298,gap2
    const r = getHelperLines(dragged, [other], D);
    expect(r.snapX).toBe(250);    // 250+50=300=目标左
    expect(r.vertical).toBe(300);
  });

  it('超过阈值不吸附(同尺寸偏移7,5条候选全超阈值)', () => {
    // 同尺寸时 左-左/中-中/右-右 gap 全等于 x 偏移量;取 7(>6)且异边组合更远 → 全不吸。
    // (注:若目标与被拖拽尺寸不同,即便某条边超阈值,中心线仍可能落在阈值内而吸附——故此处用同尺寸。)
    const dragged: SnapRect = { x: 107, y: 500, width: 50, height: 40 };
    const other: SnapRect = { x: 100, y: 0, width: 50, height: 40 };
    const r = getHelperLines(dragged, [other], D);
    expect(r.snapX).toBeUndefined();
    expect(r.vertical).toBeUndefined();
  });

  it('恰好等于阈值仍吸附(<=)', () => {
    const dragged: SnapRect = { x: 106, y: 500, width: 50, height: 40 }; // gap=6
    const other: SnapRect = { x: 100, y: 0, width: 80, height: 60 };
    expect(getHelperLines(dragged, [other], D).snapX).toBe(100);
  });

  it('Y 轴:上-上对齐独立于 X', () => {
    const dragged: SnapRect = { x: 999, y: 203, width: 50, height: 40 }; // 上=203,X 远离
    const other: SnapRect = { x: 0, y: 200, width: 80, height: 60 };     // 上=200,gap3
    const r = getHelperLines(dragged, [other], D);
    expect(r.snapY).toBe(200);
    expect(r.horizontal).toBe(200);
    expect(r.snapX).toBeUndefined(); // X 不吸
  });

  it('X 与 Y 可同时吸附到不同目标', () => {
    const dragged: SnapRect = { x: 102, y: 302, width: 50, height: 40 };
    const vTarget: SnapRect = { x: 100, y: -999, width: 20, height: 20 }; // 只提供竖直对齐(左=100)
    const hTarget: SnapRect = { x: -999, y: 300, width: 20, height: 20 }; // 只提供水平对齐(上=300)
    const r = getHelperLines(dragged, [vTarget, hTarget], D);
    expect(r.snapX).toBe(100);
    expect(r.snapY).toBe(300);
  });

  it('多个目标时吸最近的一条', () => {
    const dragged: SnapRect = { x: 104, y: 500, width: 50, height: 40 }; // 左=104
    const near: SnapRect = { x: 105, y: 0, width: 30, height: 30 };      // 左=105,gap1
    const far: SnapRect = { x: 100, y: 0, width: 30, height: 30 };       // 左=100,gap4
    const r = getHelperLines(dragged, [far, near], D);
    expect(r.snapX).toBe(105);    // 吸到更近的 105,而非先出现的 100
    expect(r.vertical).toBe(105);
  });
});
