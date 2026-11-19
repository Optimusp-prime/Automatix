import { stateSize } from './stateSize';

export interface DraftState {
  id: string; label: string; initial: boolean; final: boolean; x: number; y: number; size?: number; color?: string;
}
export interface DraftTransition { id: string; source: string; target: string; symbol: string; curve?: { x: number; y: number } }
export interface EditorDocument { version: 1; alphabetText: string; states: DraftState[]; transitions: DraftTransition[] }
export interface Issue { code: string; message: string; state_id: string | null; transition_id: string | null; symbol: string | null }
export interface ValidationResult { valid: boolean; issues: Issue[] }
export const STORAGE_KEY = 'automatix.dfa-editor.v1';
export const LIMITS = { states: 200, transitions: 4000, alphabet: 128 };
export const emptyDocument = (): EditorDocument => ({ version: 1, alphabetText: 'a, b', states: [], transitions: [] });
export const parseAlphabet = (text: string) => text.trim() === '' ? [] : text.split(',').map(s => s.trim());

export function toPayload(document: EditorDocument) {
  return { alphabet: parseAlphabet(document.alphabetText),
    states: document.states.map(({ id, label, initial, final }) => ({ id, label, initial, final })),
    transitions: document.transitions.map(({ id, source, target, symbol }) => ({ id, source, target, symbol })) };
}

export function removeState(document: EditorDocument, id: string): EditorDocument {
  return { ...document, states: document.states.filter(s => s.id !== id),
    transitions: document.transitions.filter(t => t.source !== id && t.target !== id) };
}

export function appendTransition(document: EditorDocument, edge: DraftTransition): EditorDocument {
  if (!document.states.some(s => s.id === edge.source) || !document.states.some(s => s.id === edge.target)) return document;
  if (transitionConflict(document, edge.source, edge.symbol)) return document;
  return { ...document, transitions: [...document.transitions, edge] };
}

/** A DFA has at most one outgoing edge per (source, symbol), whatever its target. O(E). */
export function transitionConflict(document: EditorDocument, source: string, symbol: string, exceptId?: string) {
  return document.transitions.find(e => e.id !== exceptId && e.source === source && e.symbol === symbol);
}

export function updateTransitionSymbol(document: EditorDocument, id: string, symbol: string): EditorDocument {
  const edge = document.transitions.find(e => e.id === id);
  if (!edge || edge.symbol === symbol || transitionConflict(document, edge.source, symbol, id)) return document;
  return { ...document, transitions: document.transitions.map(e => e.id === id ? { ...e, symbol } : e) };
}

export function updateState(document: EditorDocument, id: string, patch: Partial<Omit<DraftState, 'id'>>): EditorDocument {
  return { ...document, states: document.states.map(s => {
    if (s.id !== id) return patch.initial ? { ...s, initial: false } : s;
    const next = { ...s, ...patch };
    if (patch.label !== undefined) {
      const difference = (stateSize(next) - stateSize(s)) / 2;
      return { ...next, x: next.x - difference, y: next.y - difference };
    }
    return next;
  }) };
}

// Reject broken storage, but retain semantically invalid drafts for correction.
export function restoreDocument(raw: string | null): EditorDocument | null {
  if (!raw || raw.length > 2_000_000) return null;
  try {
    const value: unknown = JSON.parse(raw);
    if (!value || typeof value !== 'object') return null;
    const d = value as Record<string, unknown>;
    if (d.version !== 1 || typeof d.alphabetText !== 'string' || d.alphabetText.length > 1024
      || !Array.isArray(d.states) || d.states.length > LIMITS.states
      || !Array.isArray(d.transitions) || d.transitions.length > LIMITS.transitions) return null;
    const short = (v: unknown) => typeof v === 'string' && v.length <= 64;
    const id = (v: unknown) => short(v) && (v as string).length > 0;
    const record = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object';
    const coordinate = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v) && Math.abs(v) <= 1_000_000;
    if (!d.states.every(s => record(s) && id(s.id) && short(s.label) && typeof s.initial === 'boolean'
      && typeof s.final === 'boolean' && coordinate(s.x) && coordinate(s.y)
      && (s.color === undefined || (typeof s.color === 'string' && /^#[0-9a-f]{6}$/i.test(s.color)))
      && (s.size === undefined || (typeof s.size === 'number' && Number.isFinite(s.size) && s.size >= 64 && s.size <= 2048)))) return null;
    const states = d.states as DraftState[];
    const ids = new Set(states.map(s => s.id));
    if (ids.size !== states.length) return null;
    if (!d.transitions.every(e => record(e) && id(e.id) && short(e.symbol)
      && typeof e.source === 'string' && ids.has(e.source)
      && typeof e.target === 'string' && ids.has(e.target)
      && (e.curve === undefined || (record(e.curve) && coordinate(e.curve.x) && coordinate(e.curve.y))))) return null;
    const transitions = d.transitions as DraftTransition[];
    if (new Set(transitions.map(e => e.id)).size !== transitions.length) return null;
    // Reconstruct only supported fields, dropping unrelated persisted data.
    return { version: 1, alphabetText: d.alphabetText,
      states: states.map(({ id, label, initial, final, x, y, size, color }) => ({ id, label, initial, final, x, y,
        ...(color === undefined ? {} : { color }),
        ...(size === undefined ? {} : { size }) })),
      transitions: transitions.map(({ id, source, target, symbol, curve }) => ({ id, source, target, symbol,
        ...(curve ? { curve: { x: curve.x, y: curve.y } } : {}) })) };
  } catch { return null; }
}
