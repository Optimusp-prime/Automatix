import { describe, expect, it } from 'vitest';
import { displayStates, stateSize } from './stateSize';
import { stateTextColor } from './stateColor';
import { routeTransitions } from './routeTransitions';
import { emptyDocument, restoreDocument, toPayload, type DraftState, type DraftTransition } from './model';

const node = (id: string, x: number, y = 0): DraftState => ({ id, label:id, initial:false, final:false, x, y });
const edge = (id: string, source: string, target: string, symbol='a'): DraftTransition => ({ id,source,target,symbol });

describe('display sizing and color', () => {
  it('grows crowded states about their center without changing stored data', () => {
    const states = [node('q',400), ...Array.from({length:5},(_,i)=>node(`p${i}`,i*100,200))];
    const edges = states.slice(1).map((s,i)=>edge(`${i}`,s.id,'q'));
    const before=JSON.stringify(states), views=displayStates(states,edges), q=views[0];
    expect(stateSize(q)).toBe(124);
    expect(q.x+stateSize(q)/2).toBe(432);
    expect(q.y+stateSize(q)/2).toBe(32);
    expect(JSON.stringify(states)).toBe(before);
    expect(stateSize(displayStates(states,[])[0])).toBe(64);
    expect(stateSize(displayStates([{...states[0],size:200},...states.slice(1)],edges)[0])).toBe(200);
  });
  it('counts symbol groups once and handles initial arrows/loops', () => {
    const states=[{...node('q',0),initial:true},node('p',200)];
    const edges=[edge('a','p','q','a'),edge('b','p','q','b'),edge('c','q','q','c')];
    expect(stateSize(displayStates(states,edges)[0])).toBe(84);
  });
  it('preserves local colors but strips visual metadata from API', () => {
    const doc={...emptyDocument(),states:[{...node('q',0),color:'#123456'}]};
    expect(restoreDocument(JSON.stringify(doc))).toEqual(doc);
    expect(toPayload(doc).states[0]).not.toHaveProperty('color');
    expect(stateTextColor('#000000')).toBe('#ffffff');
    expect(stateTextColor('#ffffff')).toBe('#000000');
    expect(stateTextColor('#ff0000')).toBe('#000000');
  });
});

describe('obstacle routing', () => {
  it('rejects unusable coordinates from local storage', () => {
    const doc = {...emptyDocument(),states:[node('q',1e20)]};
    expect(restoreDocument(JSON.stringify(doc))).toBeNull();
  });
  it('bounds spatial enumeration even for extreme finite coordinates', () => {
    const routes = routeTransitions([node('a',0),node('b',1e20)], [edge('ab','a','b')]);
    expect(routes).toHaveLength(1);
    expect(routes[0].geometry.path).not.toMatch(/NaN|Infinity/);
  });
  it('routes q0 to q2 around the intervening q1 and retains grouped symbols', () => {
    const states=[node('q0',0),node('q1',180),node('q2',360)];
    const edges=[edge('01','q0','q1'),edge('12','q1','q2'),edge('02b','q0','q2','b'),edge('02c','q0','q2','c')];
    const original=JSON.stringify({states,edges});
    const routes=routeTransitions(states,edges), long=routes.find(r=>r.members[0].id==='02b')!;
    expect(routes).toHaveLength(3);
    expect(long.members.map(e=>e.symbol)).toEqual(['b','c']);
    for(let i=0;i<=100;i++) {
      const p=long.geometry.pointAt(i/100);
      expect(Math.hypot(p.x-212,p.y-32)).toBeGreaterThan(32);
    }
    expect(JSON.stringify({states,edges})).toBe(original);
  });
  it('keeps opposite edges distinct and loops attached to the current radius', () => {
    const states=[{...node('a',0),size:160},node('b',300)];
    const routes=routeTransitions(states,[edge('ab','a','b'),edge('ba','b','a'),edge('loop','a','a')]);
    expect(routes[1].geometry.path).not.toBe(routes[2].geometry.path);
    const loop=routes.find(r=>r.members[0].id==='loop')!;
    expect(Math.hypot(loop.geometry.start.x-80,loop.geometry.start.y-80)).toBeCloseTo(80);
    expect(loop.geometry.path).not.toMatch(/NaN|Infinity/);
  });
});
