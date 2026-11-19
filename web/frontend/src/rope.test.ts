import { describe, expect, it } from 'vitest';
import { emptyDocument, restoreDocument, toPayload, type EditorDocument } from './model';
import { hitState, previewRope, transitionGeometry } from './geometry';

describe('editable transition ropes', () => {
  const document = (): EditorDocument => ({ ...emptyDocument(), states: [
    { id: 'a', label: 'a', initial: true, final: false, x: 0, y: 0 },
    { id: 'b', label: 'b', initial: false, final: true, x: 200, y: 0 },
  ], transitions: [{ id: 'ab', source: 'a', target: 'b', symbol: 'a', curve: { x: 15, y: 100 } }] });
  it('persists curve metadata but never sends it to the strict Python API', () => {
    const d = document();
    expect(restoreDocument(JSON.stringify(d))).toEqual(d);
    expect(toPayload(d).transitions).toEqual([{ id: 'ab', source: 'a', target: 'b', symbol: 'a' }]);
    const legacy = document(); delete legacy.transitions[0].curve;
    expect(restoreDocument(JSON.stringify(legacy))).toEqual(legacy);
  });
  it('rejects malformed curve coordinates in stored documents', () => {
    const d = document();
    expect(restoreDocument(JSON.stringify({ ...d, transitions: [{ ...d.transitions[0], curve: { x: null, y: 1 } }] }))).toBeNull();
  });
  it('keeps reshaped endpoints on circle boundaries on either side', () => {
    for (const curve of [{ x: 80, y: 120 }, { x: -180, y: -80 }, { x: 0, y: 0 }, { x: -100, y: 0 }, { x: 100, y: 0 }]) {
      const g = transitionGeometry({ x: 0, y: 0 }, { x: 200, y: 0 }, 0, false, curve);
      expect(Math.hypot(g.start.x, g.start.y)).toBeCloseTo(32);
      expect(Math.hypot(g.end.x - 200, g.end.y)).toBeCloseTo(32);
      expect(g.path).not.toMatch(/NaN|Infinity/);
    }
  });
  it('can bend self loops below or beside their state', () => {
    const g = transitionGeometry({ x: 0, y: 0 }, { x: 0, y: 0 }, 0, true, { x: 130, y: 0 });
    expect(g.label.x).toBeGreaterThan(32);
    expect(Math.hypot(g.start.x, g.start.y)).toBeCloseTo(32);
  });
  it('does not snap when starting to drag automatic loops or straight transitions', () => {
    for (const loop of [true, false]) {
      const a = { x: 0, y: 0 }, b = loop ? a : { x: 200, y: 0 };
      const automatic = transitionGeometry(a, b, 0, loop);
      const grabbed = transitionGeometry(a, b, 0, loop, automatic.control);
      expect(grabbed.path).toBe(automatic.path);
      expect(grabbed.label).toEqual(automatic.label);
    }
  });
  it('only completes connections within state circles, including self loops', () => {
    const states = document().states;
    expect(hitState(states, { x: 32, y: 32 })).toBe('a');
    expect(hitState(states, { x: 232, y: 32 })).toBe('b');
    expect(hitState(states, { x: 100, y: 32 })).toBeNull();
    expect(hitState(states, { x: 0, y: 0 })).toBeNull();
  });
  it('produces a smooth finite preview in every direction and at zero length', () => {
    for (const end of [{ x: 0, y: 0 }, { x: -200, y: 100 }, { x: 30, y: -100 }]) {
      const path = previewRope({ x: 0, y: 0 }, end, { x: 1, y: 0 });
      expect(path).toContain(' C '); expect(path).not.toMatch(/NaN|Infinity/);
    }
  });
});
