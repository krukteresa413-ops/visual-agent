// 对齐吸附的纯几何:给定「被拖拽矩形」与「其他矩形」(均为绝对坐标),在阈值内找最近的
// 对齐线,返回吸附后的绝对左上角 + 参考线绝对坐标。无 React/DOM 依赖,便于单测。
//
// 设计要点(第一性原理):
//  - 坐标全为「绝对」。画布里子节点 position 是相对父画板的,故调用方(CanvasFlow)负责
//    相对↔绝对转换,本函数只做纯几何,不关心嵌套。
//  - 每轴 5 条候选对齐线:同边 左-左 / 中-中 / 右-右,异边 左-右 / 右-左(相邻贴合)。
//    覆盖设计工具最常用的对齐语义,又不至于像 9 组合那样产生噪声吸附。
//  - X、Y 两轴独立求解:一次拖拽可能只在一个轴发生吸附(另一轴自由)。
//  - 阈值内取「最近」命中(gap 严格更小才替换),保证多个目标时吸最近的那条。

export interface SnapRect {
  x: number; // 左
  y: number; // 上
  width: number;
  height: number;
}

export interface HelperLinesResult {
  snapX?: number;      // 吸附后矩形的绝对左(x);未命中为 undefined
  snapY?: number;      // 吸附后矩形的绝对上(y);未命中为 undefined
  vertical?: number;   // 竖直参考线的绝对 X;未命中为 undefined
  horizontal?: number; // 水平参考线的绝对 Y;未命中为 undefined
}

// 候选三元组:[被拖拽矩形的参考点, 目标参考点(=参考线坐标), 吸附后矩形的新左上角坐标]
type Candidate = [number, number, number];

export function getHelperLines(dragged: SnapRect, others: SnapRect[], distance: number): HelperLinesResult {
  const result: HelperLinesResult = {};

  const aL = dragged.x;
  const aR = dragged.x + dragged.width;
  const aCx = dragged.x + dragged.width / 2;
  const aT = dragged.y;
  const aB = dragged.y + dragged.height;
  const aCy = dragged.y + dragged.height / 2;

  let bestX = distance; // 允许等于阈值命中(<=);越近越优,故记录已命中的最小 gap
  let bestY = distance;
  let hitX = false;
  let hitY = false;

  for (const o of others) {
    const bL = o.x;
    const bR = o.x + o.width;
    const bCx = o.x + o.width / 2;
    const bT = o.y;
    const bB = o.y + o.height;
    const bCy = o.y + o.height / 2;

    // X 轴(竖直参考线)候选
    const xCands: Candidate[] = [
      [aL, bL, bL],                          // 左-左
      [aR, bR, bR - dragged.width],          // 右-右
      [aCx, bCx, bCx - dragged.width / 2],   // 中-中
      [aL, bR, bR],                          // 左贴右
      [aR, bL, bL - dragged.width],          // 右贴左
    ];
    for (const [d, lineX, newX] of xCands) {
      const gap = Math.abs(d - lineX);
      if (gap <= distance && (!hitX || gap < bestX)) {
        bestX = gap;
        hitX = true;
        result.snapX = newX;
        result.vertical = lineX;
      }
    }

    // Y 轴(水平参考线)候选
    const yCands: Candidate[] = [
      [aT, bT, bT],                           // 上-上
      [aB, bB, bB - dragged.height],          // 下-下
      [aCy, bCy, bCy - dragged.height / 2],   // 中-中
      [aT, bB, bB],                           // 上贴下
      [aB, bT, bT - dragged.height],          // 下贴上
    ];
    for (const [d, lineY, newY] of yCands) {
      const gap = Math.abs(d - lineY);
      if (gap <= distance && (!hitY || gap < bestY)) {
        bestY = gap;
        hitY = true;
        result.snapY = newY;
        result.horizontal = lineY;
      }
    }
  }

  return result;
}
