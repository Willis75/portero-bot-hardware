"""
58b — probe clear B.Cu corridors.

For each candidate x in [80..165] step 1.0:
  Test seg from (x, 148) to (x, y_top) where y_top ranges over [70, 80, 90, 100, 110, 120, 130, 140].
  Report clear length per x (longest clear north-south stretch).

Similarly: scan horizontal corridors at various y.
"""
import sys, math
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"
CLEAR = 0.17
TRACK_W = 0.25
HW = TRACK_W/2

F = pcbnew.F_Cu; B = pcbnew.B_Cu
ANT = (122.25, 47.145, 170.25, 68.085)

def dpp(p,q): return math.hypot(p[0]-q[0], p[1]-q[1])
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

def in_ant(x,y,m=CLEAR):
    return (ANT[0]-m)<=x<=(ANT[2]+m) and (ANT[1]-m)<=y<=(ANT[3]+m)
def seg_ant(a,b,m=CLEAR):
    if in_ant(a[0],a[1],m) or in_ant(b[0],b[1],m): return True
    rs=[((ANT[0],ANT[1]),(ANT[2],ANT[1])),((ANT[2],ANT[1]),(ANT[2],ANT[3])),
        ((ANT[2],ANT[3]),(ANT[0],ANT[3])),((ANT[0],ANT[3]),(ANT[0],ANT[1]))]
    return any(dss(a,b,r1,r2)<m for r1,r2 in rs)

board = pcbnew.LoadBoard(PCB)
obs = {F:[], B:[]}
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

def chk(layer, a, b, ignore_nets=()):
    if seg_ant(a,b): return False
    for o in obs[layer]:
        if o[-1] in ignore_nets: continue
        if o[0]=="cir":
            _,c,r,n=o
            d = dps(c,a,b)
            need = HW + r + CLEAR
            if d + 1e-6 < need: return False
        else:
            _,p1,p2,hw,n=o
            d = dss(a,b,p1,p2)
            need = HW + hw + CLEAR
            if d + 1e-6 < need: return False
    return True

# For each x, scan clear y-segments
print("=== B.Cu vertical clear ranges (x_step=0.5, scan dy=1) ===")
print(f"{'x':>6} {'longest clear y-range':<30}")
for x_int in range(int(80*2), int(160*2)+1):
    x = x_int / 2
    # find longest clear y range between y=60 and y=149
    # discretize 1mm chunks and find longest run
    cells = []
    for y_int in range(60, 150):
        a = (x, y_int)
        b = (x, y_int + 1)
        cells.append(chk(B, a, b))
    # find longest run
    best_start = -1; best_len = 0
    cur_start = -1; cur_len = 0
    for i, ok in enumerate(cells):
        if ok:
            if cur_start < 0:
                cur_start = i
            cur_len += 1
            if cur_len > best_len:
                best_len = cur_len; best_start = cur_start
        else:
            cur_start = -1; cur_len = 0
    if best_len >= 20:
        print(f"  x={x:5.1f}  y=[{60+best_start},{60+best_start+best_len}] len={best_len}")

# Probe horizontal y corridors at key y values
print("\n=== B.Cu horizontal clear at y=148 (bottom strip): x ranges ===")
for x_start_int in range(int(80*2), int(160*2)+1):
    x = x_start_int / 2
    if chk(B, (x, 148), (x+0.5, 148)):
        pass  # silent
# show conflict spots only at y=148
print("Conflicts on y=148 B.Cu (each 0.5mm cell where blocked):")
blocked = []
for x_int in range(int(80*2), int(160*2)+1):
    x = x_int / 2
    if not chk(B, (x, 148), (x+0.5, 148)):
        blocked.append(x)
if blocked:
    print(f"  blocked at x = {blocked}")
else:
    print("  bottom strip y=148 fully clear x=[80..160]")

print("\n=== B.Cu horizontal clear at y=147 ===")
blocked = []
for x_int in range(int(80*2), int(160*2)+1):
    x = x_int / 2
    if not chk(B, (x, 147), (x+0.5, 147)):
        blocked.append(x)
print(f"  blocked: {blocked}" if blocked else "  fully clear")

# Probe potential via locations near each endpoint
ENDPOINTS = {
    "R7.1": (115.84, 115.21, "RELAY1_GPIO"),
    "R10.1": (115.84, 122.74, "RELAY1_GPIO"),
    "R2.2": (113.48, 125.25, "BOOT"),
    "C22.1": (99.0, 130.57, "BST_5V"),
    "near_U1.8": (137.5, 78.525, "RELAY1_GPIO"),
    "near_U1.25": (155.0, 86.145, "BOOT"),
    "near_U4.1": (145.55, 112.605, "BST_5V"),
}

# For each endpoint, scan 4mm radius grid (step 0.25mm) for clear via location
print("\n=== CLEAR VIA candidates near each endpoint (4mm radius, step 0.25mm) ===")
HV = 0.30
def via_clear(x, y, ignore_net):
    if in_ant(x, y): return False
    for layer in (F, B):
        for o in obs[layer]:
            if o[-1] == ignore_net and o[-1] != "": continue
            if o[0] == "cir":
                _, c, r, n = o
                d = dpp((x, y), c)
                # endpoint contact allowed
                if dpp(c, (x, y)) < 0.05: continue
                need = HV + r + CLEAR
                if d + 1e-6 < need: return False
            else:
                _, p1, p2, hw, n = o
                d = dps((x, y), p1, p2)
                need = HV + hw + CLEAR
                if d + 1e-6 < need: return False
    return True

for label, (ex, ey, net) in ENDPOINTS.items():
    candidates = []
    for dx_int in range(-16, 17):
        for dy_int in range(-16, 17):
            x = ex + dx_int * 0.25
            y = ey + dy_int * 0.25
            d = math.hypot(x - ex, y - ey)
            if d < 0.6 or d > 4.0:  # exclude on-pad or too far
                continue
            if via_clear(x, y, net):
                candidates.append((d, x, y))
    candidates.sort()
    print(f"  {label} @({ex:.2f},{ey:.2f}) net={net} → {len(candidates)} clear via spots")
    for d, x, y in candidates[:8]:
        print(f"     ({x:.2f},{y:.2f}) dist={d:.2f}")
