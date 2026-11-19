import { stateSize } from './stateSize';
export interface Point { x: number; y: number }
// Keep the 13px label close to its edge while leaving a small visual gap.
const LABEL_OFFSET = 11;
const toward = (a: Point, b: Point, fallback: Point, radius: number): Point => {
  if (Math.hypot(b.x - a.x, b.y - a.y) < .001) b = fallback;
  const length = Math.hypot(b.x - a.x, b.y - a.y) || 1;
  return { x: a.x + (b.x - a.x) * radius / length, y: a.y + (b.y - a.y) * radius / length };
};

/** SVG curves terminate at the circular states, independently of hidden handles. */
export function transitionGeometry(a: Point, b: Point, bend: number, loop: boolean, curve?: Point, sourceRadius = 32, targetRadius = 32) {
  if (loop || Math.hypot(b.x - a.x, b.y - a.y) < 1) {
    {
      curve ??= { x: 0, y: -(sourceRadius + 64 + Math.abs(bend)) };
      const length = Math.hypot(curve.x, curve.y);
      const direction = length > 1 ? { x: curve.x / length, y: curve.y / length } : { x: 0, y: -1 };
      const perpendicular = { x: -direction.y, y: direction.x };
      const size = Math.max(sourceRadius * 1.8, sourceRadius + 40, length);
      const at = (forward: number, sideways: number) => ({ x: a.x + direction.x * forward + perpendicular.x * sideways,
        y: a.y + direction.y * forward + perpendicular.y * sideways });
      const forward = sourceRadius * 25 / 32, sideways = Math.sqrt(sourceRadius ** 2 - forward ** 2);
      const start = at(forward, -sideways), end = at(forward, sideways);
      const c1 = at(size, -size * .7), c2 = at(size, size * .7);
      return { start, end, control: curve, label: at(forward * .25 + .75 * size + LABEL_OFFSET, 0),
        pointAt: (t: number): Point => ({
          x: (1-t)**3*start.x + 3*(1-t)**2*t*c1.x + 3*(1-t)*t*t*c2.x + t**3*end.x,
          y: (1-t)**3*start.y + 3*(1-t)**2*t*c1.y + 3*(1-t)*t*t*c2.y + t**3*end.y }),
        path: `M ${start.x} ${start.y} C ${c1.x} ${c1.y}, ${c2.x} ${c2.y}, ${end.x} ${end.y}` };
    }
  }
  const length = Math.hypot(b.x - a.x, b.y - a.y);
  const offset = curve ?? { x: -(b.y - a.y) * bend / length, y: (b.x - a.x) * bend / length };
  const control = { x: (a.x + b.x) / 2 + offset.x, y: (a.y + b.y) / 2 + offset.y };
  const start = toward(a, control, b, sourceRadius), end = toward(b, control, a, targetRadius);
  // Offset the label along the midpoint normal, rather than masking the curve.
  const dx = end.x - start.x, dy = end.y - start.y;
  const tangentLength = Math.hypot(dx, dy) || 1;
  const side = dx >= 0 ? -1 : 1;
  return { start, end, control: offset, path: `M ${start.x} ${start.y} Q ${control.x} ${control.y} ${end.x} ${end.y}`,
    pointAt: (t: number): Point => ({ x: (1-t)**2*start.x + 2*(1-t)*t*control.x + t*t*end.x,
      y: (1-t)**2*start.y + 2*(1-t)*t*control.y + t*t*end.y }),
    label: { x: .25 * start.x + .5 * control.x + .25 * end.x - side * dy / tangentLength * LABEL_OFFSET,
      y: .25 * start.y + .5 * control.y + .25 * end.y + side * dx / tangentLength * LABEL_OFFSET } };
}

/** O(Q) hit test in graph coordinates, independent of zoom and DOM capture. */
export function hitState(states: readonly { id: string; x: number; y: number; label?: string; size?: number }[], point: Point): string | null {
  return [...states].reverse().find(s => { const radius = stateSize(s) / 2;
    return Math.hypot(point.x - s.x - radius, point.y - s.y - radius) <= radius; })?.id ?? null;
}

/** Smooth free-end rope, following the chosen departure direction. */
export function previewRope(start: Point, end: Point, direction: Point): string {
  const length = Math.hypot(end.x - start.x, end.y - start.y);
  const reach = Math.max(45, length * .45);
  const c1 = { x: start.x + direction.x * reach, y: start.y + direction.y * reach };
  const c2 = { x: end.x - (end.x - start.x) * .25, y: end.y - (end.y - start.y) * .25 };
  return `M ${start.x} ${start.y} C ${c1.x} ${c1.y}, ${c2.x} ${c2.y}, ${end.x} ${end.y}`;
}
