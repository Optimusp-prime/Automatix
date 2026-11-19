import { transitionGeometry, type Point } from './geometry';
import type { DraftState, DraftTransition } from './model';
import { stateSize } from './stateSize';

type Geometry = ReturnType<typeof transitionGeometry>;
type Segment = { a: Point; b: Point; owner: string };
type Box = { x: number; y: number; width: number; height: number };
export type RoutedTransition = { members: DraftTransition[]; geometry: Geometry; crowded: boolean };
const STEPS = 40, CELL = 80;
const distance = (a: Point, b: Point) => Math.hypot(a.x-b.x, a.y-b.y);
function segmentDistance(p: Point, a: Point, b: Point) {
  const dx = b.x-a.x, dy = b.y-a.y;
  const t = Math.max(0, Math.min(1, ((p.x-a.x)*dx + (p.y-a.y)*dy) / (dx*dx+dy*dy || 1)));
  return distance(p, { x: a.x+t*dx, y: a.y+t*dy });
}
function segments(g: Geometry, owner: string): Segment[] {
  return Array.from({ length: STEPS }, (_, i) => ({ a: g.pointAt(i/STEPS), b: g.pointAt((i+1)/STEPS), owner }));
}
function bounds(s: Segment, padding: number): Box {
  return { x: Math.min(s.a.x,s.b.x)-padding, y: Math.min(s.a.y,s.b.y)-padding,
    width: Math.abs(s.b.x-s.a.x)+2*padding, height: Math.abs(s.b.y-s.a.y)+2*padding };
}
const overlaps = (a: Box,b: Box) => a.x < b.x+b.width && a.x+a.width > b.x && a.y < b.y+b.height && a.y+a.height > b.y;
function crossesBox(s: Segment, box: Box) {
  let low=0, high=1;
  for (const axis of ['x','y'] as const) {
    const start=s.a[axis], delta=s.b[axis]-start, min=box[axis];
    const max=min+(axis==='x'?box.width:box.height);
    if (Math.abs(delta)<1e-9) { if (start<min || start>max) return false; }
    else { const t1=(min-start)/delta, t2=(max-start)/delta;
      low=Math.max(low,Math.min(t1,t2)); high=Math.min(high,Math.max(t1,t2));
      if(low>high) return false;
    }
  }
  return true;
}

/** Ephemeral spatial index of rendered segments; never stored on automata. */
class SegmentIndex {
  private cells = new Map<string, Segment[]>();
  private all: Segment[] = [];
  private overflow: Segment[] = [];
  private keys(box: Box) {
    const left=Math.floor(box.x/CELL), right=Math.floor((box.x+box.width)/CELL);
    const top=Math.floor(box.y/CELL), bottom=Math.floor((box.y+box.height)/CELL);
    // A broad-phase index must never enumerate an unbounded coordinate span.
    if (![left,right,top,bottom].every(Number.isSafeInteger) || (right-left+1)*(bottom-top+1)>4096) return null;
    const keys: string[] = [];
    for (let x=left; x<=right; x++)
      for (let y=top; y<=bottom; y++) keys.push(`${x},${y}`);
    return keys;
  }
  add(s: Segment) { this.all.push(s); const keys=this.keys(bounds(s,0));
    if (!keys) { this.overflow.push(s); return; }
    for (const key of keys) {
    const list=this.cells.get(key); if (list) list.push(s); else this.cells.set(key,[s]);
  } }
  query(box: Box) { const keys=this.keys(box);
    return new Set(keys ? [...this.overflow,...keys.flatMap(key => this.cells.get(key) ?? [])] : this.all); }
}

/** Display-only routing. Bounded candidate search; no draft/history mutations.
 * Worst-case O(C*G*S*(Q+G*S)) with G groups, Q states, C<=25, S=40;
 * local segment indexing reduces comparisons on sparse drawings.
 * A crowded flag exposes unresolved dense/overlapping layouts instead of claiming
 * a collision-free route. Ordinary transverse crossings remain allowed.
 */
export function routeTransitions(states: readonly DraftState[], transitions: readonly DraftTransition[],
  drag?: { id: string; curve: Point } | null): RoutedTransition[] {
  const circles = states.map(s => { const r=stateSize(s)/2; return { id:s.id, r, x:s.x+r, y:s.y+r }; });
  const nodes = new Map(circles.map(s => [s.id,s]));
  const groups = new Map<string,DraftTransition[]>();
  for (const e of transitions) { const key=JSON.stringify([e.source,e.target]);
    const group=groups.get(key); if (group) group.push(e); else groups.set(key,[e]); }
  // Short local edges go first; longer edges detour around their occupied lanes.
  const ordered = [...groups.values()].sort((a,b) => {
    const span=(e:DraftTransition) => { const s=nodes.get(e.source),t=nodes.get(e.target); return s&&t?distance(s,t):0; };
    return span(a[0])-span(b[0]) || a[0].id.localeCompare(b[0].id);
  });
  const index = new SegmentIndex(), routed: RoutedTransition[] = [];
  for (const members of ordered) {
    const e=members[0], a=nodes.get(e.source), b=nodes.get(e.target);
    if (!a || !b) continue;
    const loop=e.source===e.target, length=distance(a,b);
    const opposite=!loop && groups.has(JSON.stringify([e.target,e.source]));
    const manual=drag && members.some(p=>p.id===drag.id) ? drag.curve : e.curve;
    const base=transitionGeometry(a,b,opposite?48:0,loop,manual,a.r,b.r);
    const candidates=[base];
    const normal={ x:-(b.y-a.y)/(length||1), y:(b.x-a.x)/(length||1) };
    const step=Math.max(80, a.r+b.r+32, length*.22);
    for (let level=1;level<=6;level++) {
      if (loop) {
        for (const angle of [0,Math.PI/2,Math.PI,3*Math.PI/2]) {
          const reach=a.r+64+(level-1)*60;
          candidates.push(transitionGeometry(a,b,0,true,{ x:Math.cos(angle)*reach,y:Math.sin(angle)*reach },a.r,b.r));
        }
      } else for (const sign of [-1,1]) candidates.push(transitionGeometry(a,b,0,false,
        { x:base.control.x+normal.x*step*level*sign, y:base.control.y+normal.y*step*level*sign },a.r,b.r));
    }
    function cost(g:Geometry) {
      let nodeHits=0, shared=0;
      for (const s of segments(g,e.id)) {
        for (const node of circles) {
          // End circles are checked with a slightly smaller radius, since the
          // path starts/ends on their boundary. Other states get a safety margin.
          const radius=node.id===e.source || node.id===e.target ? node.r-3 : node.r+12;
          if (segmentDistance(node,s.a,s.b)<radius) nodeHits++;
        }
        const dx=s.b.x-s.a.x, dy=s.b.y-s.a.y, size=Math.hypot(dx,dy)||1;
        for (const other of index.query(bounds(s,9))) {
          const ox=other.b.x-other.a.x, oy=other.b.y-other.a.y, os=Math.hypot(ox,oy)||1;
          if (Math.abs((dx*ox+dy*oy)/(size*os)) < .97) continue;
          const middle={ x:(s.a.x+s.b.x)/2,y:(s.a.y+s.b.y)/2 };
          if (segmentDistance(middle,other.a,other.b)<9) shared+=size;
        }
      }
      return { nodeHits, shared, total:nodeHits*100000 + shared*100 + distance(g.control,base.control)*.02 };
    }
    let best=base, score=cost(base);
    // Preserve a clear hand-shaped curve. Otherwise choose the least obstructed
    // candidate rather than allowing a hidden transition underneath another state.
    if (score.nodeHits || score.shared>12) for (const candidate of candidates.slice(1)) {
      const next=cost(candidate); if (next.total<score.total) { best=candidate; score=next; }
      if (!score.nodeHits && score.shared<=12) break;
    }
    routed.push({ members, geometry:best, crowded:score.nodeHits>0 || score.shared>12 });
    for (const s of segments(best,e.id)) index.add(s);
  }
  // Label placement sees every route, including those selected later above.
  const labels: Box[]=[];
  for (const route of routed) {
    const g=route.geometry, owner=route.members[0].id;
    const width=Math.max(12,Array.from(route.members.map(e=>e.symbol||'…').join(', ')).length*8)+6;
    const choices=[g.label];
    for (const t of [.5,.38,.62,.26,.74]) {
      const p=g.pointAt(t), before=g.pointAt(t-.01), after=g.pointAt(t+.01);
      const length=distance(before,after)||1, nx=-(after.y-before.y)/length, ny=(after.x-before.x)/length;
      // Keep horizontal text clear even on vertical arcs with grouped symbols.
      const offset=Math.abs(nx)*width/2+Math.abs(ny)*9+3;
      for (const side of [-1,1]) choices.push({ x:p.x+nx*offset*side,y:p.y+ny*offset*side });
    }
    let best=g.label, bestCost=Infinity, bestBox:Box={x:0,y:0,width:0,height:0};
    for (const p of choices) {
      const box={ x:p.x-width/2,y:p.y-9,width,height:18 };
      let score=distance(p,g.label)*.02;
      for (const n of circles) {
        const closest={x:Math.max(box.x,Math.min(n.x,box.x+width)),y:Math.max(box.y,Math.min(n.y,box.y+18))};
        if(distance(n,closest)<n.r+5) score+=10000;
      }
      for (const label of labels) if(overlaps(box,label)) score+=5000;
      for (const s of index.query(box)) if(crossesBox(s,box)) score+=s.owner===owner?100:200;
      if(score<bestCost) { bestCost=score; best=p; bestBox=box; }
    }
    route.geometry={...g,label:best}; labels.push(bestBox);
    route.crowded ||= bestCost>=100;
  }
  return routed;
}
