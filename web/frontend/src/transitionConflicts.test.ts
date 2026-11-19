import { describe, expect, it } from 'vitest';
import { appendTransition, emptyDocument, restoreDocument, updateTransitionSymbol, type EditorDocument } from './model';

const sample = (): EditorDocument => ({ ...emptyDocument(), states: [
  { id: 'q0', label: 'q0', initial: true, final: false, x: 0, y: 0 },
  { id: 'q1', label: 'q1', initial: false, final: true, x: 200, y: 0 },
], transitions: [
  { id: 'a', source: 'q0', target: 'q1', symbol: 'a' },
  { id: 'b', source: 'q0', target: 'q0', symbol: 'b', curve: { x: 0, y: -90 } },
] });

describe('DFA transition conflict prevention', () => {
  it('rejects the same source and symbol regardless of destination', () => {
    const d = sample();
    for (const target of ['q0', 'q1']) {
      expect(appendTransition(d, { id: 'new', source: 'q0', target, symbol: 'a' })).toBe(d);
    }
    expect(d.transitions).toHaveLength(2);
  });
  it('allows a symbol from another state and a different symbol from the same state', () => {
    const d = sample();
    expect(appendTransition(d, { id: 'new', source: 'q1', target: 'q0', symbol: 'a' }).transitions).toHaveLength(3);
    expect(appendTransition(d, { id: 'new', source: 'q0', target: 'q1', symbol: 'c' }).transitions).toHaveLength(3);
  });
  it('blocks conflicting edits without changing endpoints or curve metadata', () => {
    const d = sample();
    expect(updateTransitionSymbol(d, 'b', 'a')).toBe(d);
    expect(updateTransitionSymbol(d, 'b', 'b')).toBe(d);
    const edited = updateTransitionSymbol(d, 'b', 'c');
    expect(edited.transitions[1]).toEqual({ ...d.transitions[1], symbol: 'c' });
    expect(d.transitions[1].symbol).toBe('b');
  });
  it('keeps legacy duplicates readable and lets the user resolve them', () => {
    const d = sample(); d.transitions[1].symbol = 'a';
    expect(restoreDocument(JSON.stringify(d))).toEqual(d);
    expect(updateTransitionSymbol(d, 'b', 'b').transitions.map(e => e.symbol)).toEqual(['a', 'b']);
  });
});
