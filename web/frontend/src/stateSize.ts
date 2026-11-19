import type { DraftState, DraftTransition } from './model';

export const STATE_FONT = '14px system-ui, sans-serif';
let context: CanvasRenderingContext2D | null | undefined;

/** Full-label width plus breathing room; same font as the rendered state. */
export function minimumStateSize(label: string): number {
  if (context === undefined) context = typeof document === 'undefined' ? null : document.createElement('canvas').getContext('2d');
  if (context) context.font = STATE_FONT;
  const width = context ? context.measureText(label || '…').width : Array.from(label).length * 14;
  return Math.max(64, Math.ceil(width + 32));
}

export function stateSize(state: { label?: string; size?: number; autoMinimum?: number }): number {
  return Math.max(minimumStateSize(state.label ?? ''), state.size ?? 64, state.autoMinimum ?? 64);
}

export type DisplayState = DraftState & { autoMinimum: number };

/** O(Q + E) display sizing; grouped arcs count once, loops have two attachments.
 * Keep stored centers and manual sizes intact. This derived metadata is never
 * persisted or sent to the API. Automatic growth is capped at 240px.
 */
export function displayStates(states: readonly DraftState[], transitions: readonly DraftTransition[]): DisplayState[] {
  const incoming = new Map<string, number>(), outgoing = new Map<string, number>();
  const seen = new Set<string>();
  for (const edge of transitions) {
    const key = JSON.stringify([edge.source, edge.target]);
    if (seen.has(key)) continue;
    seen.add(key);
    outgoing.set(edge.source, (outgoing.get(edge.source) ?? 0) + 1);
    incoming.set(edge.target, (incoming.get(edge.target) ?? 0) + 1);
  }
  return states.map(s => {
    const entry = (incoming.get(s.id) ?? 0) + (s.initial ? 1 : 0);
    const exit = outgoing.get(s.id) ?? 0;
    // Most incoming arrows share one side: allocate more space for that side
    // than a circumference-only rule would provide.
    const load = Math.max(entry, exit, Math.ceil((entry + exit) / 2));
    const autoMinimum = Math.max(minimumStateSize(s.label), Math.min(240, 64 + Math.max(0, load - 2) * 20));
    const growth = Math.max(stateSize(s), autoMinimum) - stateSize(s);
    return { ...s, autoMinimum, x: s.x - growth / 2, y: s.y - growth / 2 };
  });
}
