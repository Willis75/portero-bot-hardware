"""
58c — A* router on B.Cu 0.5mm grid for RELAY1_GPIO, BOOT, BST_5V.

For each net:
  1. F.Cu escape from each endpoint pad to a clear nearby via location.
  2. A* on B.Cu grid (0.5mm step, 8-neighbor) connecting each via.
  3. F.Cu stub at destination side.

A* uses Manhattan-ish heuristic and verifies each grid edge segment is clear
on B.Cu before traversing. Builds path in (x,y) world coordinates,
simplifies to long straight runs, then emits as track segments.
"""
import sys, math, heapq, time
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"
DRY = "--dry" in sys.argv

CLEAR=0.15; TRACK_W=0.25; VIA_DIA=0.60; VIA_DRILL=0.30
HW=TRACK_W/2; HV=VIA_DIA/2
GRID = 0.5  # mm
X_MIN, X_MAX = 80.0, 160.0
Y_MIN, Y_MAX = 60.0, 150.0

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

board = pcbnew.LoadBoard(PCB)
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

# ==================== CLEARANCE FNS ====================
def chk_seg_b(a, b, self_net, ignore_endpoint_pads=False):
    """B.Cu clearance check. Returns True if clear."""
    if seg_ant(a, b): return False
    for o in obs[B]:
        if o[-1]==self_net and o[-1]!="": continue
        if o[0]=="cir":
            _,c,r,n=o; d=dps(c,a,b)
            if ignore_endpoint_pads and (dpp(c,a)<0.05 or dpp(c,b)<0.05): continue
            if d + 1e-6 < HW + r + CLEAR: return False
        else:
            _,p1,p2,hw,n=o; d=dss(a,b,p1,p2)
            if d + 1e-6 < HW + hw + CLEAR: return False
    return True

def chk_via_b(x, y, self_net):
    if in_ant(x, y): return False
    for layer in (F, B):
        for o in obs[layer]:
            if o[-1]==self_net and o[-1]!="": continue
            if o[0]=="cir":
                _,c,r,n=o; d=dpp((x,y),c)
                if dpp(c,(x,y))<0.05: continue
                if d + 1e-6 < HV + r + CLEAR: return False
            else:
                _,p1,p2,hw,n=o; d=dps((x,y),p1,p2)
                if d + 1e-6 < HV + hw + CLEAR: return False
    return True

def chk_seg_f(a, b, self_net):
    if seg_ant(a, b): return False
    for o in obs[F]:
        if o[-1]==self_net and o[-1]!="": continue
        if o[0]=="cir":
            _,c,r,n=o; d=dps(c,a,b)
            if dpp(c,a)<0.05 or dpp(c,b)<0.05: continue
            if d + 1e-6 < HW + r + CLEAR: return False
        else:
            _,p1,p2,hw,n=o; d=dss(a,b,p1,p2)
            if d + 1e-6 < HW + hw + CLEAR: return False
    return True

# ==================== A* GRID ====================
NX = int((X_MAX - X_MIN) / GRID) + 1
NY = int((Y_MAX - Y_MIN) / GRID) + 1
def i2x(i): return X_MIN + i * GRID
def i2y(j): return Y_MIN + j * GRID
def x2i(x): return int(round((x - X_MIN) / GRID))
def y2j(y): return int(round((y - Y_MIN) / GRID))

# Precompute "is cell a valid trace point on B.Cu" for the current net
# Actually for trace we care about segments not cells. Use seg check between cells.

# 8-neighbor offsets
DIRS = [(1,0,1.0), (-1,0,1.0), (0,1,1.0), (0,-1,1.0),
        (1,1,1.4142), (-1,1,1.4142), (1,-1,1.4142), (-1,-1,1.4142)]

def astar(start_xy, goal_xy, self_net, cell_size=0.5):
    """A* B.Cu pathfinding. Returns list of (x,y) points or None."""
    si, sj = x2i(start_xy[0]), y2j(start_xy[1])
    gi, gj = x2i(goal_xy[0]), y2j(goal_xy[1])
    start = (si, sj); goal = (gi, gj)

    def h(node):
        return math.hypot(node[0]-gi, node[1]-gj) * cell_size

    open_heap = [(h(start), 0.0, start, None)]
    came_from = {}
    g_score = {start: 0.0}

    visited_count = 0
    while open_heap:
        f, g, cur, parent = heapq.heappop(open_heap)
        if cur in came_from and g_score[cur] < g: continue
        if cur not in came_from: came_from[cur] = parent
        visited_count += 1
        if visited_count > 100000:
            print(f"    A* abort: visited {visited_count}")
            return None
        if cur == goal:
            # reconstruct
            path = []
            n = cur
            while n is not None:
                path.append((i2x(n[0]), i2y(n[1])))
                n = came_from[n]
            path.reverse()
            return path
        ci, cj = cur
        a = (i2x(ci), i2y(cj))
        for di, dj, cost in DIRS:
            ni, nj = ci+di, cj+dj
            if not (0 <= ni < NX and 0 <= nj < NY): continue
            nxt = (ni, nj)
            ng = g + cost * cell_size
            if nxt in g_score and g_score[nxt] <= ng: continue
            b = (i2x(ni), i2y(nj))
            if not chk_seg_b(a, b, self_net): continue
            g_score[nxt] = ng
            came_from[nxt] = cur
            heapq.heappush(open_heap, (ng + h(nxt), ng, nxt, cur))
    return None

def simplify_path(path):
    """Reduce path to corners only (where direction changes)."""
    if len(path) <= 2: return path
    out = [path[0]]
    for i in range(1, len(path)-1):
        dx1 = path[i][0] - path[i-1][0]
        dy1 = path[i][1] - path[i-1][1]
        dx2 = path[i+1][0] - path[i][0]
        dy2 = path[i+1][1] - path[i][1]
        # if direction same, skip
        # normalize via small tolerance
        if abs(dx1*dy2 - dy1*dx2) > 1e-6:
            out.append(path[i])
    out.append(path[-1])
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

# ==================== ENDPOINT VIA SELECTION ====================
# Endpoint pads and pre-computed clear via candidates
ENDPOINTS = {
    "RELAY1_GPIO": [
        # R10/R11/R12 removed — RELAY1_GPIO now just R7.1 ↔ U1.8
        ("R7.1",  (115.84,115.21), (115.34,114.71)),
        ("U1.8",  (137.50,78.525), (136.50,78.525)),
    ],
    "BOOT": [
        ("R2.2",  (113.48,125.25), (112.73,125.75)),
        ("SW1.1", (134.635,132.0), (134.635,132.75)),
        ("U1.25", (155.00,86.145), (156.50,86.89)),
    ],
    "BST_5V": [
        ("C22.1", (99.0,130.57), (98.00,131.82)),
        ("U4.1",  (145.55,112.605), (145.55,111.86)),
    ],
}

def route_net(name):
    print(f"\n=== {name} ===")
    eps = ENDPOINTS[name]

    # Step 1: F.Cu escape from each pad to its via location
    f_escapes = []
    via_positions = []
    for label, pad_pos, via_pos in eps:
        if not chk_seg_f(pad_pos, via_pos, name):
            print(f"  WARN F.Cu escape {label}: blocked")
        f_escapes.append((label, pad_pos, via_pos))
        via_positions.append(via_pos)

    # Step 2: A* connect via_positions in chain: via[0] -> via[1] -> via[2]
    # Build full B.Cu path
    full_b_paths = []
    for i in range(len(via_positions)-1):
        start = via_positions[i]
        goal = via_positions[i+1]
        print(f"  A* {eps[i][0]}→{eps[i+1][0]}: ({start[0]:.2f},{start[1]:.2f}) → ({goal[0]:.2f},{goal[1]:.2f})")
        t0 = time.time()
        path = astar(start, goal, name)
        dt = time.time() - t0
        if path is None:
            print(f"    A* FAILED ({dt:.1f}s)")
            return False
        simplified = simplify_path(path)
        print(f"    A* OK ({dt:.1f}s, {len(path)} cells, {len(simplified)} corners)")
        full_b_paths.append(simplified)

    # Apply if not dry
    if DRY: return True
    net_obj = nets[name]
    for label, pad_pos, via_pos in f_escapes:
        add_seg(net_obj, F, pad_pos[0], pad_pos[1], via_pos[0], via_pos[1])
        add_via(net_obj, via_pos[0], via_pos[1])
    for bpath in full_b_paths:
        for i in range(len(bpath)-1):
            add_seg(net_obj, B, bpath[i][0], bpath[i][1], bpath[i+1][0], bpath[i+1][1])
    return True

# ==================== RUN ====================
results = {}
for n in TARGET:
    results[n] = route_net(n)

if not DRY and any(results.values()):
    board.Save(PCB)
    print(f"\nSaved {PCB}")
print(f"\nRESULTS: {results}  DRY={DRY}")
