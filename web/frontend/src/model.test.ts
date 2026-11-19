import { describe, expect, it } from 'vitest';
import { appendTransition, emptyDocument, removeState, toPayload, restoreDocument, updateState } from './model';
import { transitionGeometry } from './geometry';

describe('editable document', () => {
  const sample = () => ({ ...emptyDocument(), alphabetText: 'a, b', states: [
    { id: 's0', label: 'q0', initial: true, final: false, x: 0, y: 10 },
    { id: 's1', label: 'q1', initial: false, final: true, x: 200, y: 10 },
  ], transitions: [{ id: 'e', source: 's0', target: 's1', symbol: 'a' }] });

  it('deletes incident edges atomically without changing the original', () => {
    const original = sample();
    const next = removeState(original, 's1');
    expect(next.states).toHaveLength(1);
    expect(next.transitions).toEqual([]);
    expect(original.transitions).toHaveLength(1);
  });
  it('rejects a transition whose endpoint disappeared during undo, preserving storage', () => {
    const original = removeState(sample(), 's1');
    for (const edge of [
      { id: 'new', source: 's1', target: 's0', symbol: 'a' },
      { id: 'new', source: 's0', target: 's1', symbol: 'a' },
    ]) expect(appendTransition(original, edge)).toBe(original);
    const next = appendTransition(original, { id: 'loop', source: 's0', target: 's0', symbol: 'a' });
    expect(next.transitions).toHaveLength(1);
    expect(original.transitions).toHaveLength(0);
    expect(restoreDocument(JSON.stringify(next))).toEqual(next);
  });
  it('renames without breaking endpoints and replaces the initial state', () => {
    const next = updateState(sample(), 's1', { label: 'renommé', initial: true });
    expect(next.states.map(s => s.initial)).toEqual([false, true]);
    expect(next.transitions[0].target).toBe('s1');
  });
  it('sends mathematical data only and preserves invalid symbols/duplicates', () => {
    const draft = sample();
    draft.alphabetText = 'a, a, ';
    draft.transitions.push({ ...draft.transitions[0], id: 'other' });
    const payload = toPayload(draft);
    expect(payload.alphabet).toEqual(['a', 'a', '']);
    expect(payload.states[0]).not.toHaveProperty('x');
    expect(payload.transitions).toHaveLength(2);
    expect(toPayload(emptyDocument()).alphabet).toEqual(['a', 'b']);
  });
  it('restores an unfinished drawing, but rejects corrupt or incompatible storage', () => {
    const document = sample();
    document.states[0].initial = false;
    expect(restoreDocument(JSON.stringify(document))).toEqual(document);
    for (const bad of ['{', '{}', 'null', JSON.stringify({ ...document, version: 9 }),
      JSON.stringify({ ...document, states: [{ ...document.states[0], x: null }] }),
      JSON.stringify({ ...document, transitions: [{ ...document.transitions[0], target: 'absent' }] })]) {
      expect(restoreDocument(bad)).toBeNull();
    }
  });
});

describe('transition geometry', () => {
  it('terminates at the circle boundary', () => {
    const curve = transitionGeometry({ x: 0, y: 0 }, { x: 200, y: 0 }, 0, false);
    expect(Math.hypot(curve.end.x - 200, curve.end.y)).toBeCloseTo(32);
    expect(curve.path).not.toMatch(/NaN|Infinity/);
  });
  it('separates opposite curves and self loops', () => {
    const a = transitionGeometry({ x: 0, y: 0 }, { x: 200, y: 0 }, 38, false);
    const b = transitionGeometry({ x: 200, y: 0 }, { x: 0, y: 0 }, 38, false);
    expect(a.label.y).toBeGreaterThan(0);
    expect(b.label.y).toBeLessThan(0);
    const loop = transitionGeometry({ x: 0, y: 0 }, { x: 0, y: 0 }, 0, true);
    expect(loop.path).toContain('C');
    expect(loop.label.y).toBeLessThan(-32);
    expect(transitionGeometry({ x: 0, y: 0 }, { x: 0, y: 0 }, 0, false).path).not.toMatch(/NaN|Infinity/);
  });
});
