export type NodeBounds = { x: number; y: number; width: number; height: number };
export type ViewportTransform = { x: number; y: number; zoom: number };

export function actionBarAnchor(bounds: NodeBounds, viewport: ViewportTransform) {
  const left = viewport.x + (bounds.x + bounds.width / 2) * viewport.zoom;
  const top = Math.max(8, viewport.y + bounds.y * viewport.zoom - 46);
  return { left: Math.round(left), top: Math.round(top) };
}
