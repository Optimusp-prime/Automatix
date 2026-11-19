import { describe, expect, it } from 'vitest';
import { emptyDocument, restoreDocument, toPayload, updateState, type DraftState } from './model';
import { stateSize, minimumStateSize } from './stateSize';
import { hitState, transitionGeometry } from './geometry';

const state = (): DraftState => ({ id: 'q0', label: 'q0', initial: true, final: false, x: 20, y: 30 });
describe('resizable readable states', () => {
  it('grows the minimum with the complete label and rejects undersized circles', () => {
    expect(stateSize(state())).toBe(64);
    const long = { ...state(), label: 'un_nom_entier_sans_troncature', size: 64 };
    expect(stateSize(long)).toBeGreaterThan(150);
    expect(stateSize(long)).toBe(minimumStateSize(long.label));
  });
  it('grows renamed states around their existing center without mutating the document', () => {
    const original = { ...emptyDocument(), states: [state()] };
    const next = updateState(original, 'q0', { label: 'un_nom_entier_sans_troncature' });
    const radius = stateSize(next.states[0]) / 2;
    expect(next.states[0].x + radius).toBe(52);
    expect(next.states[0].y + radius).toBe(62);
    expect(original.states[0].label).toBe('q0');
  });
  it('persists size locally but excludes it from API payloads', () => {
    const d = { ...emptyDocument(), states: [{ ...state(), size: 180 }] };
    expect(restoreDocument(JSON.stringify(d))).toEqual(d);
    expect(toPayload(d).states[0]).not.toHaveProperty('size');
    expect(restoreDocument(JSON.stringify({ ...d, states: [{ ...state(), size: -3 }] }))).toBeNull();
  });
  it('attaches edges and loops to resized circle boundaries', () => {
    const g = transitionGeometry({ x: 0, y: 0 }, { x: 350, y: 0 }, 80, false, undefined, 70, 100);
    expect(Math.hypot(g.start.x, g.start.y)).toBeCloseTo(70);
    expect(Math.hypot(g.end.x - 350, g.end.y)).toBeCloseTo(100);
    const loop = transitionGeometry({ x: 0, y: 0 }, { x: 0, y: 0 }, 0, true, undefined, 90, 90);
    expect(Math.hypot(loop.start.x, loop.start.y)).toBeCloseTo(90);
    expect(loop.label.y).toBeLessThan(-90);
  });
  it('uses resized circles for drop targets', () => {
    expect(hitState([{ ...state(), size: 180 }], { x: 180, y: 120 })).toBe('q0');
    expect(hitState([{ ...state(), size: 180 }], { x: 20, y: 30 })).toBeNull();
  });
});
