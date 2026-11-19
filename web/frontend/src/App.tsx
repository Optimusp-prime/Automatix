import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Background, BackgroundVariant, MarkerType, ReactFlow, ReactFlowProvider, ViewportPortal, useReactFlow, type NodeChange } from '@xyflow/react';
import { ArrowUpRight, Check, Circle, Hand, Maximize, Minus, MousePointer2, Plus, Redo2, Trash2, Undo2, X, LoaderCircle, AlertCircle, Eraser, Workflow } from 'lucide-react';
import { AlgorithmPanel } from './AlgorithmPanel';
import { StateNode, type StateFlowNode } from './StateNode';
import { TransitionEdge, type TransitionFlowEdge } from './TransitionEdge';
import { appendTransition, LIMITS, parseAlphabet, removeState, transitionConflict, updateTransitionSymbol, updateState, type Issue, type ValidationResult } from './model';
import { useDocument } from './useDocument';
import { validateDocument } from './api';
import { stateFlowNode } from './flowNodes';
import { useRopeGesture } from './useRopeGesture';
import { previewRope, type Point } from './geometry';
import { displayStates, stateSize } from './stateSize';
import { routeTransitions } from './routeTransitions';

const nodeTypes = { state: StateNode }, edgeTypes = { transition: TransitionEdge };
type Tool = 'select' | 'state' | 'transition' | 'hand';
type Selection = { kind: 'state' | 'transition'; id: string } | null;
type EdgeDraft = { source: string; target: string; symbol: string };

function Editor() {
  const { document, current, commit, checkpoint, undo: undoDocument, redo: redoDocument, canUndo, canRedo, warning } = useDocument();
  const displayed = useMemo(() => ({ ...document, states: displayStates(document.states, document.transitions) }), [document]);
  const [tool, setTool] = useState<Tool>('select');
  const [algorithmsOpen, setAlgorithmsOpen] = useState(false);
  const [selection, setSelection] = useState<Selection>(null);
  const [source, setSource] = useState<string | null>(null);
  const [edgeDraft, setEdgeDraft] = useState<EdgeDraft | null>(null);
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [networkError, setNetworkError] = useState('');
  const [notice, setNotice] = useState('');
  const [symbolError, setSymbolError] = useState('');
  const [pending, setPending] = useState(false);
  const [zoom, setZoom] = useState(1);
  const board = useRef<HTMLDivElement>(null);
  const pointerDragging = useRef(false);
  const beginResize = useCallback(() => { pointerDragging.current = true; checkpoint(); }, [checkpoint]);
  const endResize = useCallback(() => { pointerDragging.current = false; }, []);
  function undo() { pointerDragging.current = false; setSource(null); setEdgeDraft(null); undoDocument(); }
  function redo() { pointerDragging.current = false; setSource(null); setEdgeDraft(null); redoDocument(); }
  const request = useRef<AbortController | null>(null);
  const { screenToFlowPosition, zoomIn, zoomOut, fitView, setCenter } = useReactFlow<StateFlowNode, TransitionFlowEdge>();
  const state = document.states.find(s => selection?.kind === 'state' && s.id === selection.id);
  const displayedState = displayed.states.find(s => s.id === state?.id);
  const transition = document.transitions.find(e => selection?.kind === 'transition' && e.id === selection.id);
  const draftConflict = edgeDraft && transitionConflict(document, edgeDraft.source, edgeDraft.symbol);
  function conflictMessage(source: string, symbol: string) {
    const label = document.states.find(s => s.id === source)?.label ?? source;
    return `L’état « ${label} » possède déjà une transition « ${symbol || 'vide'} ». Choisissez un autre symbole.`;
  }
  useEffect(() => { setSymbolError(''); }, [selection, document]);
  const connectRope = useCallback((source: string, target: string) => {
    setSource(null);
    setEdgeDraft({ source, target, symbol: parseAlphabet(current.current.alphabetText)[0] ?? '' });
  }, [current]);
  const bendRope = useCallback((id: string, curve: Point) => {
    const d = current.current;
    const member = d.transitions.find(e => e.id === id);
    if (!member) return;
    commit({ ...d, transitions: d.transitions.map(e => e.source === member.source && e.target === member.target ? { ...e, curve } : e) });
    setSelection({ kind: 'transition', id });
  }, [commit, current]);
  const { gesture, beginConnection, beginBend } = useRopeGesture(displayed, tool, screenToFlowPosition, connectRope, bendRope);

  useEffect(() => {
    request.current?.abort(); setResult(null); setNetworkError(''); setPending(false);
    return () => request.current?.abort();
  }, [document]);

  useEffect(() => {
    if (source && !document.states.some(s => s.id === source)) setSource(null);
    if (edgeDraft && (!document.states.some(s => s.id === edgeDraft.source)
      || !document.states.some(s => s.id === edgeDraft.target))) setEdgeDraft(null);
  }, [document.states, source, edgeDraft]);

  const selectEdge = useCallback((id: string) => { setSelection({ kind: 'transition', id }); setSource(null); }, []);
  const nodes: StateFlowNode[] = useMemo(() => displayed.states.map(s => {
    const node = stateFlowNode(s, selection?.kind === 'state' && selection.id === s.id, source === s.id,
      !!result?.issues.some(i => i.state_id === s.id));
    return { ...node, data: { ...node.data, connectable: tool === 'transition', onConnectStart: beginConnection,
      resizable: tool === 'select', onResizeStart: beginResize, onResizeEnd: endResize,
      dropTarget: gesture?.kind === 'connect' && gesture.target === s.id } };
  }), [displayed.states, selection, result, source, tool, beginConnection, gesture, beginResize, endResize]);
  const bendGesture = gesture?.kind === 'bend' ? gesture : null;
  const routes = useMemo(() => routeTransitions(displayed.states, document.transitions, bendGesture),
    [displayed.states, document.transitions, bendGesture]);
  const crowdedRoutes = routes.filter(route => route.crowded).length;
  const edges: TransitionFlowEdge[] = useMemo(() => {
    return routes.map(({ members: peers, geometry, crowded }) => {
    const e = peers[0];
    const invalid = !!result?.issues.some(i => peers.some(p => p.id === i.transition_id));
    const selected = selection?.kind === 'transition' && peers.some(p => p.id === selection.id);
    return { id: e.id, type: 'transition', source: e.source, target: e.target, selected,
      markerEnd: { type: MarkerType.ArrowClosed, width: 18, height: 18, color: invalid ? '#b34840' : selected ? '#286b60' : '#777e86' },
      data: { symbols: peers.map(p => ({ id: p.id, symbol: p.symbol })), bend: 0, route: geometry, crowded,
        invalid, onSelect: selectEdge, editable: tool === 'select', onBendStart: beginBend } };
    });
  }, [routes, result, selection, selectEdge, tool, beginBend]);

  function changeTool(next: Tool) { setTool(next); setSource(null); setNotice(''); }
  function addState(position?: { x: number; y: number }) {
    const d = current.current;
    if (d.states.length >= LIMITS.states) { setNotice('Limite du POC : 200 états.'); return; }
    const rect = board.current?.getBoundingClientRect();
    const p = position ?? screenToFlowPosition({ x: (rect?.left ?? 0) + (rect?.width ?? 600) / 2,
      y: (rect?.top ?? 0) + (rect?.height ?? 500) / 2 });
    let index = 0; while (d.states.some(s => s.label === `q${index}`)) index++;
    const id = crypto.randomUUID();
    commit({ ...d, states: [...d.states, { id, label: `q${index}`, initial: d.states.length === 0,
      final: false, x: p.x - 32, y: p.y - 32 }] });
    setSelection({ kind: 'state', id });
  }
  function deleteSelection() {
    pointerDragging.current = false;
    const d = current.current;
    if (!selection) return;
    commit(selection.kind === 'state' ? removeState(d, selection.id)
      : { ...d, transitions: d.transitions.filter(e => e.id !== selection.id) });
    setSelection(null); setSource(null);
  }
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (event.key === 'Escape' && edgeDraft) { event.preventDefault(); setEdgeDraft(null); setSource(null); return; }
      if (target.closest('input, textarea, select, [contenteditable=true]')) return;
      if (event.key === 'Escape') { setEdgeDraft(null); setSource(null); setSelection(null); setTool('select'); }
      if (edgeDraft) return;
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') {
        event.preventDefault(); if (event.shiftKey) redo(); else undo();
      } else if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'y') { event.preventDefault(); redo(); }
      else if (event.key === 'Delete' || event.key === 'Backspace') { event.preventDefault(); deleteSelection(); }
      else if (!event.ctrlKey && !event.metaKey) {
        const map: Record<string, Tool> = { v: 'select', e: 'state', t: 'transition', h: 'hand' };
        if (map[event.key.toLowerCase()]) changeTool(map[event.key.toLowerCase()]);
      }
    };
    window.addEventListener('keydown', handler); return () => window.removeEventListener('keydown', handler);
  });

  function onNodesChange(changes: NodeChange<StateFlowNode>[]) {
    const positions = changes.filter(c => c.type === 'position');
    const dimensions = changes.filter(c => c.type === 'dimensions').filter(c => c.setAttributes);
    if (!positions.length && !dimensions.length) return;
    const d = current.current;
    let changed = false;
    const views = new Map(displayStates(d.states, d.transitions).map(s => [s.id, s]));
    const states = d.states.map(s => {
      const position = positions.find(p => p.id === s.id)?.position;
      const dimension = dimensions.find(p => p.id === s.id)?.dimensions;
      const view = views.get(s.id)!;
      const size = dimension ? Math.min(2048, Math.max(view.autoMinimum, dimension.width, dimension.height)) : undefined;
      const next = { ...s, ...(size === undefined ? {} : { size }) };
      if (position || dimension) {
        const growth = Math.max(stateSize(next), view.autoMinimum) - stateSize(next);
        next.x = (position?.x ?? view.x) + growth / 2;
        next.y = (position?.y ?? view.y) + growth / 2;
      }
      if (next.x === s.x && next.y === s.y && next.size === s.size) return s;
      changed = true; return next;
    });
    if (changed) commit({ ...d, states }, !pointerDragging.current);
  }

  async function validate() {
    setAlgorithmsOpen(false);
    request.current?.abort(); const controller = new AbortController(); request.current = controller;
    const snapshot = current.current;
    setPending(true); setNetworkError(''); setResult(null);
    const timeout = setTimeout(() => controller.abort('timeout'), 15000);
    try {
      const response = await validateDocument(snapshot, controller.signal);
      if (!controller.signal.aborted && current.current === snapshot) setResult(response);
    } catch (error) {
      if (current.current === snapshot && (!controller.signal.aborted || controller.signal.reason === 'timeout')) {
        setNetworkError(error instanceof TypeError ? 'Serveur inaccessible. Vérifiez que l’API est démarrée, puis réessayez.'
          : controller.signal.reason === 'timeout' ? 'Le serveur met trop de temps à répondre. Réessayez.'
          : error instanceof Error ? error.message : 'La validation a échoué. Réessayez.');
      }
    } finally { clearTimeout(timeout); if (request.current === controller) setPending(false); }
  }

  function locate(issue: Issue) {
    if (issue.transition_id) setSelection({ kind: 'transition', id: issue.transition_id });
    else if (issue.state_id) setSelection({ kind: 'state', id: issue.state_id });
    const s = document.states.find(s => s.id === issue.state_id);
    if (s) void setCenter(s.x + stateSize(s) / 2, s.y + stateSize(s) / 2, { zoom: Math.max(zoom, .8), duration: 180 });
  }
  const hint = notice || (tool === 'state' ? 'Cliquez dans l’espace pour ajouter un état.' : tool === 'transition'
    ? gesture?.kind === 'connect' ? 'Relâchez sur un état pour le relier. Échap pour annuler.'
      : source ? 'Choisissez l’arrivée. Le même état crée une boucle.' : 'Tirez un point vers un état, ou cliquez sur le départ puis l’arrivée.'
    : tool === 'hand' ? 'Glissez pour déplacer la vue.' : 'Déplacez les états. Sélectionnez un élément pour le modifier.');

  return <main className="editor-shell">
    <div className="document-controls" aria-label="Alphabet et validation">
      <label className="alphabet-field"><span>Alphabet</span><input aria-label="Alphabet" value={document.alphabetText} maxLength={1024}
        placeholder="a, b" onChange={e => commit({ ...current.current, alphabetText: e.target.value })} title="Symboles séparés par des virgules ; vide pour l’alphabet vide" /></label>
      <button className="primary-button validate-button" onClick={() => void validate()} disabled={pending}>
        {pending ? <LoaderCircle size={16} className="spin" /> : <Check size={16} />} {pending ? 'Validation…' : 'Valider'}
      </button>
    </div>
    <section className={`board tool-${tool}`} ref={board} aria-label="Dessin de l’automate">
      <ReactFlow<StateFlowNode, TransitionFlowEdge> nodes={nodes} edges={edges} nodeTypes={nodeTypes} edgeTypes={edgeTypes}
        proOptions={{ hideAttribution: true }}
        onNodesChange={onNodesChange} onNodeDragStart={() => { pointerDragging.current = true; checkpoint(); }}
        onNodeDragStop={() => { pointerDragging.current = false; }} nodesDraggable={tool === 'select'}
        nodesConnectable={false} elementsSelectable={tool === 'select'} panOnDrag={tool === 'hand' ? true : [1, 2]}
        deleteKeyCode={null} zoomOnDoubleClick={false} minZoom={.25} maxZoom={2} fitView={document.states.length > 0}
        fitViewOptions={{ padding: .7, maxZoom: 1 }} onMove={(_, viewport) => setZoom(viewport.zoom)}
        onNodeClick={(_, node) => { if (tool === 'transition') {
          if (source === null) { setSource(node.id); setSelection({ kind: 'state', id: node.id }); }
          else { setEdgeDraft({ source, target: node.id, symbol: parseAlphabet(document.alphabetText)[0] ?? '' }); }
        } else if (tool === 'select') { setSelection({ kind: 'state', id: node.id }); } }}
        onEdgeClick={(_, edge) => { if (tool === 'select') selectEdge(edge.id); }}
        onPaneClick={event => { if (tool === 'state') addState(screenToFlowPosition({ x: event.clientX, y: event.clientY }));
          else { setSelection(null); setSource(null); } }}>
        <Background id="paper-fine" variant={BackgroundVariant.Dots} gap={24} size={1.2} color="#c6cec4" />
        <Background id="paper-major" variant={BackgroundVariant.Dots} gap={120} size={2} color="#aabbb0" />
        {gesture?.kind === 'connect' && <ViewportPortal><svg className="rope-preview" aria-hidden="true">
          <path d={previewRope(gesture.start, gesture.point, gesture.direction)} fill="none" stroke="var(--accent)" strokeWidth={2} />
          <circle cx={gesture.point.x} cy={gesture.point.y} r={4} fill="var(--accent)" />
        </svg></ViewportPortal>}
      </ReactFlow>
      <div className="drawing-toolbar" role="toolbar" aria-label="Outils de dessin">
        {([{ id: 'select', name: 'Sélection', key: 'V', Icon: MousePointer2 }, { id: 'state', name: 'État', key: 'E', Icon: Circle },
          { id: 'transition', name: 'Transition', key: 'T', Icon: ArrowUpRight }, { id: 'hand', name: 'Déplacer la vue', key: 'H', Icon: Hand }] as const)
          .map(({ id, name, key, Icon }) => <button key={id} aria-label={name} aria-pressed={tool === id}
            title={`${name} (${key})`} onClick={() => changeTool(id)}><Icon size={18} /><span>{name === 'Déplacer la vue' ? 'Main' : name}</span></button>)}
        <span className="toolbar-divider" /><button aria-label="Annuler" title="Annuler (Ctrl+Z)" disabled={!canUndo} onClick={undo}><Undo2 size={17} /></button>
        <button aria-label="Rétablir" title="Rétablir (Ctrl+Maj+Z)" disabled={!canRedo} onClick={redo}><Redo2 size={17} /></button>
        <span className="toolbar-divider" />
        <button aria-label="Effacer la feuille" title="Effacer la feuille (annulable)" disabled={!document.states.length && !document.transitions.length}
          onClick={() => { pointerDragging.current = false; setSelection(null); setSource(null); setEdgeDraft(null);
            commit({ ...current.current, states: [], transitions: [] }); }}><Eraser size={18} /></button>
        <button aria-label="Algorithmes" title="Algorithmes" aria-expanded={algorithmsOpen} aria-pressed={algorithmsOpen}
          onClick={() => setAlgorithmsOpen(value => !value)}><Workflow size={18} /></button>
      </div>
      {!nodes.length && <div className="empty-canvas"><div className="empty-symbol" aria-hidden="true">q₀</div>
        <h1>Tout commence par un état.</h1><p>Ajoutez vos états, reliez-les, puis validez votre DFA.</p>
        <button className="secondary-button" onClick={() => addState()}><Plus size={16} /> Ajouter le premier état</button>
      </div>}
      {(tool !== 'select' || notice || crowdedRoutes > 0) && <div className="canvas-hint" aria-live="polite">
        {tool === 'select' && !notice && crowdedRoutes > 0
          ? `${crowdedRoutes} tracé(s) encore serré(s) : écartez les états ou ajustez les courbes soulignées.` : hint}</div>}
      <div className="zoom-toolbar"><button aria-label="Dézoomer" onClick={() => void zoomOut()}><Minus size={16} /></button>
        <span>{Math.round(zoom * 100)} %</span><button aria-label="Zoomer" onClick={() => void zoomIn()}><Plus size={16} /></button>
        <button aria-label="Centrer le dessin" title="Centrer le dessin" onClick={() => void fitView({ padding: .5, maxZoom: 1 })}><Maximize size={16} /></button></div>
    </section>
    {algorithmsOpen && <AlgorithmPanel document={document} onClose={() => setAlgorithmsOpen(false)}
      onApply={next => { setSelection(null); setSource(null); setEdgeDraft(null); setTool('select');
        commit(next); setAlgorithmsOpen(false); requestAnimationFrame(() => void fitView({ padding: .5, maxZoom: 1 })); }} />}
    {!algorithmsOpen && (result || networkError) && <section className={`validation-panel ${result?.valid ? 'success' : ''}`} aria-live="polite">
      <div className="panel-heading"><strong>{result?.valid ? <Check size={17} /> : <AlertCircle size={17} />}
        {networkError ? 'Validation indisponible' : result?.valid ? 'DFA valide' : `DFA à compléter · ${result?.issues.length} erreur${result?.issues.length === 1 ? '' : 's'}`}</strong>
        <button aria-label="Fermer la validation" onClick={() => { setResult(null); setNetworkError(''); }}><X size={16} /></button></div>
      {networkError ? <p role="alert">{networkError}</p> : result?.valid ? <p>Automatix a confirmé la validité de votre DFA complet.</p>
        : <ul>{result?.issues.slice(0, 40).map((issue, i) => <li key={i}><button onClick={() => locate(issue)}>{issue.message}</button></li>)}</ul>}
      {!!result && result.issues.length > 40 && <p>Les 40 premières erreurs sont affichées. Corrigez-les, puis relancez la validation.</p>}
    </section>}
    {(state || transition) && <section className="properties" aria-label="Propriétés de la sélection">
      <strong>{state ? 'État' : 'Transition'}</strong>
      {state ? <><label>Nom<input aria-label="Nom de l’état" maxLength={64} value={state.label}
        onChange={e => commit(updateState(current.current, state.id, { label: e.target.value }))} /></label>
        <label className="check-field"><input type="checkbox" checked={state.initial} onChange={e => commit(updateState(current.current, state.id, { initial: e.target.checked }))} />Initial</label>
        <label className="check-field"><input type="checkbox" checked={state.final} onChange={e => commit(updateState(current.current, state.id, { final: e.target.checked }))} />Final</label>
        <label>Diamètre<input aria-label="Diamètre de l’état" type="number" min={displayedState?.autoMinimum ?? 64} max={2048}
          value={Math.round(stateSize(displayedState ?? state))} onChange={e => { const value = Number(e.target.value);
            if (Number.isFinite(value) && value >= (displayedState?.autoMinimum ?? 64) && value <= 2048) {
              const difference = (value - stateSize(state)) / 2;
              commit(updateState(current.current, state.id, { size: value, x: state.x - difference, y: state.y - difference }));
            } }} /></label>
        <small className="resize-hint">Minimum adapté au nom et au nombre de flèches. Tirez une poignée pour agrandir.</small>
        <label>Couleur de fond<input className="state-color-input" type="color" aria-label="Couleur de fond de l’état"
          value={state.color ?? '#ffffff'} onChange={e => commit(updateState(current.current, state.id, { color: e.target.value }))} /></label>
        <div className="state-palette" role="group" aria-label="Couleurs proposées">
          {[['Blanc','#ffffff'],['Menthe','#dcefe4'],['Bleu','#dceaf6'],['Sable','#f4e8cc'],['Rose','#f2dce1'],['Bleu nuit','#173b50']].map(([name,color]) =>
            <button key={color} aria-label={`Fond ${name}`} title={name} aria-pressed={(state.color ?? '#ffffff') === color}
              style={{ backgroundColor:color }} onClick={() => commit(updateState(current.current,state.id,{color}))} />)}
        </div>
        <small className="resize-hint">La couleur du texte s’adapte automatiquement.</small></>
        : transition && <><span className="edge-endpoints">{document.states.find(s => s.id === transition.source)?.label} → {document.states.find(s => s.id === transition.target)?.label}</span>
          <label>Symbole<input aria-label="Symbole de la transition" aria-describedby={symbolError ? 'symbol-conflict' : undefined}
            maxLength={64} value={transition.symbol} onChange={e => {
              const symbol = e.target.value;
              if (transitionConflict(current.current, transition.source, symbol, transition.id)) {
                setSymbolError(conflictMessage(transition.source, symbol)); return;
              }
              setSymbolError(''); const next = updateTransitionSymbol(current.current, transition.id, symbol);
              if (next !== current.current) commit(next);
            }} /></label></>}
      <button className="delete-button" onClick={deleteSelection}><Trash2 size={16} />Supprimer</button>
      <button className="close-properties" aria-label="Fermer les propriétés" onClick={() => setSelection(null)}><X size={16} /></button>
      {symbolError && <p id="symbol-conflict" className="inline-error property-error" role="alert">{symbolError}</p>}
    </section>}
    <div className="canvas-status"><span>{document.states.length} état{document.states.length !== 1 ? 's' : ''}<span className="footer-dot">·</span>{document.transitions.length} transition{document.transitions.length !== 1 ? 's' : ''}</span>
      <span role="status" className={warning ? 'storage-warning' : 'storage-indicator'} title={warning || 'Sauvegarde locale dans ce navigateur'}>
        {warning || <><Check size={13} /><span className="storage-text">Local</span></>}</span></div>
    {edgeDraft && <div className="dialog-backdrop" onClick={() => { setEdgeDraft(null); setSource(null); }}>
      <form className="transition-dialog" role="dialog" aria-modal="true" aria-labelledby="transition-title" onClick={e => e.stopPropagation()}
        onKeyDown={e => { if (e.key === 'Tab') { const controls = Array.from(e.currentTarget.querySelectorAll<HTMLElement>('input, button'));
          if (e.shiftKey && window.document.activeElement === controls[0]) { e.preventDefault(); controls.at(-1)?.focus(); }
          else if (!e.shiftKey && window.document.activeElement === controls.at(-1)) { e.preventDefault(); controls[0]?.focus(); } } }}
        onSubmit={e => { e.preventDefault();
          if (transitionConflict(current.current, edgeDraft.source, edgeDraft.symbol)) return;
          if (current.current.transitions.length >= LIMITS.transitions) { setNotice('Limite du POC : 4 000 transitions.'); setEdgeDraft(null); return; }
          const id = crypto.randomUUID(); const next = appendTransition(current.current, { id, ...edgeDraft });
          if (next === current.current) { setEdgeDraft(null); setSource(null); return; }
          commit(next);
          setEdgeDraft(null); setSource(null); setSelection({ kind: 'transition', id }); setTool('select'); }}>
        <h2 id="transition-title">Nouvelle transition</h2><p>{document.states.find(s => s.id === edgeDraft.source)?.label} → {document.states.find(s => s.id === edgeDraft.target)?.label}</p>
        <label>Symbole<input autoFocus aria-label="Symbole de la nouvelle transition" aria-invalid={!!draftConflict}
          aria-describedby={draftConflict ? 'draft-conflict' : undefined} maxLength={64} value={edgeDraft.symbol} onChange={e => setEdgeDraft({ ...edgeDraft, symbol: e.target.value })} /></label>
        {draftConflict && <p id="draft-conflict" className="inline-error" role="alert">{conflictMessage(edgeDraft.source, edgeDraft.symbol)}</p>}
        <small>Un symbole par transition. Alphabet : {parseAlphabet(document.alphabetText).join(', ') || '∅'}</small>
        <div className="dialog-actions"><button type="button" className="secondary-button" onClick={() => { setEdgeDraft(null); setSource(null); }}>Annuler</button>
          <button type="submit" className="primary-button" disabled={!!draftConflict}>Ajouter</button></div>
      </form>
    </div>}
  </main>;
}

export default function App() { return <ReactFlowProvider><Editor /></ReactFlowProvider>; }
