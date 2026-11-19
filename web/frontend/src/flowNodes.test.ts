import { describe, expect, it } from 'vitest';
import { adoptUserNodes, nodeHasDimensions, Position, type InternalNodeBase } from '@xyflow/system';
import { stateFlowNode } from './flowNodes';
import type { StateFlowNode } from './StateNode';

describe('controlled node visibility during drag', () => {
  it('retains dimensions and edge anchors at every pointer update and on selection changes', () => {
    const state = { id: 'q0', label: 'q0', initial: true, final: false, x: 0, y: 0 };
    const lookup = new Map<string, InternalNodeBase<StateFlowNode>>();
    const parents = new Map<string, Map<string, InternalNodeBase<StateFlowNode>>>();
    adoptUserNodes([stateFlowNode(state, false, false, false)], lookup, parents);
    // The browser's first ResizeObserver measurement establishes the handles.
    const initial = lookup.get(state.id)!;
    initial.measured = { width: 64, height: 64 };
    initial.internals.handleBounds = {
      source: [{ id: null, nodeId: state.id, type: 'source', position: Position.Right, x: 61, y: 29, width: 6, height: 6 }],
      target: [{ id: null, nodeId: state.id, type: 'target', position: Position.Left, x: -3, y: 29, width: 6, height: 6 }],
    };
    for (let step = 0; step < 20; step++) {
      const next = stateFlowNode({ ...state, x: step * 10, y: step * 3 }, step % 2 === 0, false, false);
      const status = adoptUserNodes([next], lookup, parents);
      const internal = lookup.get(state.id)!;
      expect(nodeHasDimensions(internal), `state visible at frame ${step}`).toBe(true);
      expect(status.nodesInitialized).toBe(true);
      expect(internal.internals.handleBounds).toEqual(initial.internals.handleBounds);
      expect(internal.internals.positionAbsolute).toEqual({ x: step * 10, y: step * 3 });
    }
  });
});
