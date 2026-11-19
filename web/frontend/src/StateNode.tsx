import { Handle, NodeResizer, Position, type Node, type NodeProps } from '@xyflow/react';
import type { PointerEvent } from 'react';
import type { Point } from './geometry';
import { stateTextColor } from './stateColor';

export type StateFlowNode = Node<{ label: string; initial: boolean; final: boolean; invalid: boolean; source: boolean; color?: string;
  diameter: number; minDiameter: number; resizable?: boolean; onResizeStart?: () => void; onResizeEnd?: () => void;
  connectable?: boolean; dropTarget?: boolean; onConnectStart?: (event: PointerEvent<Element>, id: string, direction: Point) => void }, 'state'>;

export function StateNode({ id, data, selected }: NodeProps<StateFlowNode>) {
  const background = data.color ?? '#ffffff';
  const foreground = stateTextColor(background);
  return <div style={{ width: data.diameter, height: data.diameter }} className={`state-node ${data.final ? 'final' : ''} ${selected ? 'selected' : ''} ${data.invalid ? 'invalid' : ''} ${data.source ? 'connection-source' : ''} ${data.dropTarget ? 'drop-target' : ''}`}>
    <svg className="state-outline" width={data.diameter} height={data.diameter} aria-hidden="true">
      <circle className="state-outline-outer" style={{ fill: background }} cx={data.diameter / 2} cy={data.diameter / 2} r={data.diameter / 2 - .8} />
      {data.final && <circle className="state-outline-inner" style={{ stroke: foreground }} cx={data.diameter / 2} cy={data.diameter / 2} r={data.diameter / 2 - 6.5} />}
    </svg>
    <NodeResizer isVisible={!!data.resizable && selected} minWidth={data.minDiameter} minHeight={data.minDiameter}
      maxWidth={2048} maxHeight={2048} keepAspectRatio color="var(--accent)"
      onResizeStart={data.onResizeStart} onResizeEnd={data.onResizeEnd} />
    {data.initial && <span className="initial-arrow" aria-label="État initial" />}
    <Handle type="target" position={Position.Left} isConnectable={false} />
    <span className="state-name" style={{ color: foreground }} title={data.label}>{data.label || '…'}</span>
    {data.final && <span className="sr-only">État final</span>}
    <Handle type="source" position={Position.Right} isConnectable={false} />
    {data.connectable && [{ name: 'haut', x: 0, y: -1 }, { name: 'droite', x: 1, y: 0 },
      { name: 'bas', x: 0, y: 1 }, { name: 'gauche', x: -1, y: 0 }].map(point =>
      <button key={point.name} className={`connection-point connection-point-${point.name} nodrag nopan`}
        aria-label={`Relier ${data.label} — ${point.name}`} title="Tirer vers un état"
        onPointerDown={event => data.onConnectStart?.(event, id, point)} onClick={event => event.stopPropagation()} />)}
  </div>;
}
