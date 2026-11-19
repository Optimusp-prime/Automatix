import { useCallback, useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from 'react';
import { hitState, type Point } from './geometry';
import type { EditorDocument } from './model';
import { stateSize } from './stateSize';

type ConnectGesture = { kind: 'connect'; source: string; start: Point; direction: Point; point: Point; target: string | null };
type BendGesture = { kind: 'bend'; id: string; initial: Point; curve: Point; point: Point };
type Gesture = ConnectGesture | BendGesture;
type Active = { view: Gesture; pointerId: number; element: Element; origin: Point; clientOrigin: Point; moved: boolean };

/** Transient pointer gestures never enter history or local storage until release. */
export function useRopeGesture(document: EditorDocument, mode: string, toFlow: (p: Point) => Point,
  onConnect: (source: string, target: string) => void, onBend: (id: string, curve: Point) => void) {
  const [gesture, setGesture] = useState<Gesture | null>(null);
  const active = useRef<Active | null>(null);
  const frame = useRef<number | null>(null);
  const latest = useRef({ document, toFlow, onConnect, onBend });
  latest.current = { document, toFlow, onConnect, onBend };
  const cancel = useCallback(() => {
    const old = active.current; active.current = null;
    if (frame.current !== null) cancelAnimationFrame(frame.current);
    frame.current = null; setGesture(null);
    if (old?.element.hasPointerCapture(old.pointerId)) old.element.releasePointerCapture(old.pointerId);
  }, []);
  useEffect(() => { cancel(); }, [mode, document, cancel]);

  useEffect(() => {
    function update(event: PointerEvent) {
      const a = active.current;
      if (!a || event.pointerId !== a.pointerId) return null;
      const point = latest.current.toFlow({ x: event.clientX, y: event.clientY });
      a.moved ||= Math.hypot(event.clientX - a.clientOrigin.x, event.clientY - a.clientOrigin.y) >= 4;
      if (a.view.kind === 'connect') a.view = { ...a.view, point, target: hitState(latest.current.document.states, point) };
      else a.view = { ...a.view, point, curve: { x: a.view.initial.x + 2 * (point.x - a.origin.x),
        y: a.view.initial.y + 2 * (point.y - a.origin.y) } };
      return a;
    }
    function move(event: PointerEvent) {
      const a = update(event); if (!a) return;
      event.preventDefault();
      if (frame.current === null) frame.current = requestAnimationFrame(() => {
        frame.current = null; if (active.current) setGesture({ ...active.current.view });
      });
    }
    function finish(event: PointerEvent) {
      const a = update(event); if (!a) return;
      event.preventDefault(); event.stopPropagation();
      const view = a.view; cancel();
      if (!a.moved) return;
      if (view.kind === 'connect') {
        // A toolbar/dialog covering a state is not a valid drop target.
        const hit = window.document.elementFromPoint(event.clientX, event.clientY)?.closest('.react-flow__node');
        if (view.target && hit?.getAttribute('data-id') === view.target
          && latest.current.document.states.some(s => s.id === view.source)) latest.current.onConnect(view.source, view.target);
      } else if (latest.current.document.transitions.some(e => e.id === view.id)) latest.current.onBend(view.id, view.curve);
    }
    const key = (event: KeyboardEvent) => { if (event.key === 'Escape') cancel(); };
    const lost = (event: PointerEvent) => { if (event.pointerId === active.current?.pointerId) cancel(); };
    window.addEventListener('pointermove', move, { passive: false });
    window.addEventListener('pointerup', finish, true);
    window.addEventListener('pointercancel', lost);
    window.addEventListener('lostpointercapture', lost);
    window.addEventListener('blur', cancel);
    window.addEventListener('keydown', key);
    return () => {
      window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', finish, true);
      window.removeEventListener('pointercancel', lost); window.removeEventListener('lostpointercapture', lost);
      window.removeEventListener('blur', cancel); window.removeEventListener('keydown', key);
      if (frame.current !== null) cancelAnimationFrame(frame.current);
      const old = active.current; active.current = null;
      if (old?.element.hasPointerCapture(old.pointerId)) old.element.releasePointerCapture(old.pointerId);
    };
  }, [cancel]);

  const begin = useCallback((event: ReactPointerEvent<Element>, view: Gesture) => {
    if (event.button !== 0 || !event.isPrimary) return;
    event.preventDefault(); event.stopPropagation(); cancel();
    const clientOrigin = { x: event.clientX, y: event.clientY };
    event.currentTarget.setPointerCapture(event.pointerId);
    active.current = { view, element: event.currentTarget, pointerId: event.pointerId,
      origin: latest.current.toFlow(clientOrigin), clientOrigin, moved: false };
    setGesture(view);
  }, [cancel]);
  const beginConnection = useCallback((event: ReactPointerEvent<Element>, source: string, direction: Point) => {
    const state = latest.current.document.states.find(s => s.id === source); if (!state) return;
    const radius = stateSize(state) / 2;
    const start = { x: state.x + radius + direction.x * radius, y: state.y + radius + direction.y * radius };
    begin(event, { kind: 'connect', source, start, direction, point: start, target: null });
  }, [begin]);
  const beginBend = useCallback((event: ReactPointerEvent<Element>, id: string, initial: Point) => {
    begin(event, { kind: 'bend', id, initial, curve: initial, point: latest.current.toFlow({ x: event.clientX, y: event.clientY }) });
  }, [begin]);
  return { gesture, beginConnection, beginBend, cancel };
}
