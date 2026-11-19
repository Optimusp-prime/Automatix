import { useEffect, useMemo, useRef, useState } from 'react';
import { ReactFlow, ReactFlowProvider, MarkerType } from '@xyflow/react';
import { ArrowRight, Check, Copy, LoaderCircle, X } from 'lucide-react';
import { toPayload, type EditorDocument } from './model';
import { StateNode } from './StateNode';
import { TransitionEdge, type TransitionFlowEdge } from './TransitionEdge';
import { stateFlowNode } from './flowNodes';
import { routeTransitions } from './routeTransitions';
import { displayStates } from './stateSize';

const operations = [
  { id: 'to_regex', title: 'Automate → expression régulière', description: 'Décrire le langage de votre DFA.' },
  { id: 'from_regex', title: 'Expression régulière → automate', description: 'Construire un DFA par dérivées.' },
  { id: 'from_regex_minimized', title: 'Expression régulière → automate minimal', description: 'Construire puis minimiser le DFA.' },
] as const;
const nodeTypes = { state: StateNode }, edgeTypes = { transition: TransitionEdge };
type Operation = typeof operations[number]['id'];
type Result = { kind: 'regex'; expression: string } | { kind: 'dfa'; document: EditorDocument };

function Preview({ document }: { document: EditorDocument }) {
  const states = useMemo(() => displayStates(document.states, document.transitions), [document]);
  const routes = useMemo(() => routeTransitions(states, document.transitions), [states, document.transitions]);
  const edges: TransitionFlowEdge[] = routes.map(({ members: group, geometry, crowded }) => {
    const e = group[0];
    return { id: e.id, source: e.source, target: e.target, type: 'transition',
      markerEnd: { type: MarkerType.ArrowClosed, color: '#777e86' },
      data: { symbols: group.map(p => ({ id: p.id, symbol: p.symbol })), invalid: false,
        bend: 0, route: geometry, crowded,
        onSelect: () => {} } };
  });
  return <div className="algorithm-preview" aria-label="Aperçu de l’automate résultat">
    <ReactFlowProvider><ReactFlow nodes={states.map(s => stateFlowNode(s, false, false, false))} edges={edges}
      nodeTypes={nodeTypes} edgeTypes={edgeTypes} fitView fitViewOptions={{ padding: .5 }}
      nodesDraggable={false} nodesConnectable={false} elementsSelectable={false}
      deleteKeyCode={null} proOptions={{ hideAttribution: true }} minZoom={.05} /></ReactFlowProvider>
  </div>;
}

export function AlgorithmPanel({ document, onApply, onClose }: {
  document: EditorDocument; onApply: (next: EditorDocument) => void; onClose: () => void;
}) {
  const [operation, setOperation] = useState<Operation>('to_regex');
  const [expression, setExpression] = useState('');
  const [result, setResult] = useState<Result | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const active = useRef<AbortController | null>(null);
  useEffect(() => {
    active.current?.abort(); setPending(false); setResult(null); setError(''); setCopied(false);
    return () => active.current?.abort();
  }, [document, operation, expression]);

  async function run() {
    active.current?.abort(); const controller = new AbortController(); active.current = controller;
    setPending(true); setResult(null); setError(''); setCopied(false);
    const timer = setTimeout(() => controller.abort('timeout'), 20000);
    try {
      const response = await fetch('/api/algorithms/regex', { method: 'POST', signal: controller.signal,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ operation, expression, draft: toPayload(document) }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(typeof payload.detail === 'string' ? payload.detail : 'Entrée non prise en charge. Vérifiez l’expression et les limites.');
      if (controller.signal.aborted) return;
      if (payload.kind === 'regex' && typeof payload.expression === 'string') setResult(payload);
      else if (payload.kind === 'dfa' && payload.draft) {
        const draft = payload.draft as ReturnType<typeof toPayload>;
        const columns = Math.max(1, Math.ceil(Math.sqrt(draft.states.length)));
        setResult({ kind: 'dfa', document: { version: 1, alphabetText: draft.alphabet.join(', '),
          states: draft.states.map((s, index) => ({ ...s, x: 100 + index % columns * 180,
            y: 140 + Math.floor(index / columns) * 180 })), transitions: draft.transitions } });
      } else throw new Error('Réponse inattendue du serveur.');
    } catch (reason) {
      if (!controller.signal.aborted || controller.signal.reason === 'timeout') setError(
        controller.signal.reason === 'timeout' ? 'Le calcul a expiré. Simplifiez l’entrée.'
          : reason instanceof TypeError ? 'API inaccessible. Vérifiez que le serveur Python est démarré.'
          : reason instanceof Error ? reason.message : 'Conversion impossible.');
    } finally { clearTimeout(timer); if (active.current === controller) setPending(false); }
  }

  return <aside className="algorithm-panel" aria-label="Algorithmes">
    <div className="panel-heading"><strong>Algorithmes</strong><button aria-label="Fermer les algorithmes" onClick={onClose}><X size={17} /></button></div>
    <p className="algorithm-category">Expressions régulières</p>
    <div className="algorithm-options">{operations.map(item => <button key={item.id} aria-pressed={operation === item.id}
      onClick={() => setOperation(item.id)}><span>{item.title}<small>{item.description}</small></span><ArrowRight size={15} /></button>)}</div>
    {operation !== 'to_regex' && <label className="algorithm-input">Expression
      <textarea value={expression} maxLength={120} placeholder="(a|b)*abb" onChange={e => setExpression(e.target.value)} />
      <small>Alphabet de la feuille : {document.alphabetText || '∅'}. Union : | · concaténation : ab · étoile : * · mot vide : ε ou () · langage vide : ∅ seul.</small>
    </label>}
    <button className="primary-button algorithm-run" disabled={pending} onClick={() => void run()}>
      {pending ? <LoaderCircle size={16} className="spin" /> : <ArrowRight size={16} />}{pending ? 'Calcul en cours…' : 'Exécuter'}</button>
    {error && <p className="inline-error" role="alert">{error}</p>}
    {result && <section className="algorithm-result" aria-live="polite"><div className="panel-heading"><strong>Résultat</strong>
      {result.kind === 'regex' && <button aria-label="Copier l’expression" onClick={() => {
        void navigator.clipboard.writeText(result.expression).then(() => setCopied(true)).catch(() => setError('Copie indisponible : sélectionnez le texte du résultat.'));
      }}>{copied ? <Check size={16} /> : <Copy size={16} />}{copied ? 'Copié' : 'Copier'}</button>}</div>
      {result.kind === 'regex' ? <pre className="regex-result">{result.expression}</pre> : <>
        <p>{result.document.states.length} états · {result.document.transitions.length} transitions</p>
        <Preview document={result.document} />
        <button className="primary-button algorithm-run" onClick={() => onApply(result.document)}>Utiliser sur la feuille</button>
        <small>Remplace le dessin actuel. Annuler permet de le retrouver.</small>
      </>}
    </section>}
  </aside>;
}
