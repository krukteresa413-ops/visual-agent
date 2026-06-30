import getStroke from 'perfect-freehand';

// perfect-freehand 封装:把采样点 → 笔触轮廓多边形 → 可填充的 SVG path。
export { getStroke };

export const strokeOptions = (size: number) => ({
  size,
  thinning: 0.5,
  smoothing: 0.5,
  streamline: 0.5,
  simulatePressure: true,
});

export function getSvgPathFromStroke(stroke: number[][]): string {
  if (!stroke.length) return '';
  const first = stroke[0];
  const d: (string | number)[] = ['M', first[0], first[1], 'Q'];
  for (let i = 0; i < stroke.length; i += 1) {
    const [x0, y0] = stroke[i];
    const [x1, y1] = stroke[(i + 1) % stroke.length];
    d.push(x0, y0, (x0 + x1) / 2, (y0 + y1) / 2);
  }
  d.push('Z');
  return d.join(' ');
}
