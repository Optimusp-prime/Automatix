import type { DraftState } from './model';
import type { StateFlowNode } from './StateNode';
import { minimumStateSize, stateSize } from './stateSize';

/** Convert a mathematical draft state into the editor's controlled node. */
export function stateFlowNode(state: DraftState & { autoMinimum?: number }, selected: boolean, source: boolean, invalid: boolean): StateFlowNode {
  const diameter = stateSize(state);
  return { id: state.id, type: 'state', position: { x: state.x, y: state.y }, selected,
    // Preserve dimensions on every controlled update to prevent drag flicker.
    measured: { width: diameter, height: diameter }, width: diameter, height: diameter,
    ariaLabel: `État ${state.label}${state.initial ? ', initial' : ''}${state.final ? ', final' : ''}`,
    data: { label: state.label, initial: state.initial, final: state.final, color: state.color, source, invalid,
      diameter, minDiameter: Math.max(minimumStateSize(state.label), state.autoMinimum ?? 64) } };
}
