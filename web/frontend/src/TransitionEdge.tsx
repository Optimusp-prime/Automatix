import { BaseEdge, EdgeLabelRenderer, useInternalNode, type Edge, type EdgeProps } from '@xyflow/react';
import { transitionGeometry } from './geometry';
import type { Point } from './geometry';
import type { PointerEvent } from 'react';

export type TransitionFlowEdge = Edge<{ symbols: { id: string; symbol: string }[]; bend: number; invalid: boolean; curve?: Point; editable?: boolean;
  route?: ReturnType<typeof transitionGeometry>; crowded?: boolean;
  onBendStart?: (event: PointerEvent<Element>, id: string, curve: Point) => void; onSelect: (id: string) => void }, 'transition'>;

export function TransitionEdge({ id, source, target, data, selected, markerEnd }: EdgeProps<TransitionFlowEdge>) {
  const from = useInternalNode(source), to = useInternalNode(target);
  if (!from || !to || !data) return null;
  const sourceRadius = (from.width ?? from.measured.width ?? 64) / 2;
  const targetRadius = (to.width ?? to.measured.width ?? 64) / 2;
  const a = { x: from.internals.positionAbsolute.x + sourceRadius, y: from.internals.positionAbsolute.y + sourceRadius };
  const b = { x: to.internals.positionAbsolute.x + targetRadius, y: to.internals.positionAbsolute.y + targetRadius };
  const curve = data.route ?? transitionGeometry(a, b, data.bend, source === target, data.curve, sourceRadius, targetRadius);
  return <>
    <BaseEdge id={id} path={curve.path} markerEnd={markerEnd} interactionWidth={24}
      style={{ strokeWidth: selected ? 2.3 : 1.6, stroke: data.invalid ? 'var(--error)' : selected ? 'var(--accent)' : 'var(--edge)' }} />
    {data.editable && <path d={curve.path} className="rope-hit-area nodrag nopan" fill="none" stroke="transparent" strokeWidth={24}
      onPointerDown={event => data.onBendStart?.(event, id, curve.control)} />}
    <EdgeLabelRenderer><div className={`transition-label nodrag nopan ${selected ? 'selected' : ''} ${data.invalid ? 'invalid' : ''} ${data.crowded ? 'crowded' : ''}`}
      title={data.crowded ? 'Tracé serré : écartez les états ou ajustez cette courbe.' : undefined}
      style={{ transform: `translate(-50%, -50%) translate(${curve.label.x}px,${curve.label.y}px)` }}>
      {data.symbols.map((member, index) => <span key={member.id}>
        {index > 0 && <span aria-hidden="true">, </span>}
        <button className="transition-symbol" onClick={event => { event.stopPropagation(); data.onSelect(member.id); }}
          aria-label={`Modifier la transition ${member.symbol || 'sans symbole'}`}>
          {member.symbol || '…'}
        </button>
      </span>)}
    </div></EdgeLabelRenderer>
  </>;
}
