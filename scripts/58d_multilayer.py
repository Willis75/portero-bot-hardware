"""
58d — Multi-layer A* router (F.Cu + B.Cu + vias between).

State = (i, j, layer). Transitions:
  - Same-layer move: 8 neighbors, cost = step, check seg clear on that layer
  - Layer switch: via cost = via_drill_step, check via_clear (both layers)

Solves the case where pad's local F.Cu pocket is isolated — A* can
insert vias to escape into B.Cu and back.
"""
import sys, math, heapq, time
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"
DRY = "--dry" in sys.argv

CLEAR=0.15; TRACK_W=0.25; VIA_DIA=0.60; VIA_DRILL=0.30
HW=TRACK_W/2; HV=VIA_DIA/2

GRID=0.5
X_MIN=80.0; X_MAX=160.0
Y_MIN=60.0; Y_MAX=150.0

F=pcbnew.F_Cu; B=pcbnew.B_Cu
LAY={F:"F", B:"B"}
ANT=(122.25,47.145,170.25,68.085)

def dpp(p,q): return math.hypot(p[0]-q[0],p[1]-q[1])
def dps(p,a,b):
    ax,ay=a;bx,by=b;px,py=p
    dx,dy=bx-ax,by-ay; L2=dx*dx+dy*dy
    if L2<1e-12: return dpp(p,a)
    t=max(0.0,min(1.0,((px-ax)*dx+(py-ay)*dy)/L2))
    return dpp(p,(ax+t*dx, ay+t*dy))
def dss(a,b,c,d):
    def s(x): return (x>1e-9)-(x<-1e-9)
    def cr(o,p,q): return (p[0]-o[0])*(q[1]-o[1])-(p[1]-o[1])*(q[0]-o[0])
    if s(cr(a,b,c))*s(cr(a,b,d))<0 and s(cr(c,d,a))*s(cr(c,d,b))<0: return 0.0
    return min(dps(a,c,d),dps(b,c,d),dps(c,a,b),dps(d,a,b))
def in_ant(x,y,m=CLEAR): return (ANT[0]-m)<=x<=(ANT[2]+m) and (ANT[1]-m)<=y<=(ANT[3]+m)
def seg_ant(a,b,m=CLEAR):
    if in_ant(a[0],a[1],m) or in_ant(b[0],b[1],m): return True
    rs=[((ANT[0],ANT[1]),(ANT[2],ANT[1])),((ANT[2],ANT[1]),(ANT[2],ANT[3])),
        ((ANT[2],ANT[3]),(ANT[0],ANT[3])),((ANT[0],ANT[3]),(ANT[0],ANT[1]))]
    return any(dss(a,b,r1,r2)<m for r1,r2 in rs)

board=pcbnew.LoadBoard(PCB)
TARGET=["RELAY1_GPIO","BOOT","BST_5V"]
nets={n:board.FindNet(n) for n in TARGET}
obs={F:[], B:[]}

for t in list(board.GetTracks()):
    n=t.GetNetname(); cls=t.GetClass()
    if cls=="PCB_VIA":
        p=t.GetPosition(); x,y=p.x/1e6,p.y/1e6
        obs[F].append(("cir",(x,y),0.30,n)); obs[B].append(("cir",(x,y),0.30,n))
    elif cls=="PCB_TRACK":
        s=t.GetStart(); e=t.GetEnd()
        a=(s.x/1e6,s.y/1e6); b=(e.x/1e6,e.y/1e6)
        hw=t.GetWidth()/2/1e6; L=t.GetLayer()
        if L in obs: obs[L].append(("seg",a,b,hw,n))
for fp in board.GetFootprints():
    for pad in fp.Pads():
        c=pad.GetCenter(); x,y=c.x/1e6,c.y/1e6
        sz=pad.GetSize(); rr=max(sz.x,sz.y)/2/1e6
        n=pad.GetNetname()
        for layer in (F,B):
            try:
                if pad.IsOnLayer(layer): obs[layer].append(("cir",(x,y),rr,n))
            except: obs[layer].append(("cir",(x,y),rr,n))
print(f"Obs: F={len(obs[F])}, B={len(obs[B])}")

def chk_seg(layer, a, b, self_net):
    if seg_ant(a,b): return False
    for o in obs[layer]:
        if o[-1]==self_net and o[-1]!="": continue
        if o[0]=="cir":
            _,c,r,n=o; d=dps(c,a,b)
            if dpp(c,a)<0.05 or dpp(c,b)<0.05: continue
            if d+1e-6<HW+r+CLEAR: return False
        else:
            _,p1,p2,hw,n=o; d=dss(a,b,p1,p2)
            if d+1e-6<HW+hw+CLEAR: return False
    return True

def chk_via(x, y, self_net):
    if in_ant(x,y): return False
    for layer in (F,B):
        for o in obs[layer]:
            if o[-1]==self_net and o[-1]!="": continue
            if o[0]=="cir":
                _,c,r,n=o; d=dpp((x,y),c)
                if dpp(c,(x,y))<0.05: continue
                if d+1e-6<HV+r+CLEAR: return False
            else:
                _,p1,p2,hw,n=o; d=dps((x,y),p1,p2)
                if d+1e-6<HV+hw+CLEAR: return False
    return True

NX=int((X_MAX-X_MIN)/GRID)+1
NY=int((Y_MAX-Y_MIN)/GRID)+1
def i2x(i): return X_MIN+i*GRID
def i2y(j): return Y_MIN+j*GRID
def x2i(x): return int(round((x-X_MIN)/GRID))
def y2j(y): return int(round((y-Y_MIN)/GRID))

DIRS=[(1,0,1.0),(-1,0,1.0),(0,1,1.0),(0,-1,1.0),
      (1,1,1.4142),(-1,1,1.4142),(1,-1,1.4142),(-1,-1,1.4142)]

VIA_COST = 2.0  # extra penalty per via (in mm); discourages too many vias

def astar_ml(s_xy, g_xy, self_net, max_visits=400000, fixed_start_layer=None, fixed_goal_layer=None):
    """A* in (i,j,layer) state space. Returns list of (x,y,layer) or None."""
    si,sj=x2i(s_xy[0]),y2j(s_xy[1])
    gi,gj=x2i(g_xy[0]),y2j(g_xy[1])

    # Start state(s)
    start_states = []
    for L in (F, B):
        if fixed_start_layer is not None and L != fixed_start_layer: continue
        start_states.append((si, sj, L))
    # Goal states
    goal_states = set()
    for L in (F, B):
        if fixed_goal_layer is not None and L != fixed_goal_layer: continue
        goal_states.add((gi, gj, L))

    def h(node):
        return math.hypot(node[0]-gi, node[1]-gj) * GRID

    open_heap = []
    came = {}
    gscore = {}
    for s in start_states:
        gscore[s] = 0
        came[s] = None
        heapq.heappush(open_heap, (h(s), 0, s))
    closed = set()
    v = 0
    while open_heap:
        f, g, c = heapq.heappop(open_heap)
        if c in closed: continue
        closed.add(c); v += 1
        if v > max_visits: return None, v
        if c in goal_states:
            path = []
            n = c
            while n is not None:
                path.append((i2x(n[0]), i2y(n[1]), n[2]))
                n = came[n]
            path.reverse()
            return path, v
        ci, cj, cl = c
        a = (i2x(ci), i2y(cj))
        # Same-layer moves
        for di, dj, cost in DIRS:
            ni, nj = ci+di, cj+dj
            if not (0<=ni<NX and 0<=nj<NY): continue
            nxt = (ni, nj, cl)
            if nxt in closed: continue
            ng = g + cost*GRID
            if nxt in gscore and gscore[nxt] <= ng: continue
            b = (i2x(ni), i2y(nj))
            if not chk_seg(cl, a, b, self_net): continue
            gscore[nxt] = ng
            came[nxt] = c
            heapq.heappush(open_heap, (ng + h(nxt), ng, nxt))
        # Via to other layer
        other = B if cl == F else F
        nxt = (ci, cj, other)
        if nxt not in closed:
            ng = g + VIA_COST
            if not (nxt in gscore and gscore[nxt] <= ng):
                if chk_via(a[0], a[1], self_net):
                    gscore[nxt] = ng
                    came[nxt] = c
                    heapq.heappush(open_heap, (ng + h(nxt), ng, nxt))
    return None, v

def simplify_layered(path):
    """Reduce path to corners + via points. Output: list of segments and vias."""
    if len(path) <= 1: return []
    # path is [(x,y,layer), ...]
    out = []
    i = 0
    while i < len(path):
        # collect same-layer run
        j = i
        while j+1 < len(path) and path[j+1][2] == path[i][2]:
            # also must be co-linear with previous
            j += 1
        # path[i..j] all same layer
        # simplify to corners
        sub = path[i:j+1]
        # corner reduction
        corners = [sub[0]]
        for k in range(1, len(sub)-1):
            ax, ay, _ = sub[k-1]
            bx, by, _ = sub[k]
            cx, cy, _ = sub[k+1]
            dx1, dy1 = bx-ax, by-ay
            dx2, dy2 = cx-bx, cy-by
            if abs(dx1*dy2 - dy1*dx2) > 1e-6:
                corners.append(sub[k])
        corners.append(sub[-1])
        for k in range(len(corners)-1):
            l = corners[k][2]
            out.append(("seg", l, corners[k][0], corners[k][1], corners[k+1][0], corners[k+1][1]))
        # if there's a next layer change, add via at that point
        if j+1 < len(path):
            vx, vy = path[j][0], path[j][1]
            out.append(("via", vx, vy))
        i = j+1
    return out

# ==================== APPLY ====================
def mm(v): return int(v*1e6)
def pt(x,y): return pcbnew.VECTOR2I(mm(x),mm(y))
def add_seg(net,layer,x1,y1,x2,y2):
    t=pcbnew.PCB_TRACK(board); t.SetStart(pt(x1,y1)); t.SetEnd(pt(x2,y2))
    t.SetLayer(layer); t.SetWidth(mm(TRACK_W)); t.SetNet(net); board.Add(t)
    obs[layer].append(("seg",(x1,y1),(x2,y2),HW,net.GetNetname()))
def add_via(net,x,y):
    v=pcbnew.PCB_VIA(board); v.SetPosition(pt(x,y))
    v.SetWidth(mm(VIA_DIA)); v.SetDrill(mm(VIA_DRILL))
    v.SetNet(net); v.SetLayerPair(F,B); board.Add(v)
    obs[F].append(("cir",(x,y),HV,net.GetNetname()))
    obs[B].append(("cir",(x,y),HV,net.GetNetname()))

# ==================== ENDPOINTS ====================
# pad_pos, pad_layer (most endpoints are F.Cu SMD; SW1.1 also F.Cu)
ENDPOINTS = {
    "RELAY1_GPIO": [
        ("R7.1", (115.84, 115.21), F),
        ("U1.8", (137.50, 78.525), F),
    ],
    "BOOT": [
        ("R2.2", (113.48, 125.25), F),
        ("SW1.1", (134.635, 132.0), F),
        ("U1.25", (155.00, 86.145), F),
    ],
    "BST_5V": [
        ("C22.1", (99.0, 130.57), F),
        ("U4.1", (145.55, 112.605), F),
    ],
}

def route_net(name):
    print(f"\n=== {name} ===")
    eps = ENDPOINTS[name]
    all_items = []
    for i in range(len(eps)-1):
        label1, p1, l1 = eps[i]
        label2, p2, l2 = eps[i+1]
        print(f"  ML A* {label1}→{label2}: ({p1[0]:.2f},{p1[1]:.2f},{LAY[l1]}) → ({p2[0]:.2f},{p2[1]:.2f},{LAY[l2]})")
        t0 = time.time()
        path, v = astar_ml(p1, p2, name, max_visits=600000,
                           fixed_start_layer=l1, fixed_goal_layer=l2)
        dt = time.time() - t0
        if path is None:
            print(f"    FAIL ({dt:.1f}s, {v} visits)")
            return False
        items = simplify_layered(path)
        nvias = sum(1 for it in items if it[0]=="via")
        nsegs = sum(1 for it in items if it[0]=="seg")
        print(f"    OK ({dt:.1f}s, {v} visits, {len(path)} cells, {nsegs} segs, {nvias} vias)")
        all_items.extend(items)
    if DRY: return True
    net_obj = nets[name]
    for it in all_items:
        if it[0]=="via":
            add_via(net_obj, it[1], it[2])
        else:
            _, l, x1, y1, x2, y2 = it
            add_seg(net_obj, l, x1, y1, x2, y2)
    return True

# ==================== RUN ====================
results = {}
for n in TARGET:
    results[n] = route_net(n)

if not DRY and any(results.values()):
    board.Save(PCB)
    print(f"\nSaved {PCB}")
print(f"\nRESULTS: {results}  DRY={DRY}")
