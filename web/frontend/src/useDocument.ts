import { useCallback, useEffect, useRef, useState } from 'react';
import { emptyDocument, restoreDocument, STORAGE_KEY, type EditorDocument } from './model';

export function useDocument() {
  const [initial] = useState(() => {
    try { const raw = localStorage.getItem(STORAGE_KEY); const restored = restoreDocument(raw);
      return { document: restored ?? emptyDocument(), warning: raw && !restored ? 'La sauvegarde locale est illisible. Un dessin vide a été ouvert.' : '' };
    } catch { return { document: emptyDocument(), warning: 'La sauvegarde locale n’est pas disponible dans ce navigateur.' }; }
  });
  const [document, setDocument] = useState(initial.document);
  const [warning, setWarning] = useState(initial.warning);
  const current = useRef(document);
  const past = useRef<EditorDocument[]>([]), future = useRef<EditorDocument[]>([]);
  const [revision, bump] = useState(0);
  const commit = useCallback((next: EditorDocument, record = true) => {
    if (record) { past.current = [...past.current.slice(-99), current.current]; future.current = []; }
    current.current = next; setDocument(next); bump(r => r + 1);
  }, []);
  const checkpoint = useCallback(() => { past.current = [...past.current.slice(-99), current.current]; future.current = []; bump(r => r + 1); }, []);
  const undo = useCallback(() => { const previous = past.current.pop(); if (!previous) return;
    future.current.push(current.current); current.current = previous; setDocument(previous); bump(r => r + 1); }, []);
  const redo = useCallback(() => { const next = future.current.pop(); if (!next) return;
    past.current.push(current.current); current.current = next; setDocument(next); bump(r => r + 1); }, []);
  useEffect(() => { const timer = setTimeout(() => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(document)); }
    catch { setWarning('Sauvegarde impossible : le stockage du navigateur est plein ou désactivé.'); }
  }, 200); return () => clearTimeout(timer); }, [document]);
  return { document, current, commit, checkpoint, undo, redo, canUndo: !!past.current.length,
    canRedo: !!future.current.length, warning, revision };
}
