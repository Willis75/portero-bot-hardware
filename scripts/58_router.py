"""
Script 58 — Geometric router v3 for RELAY1_GPIO, BOOT, BST_5V.

Built on confirmed clear corridors (from 58b probe):
  Verticals B.Cu: x=92.5-93 y=[60,150] (full), x=156.5-160 y=[69,150], x=120-122 y=[60,88]
                  x=132.5-133.5 y=[69,100], x=144.5 y=[98,119]
  Horizontals B.Cu: y=78 x=[111.5,138], y=86 x=[80,100.5], y=88 x=[121.5,135.5],
                    y=112 x=[80,106], y=130 x=[145,160], y=145 x=[80,138.5], y=147-148 full

Clear via spots near endpoints (from probe):
  R7.1: (115.34,114.71), (115.59,114.46)
  R10.1: (116.34,123.24), (116.34,122.24), (115.84,123.49)
  R2.2: (112.73,125.75)
  C22.1: (99.50,130.07), (99.00,129.82)
  near U1.8: (136.75,78.53), (136.50,78.53)
  near U1.25: (155.00,86.89), (154.75,86.89)
  near U4.1: (145.05,112.11), (144.80,112.61), (145.55,111.86)
"""
import sys, math
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"
DRY = "--dry" in sys.argv

CLEAR=0.17; TRACK_W=0.25; VIA_DIA=0.60; VIA_DRILL=0.30
HW=TRACK_W/2; HV=VIA_DIA/2

F=pcbnew.F_Cu; B=pcbnew.B_Cu
LAY={F:"F", B:"B"}
ANT_X1,ANT_Y1,ANT_X2,ANT_Y2=122.25,47.145,170.25,68.085

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
def in_ant(x,y,m=CLEAR): return (ANT_X1-m)<=x<=(ANT_X2+m) and (ANT_Y1-m)<=y<=(ANT_Y2+m)
def seg_ant(a,b,m=CLEAR):
    if in_ant(a[0],a[1],m) or in_ant(b[0],b[1],m): return True
    rs=[((ANT_X1,ANT_Y1),(ANT_X2,ANT_Y1)),((ANT_X2,ANT_Y1),(ANT_X2,ANT_Y2)),
        ((ANT_X2,ANT_Y2),(ANT_X1,ANT_Y2)),((ANT_X1,ANT_Y2),(ANT_X1,ANT_Y1))]
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

def chk_seg(layer,a,b,self_net):
    if seg_ant(a,b): return [("ANTENNA",0.0,CLEAR)]
    res=[]
    for o in obs[layer]:
        if o[-1]==self_net and o[-1]!="": continue
        if o[0]=="cir":
            _,c,r,n=o; d=dps(c,a,b); need=HW+r+CLEAR
            if d+1e-6<need:
                if dpp(c,a)<0.05 or dpp(c,b)<0.05: continue
                res.append((f"cir[{n}]@({c[0]:.2f},{c[1]:.2f})",d,need))
        else:
            _,p1,p2,hw,n=o; d=dss(a,b,p1,p2); need=HW+hw+CLEAR
            if d+1e-6<need:
                res.append((f"seg[{n}]({p1[0]:.1f},{p1[1]:.1f})-({p2[0]:.1f},{p2[1]:.1f})",d,need))
    return res

def chk_via(x,y,self_net):
    if in_ant(x,y): return [("ANTENNA",0.0,CLEAR)]
    res=[]
    for layer in (F,B):
        for o in obs[layer]:
            if o[-1]==self_net and o[-1]!="": continue
            if o[0]=="cir":
                _,c,r,n=o; d=dpp((x,y),c); need=HV+r+CLEAR
                if d+1e-6<need:
                    if dpp(c,(x,y))<0.05: continue
                    res.append((f"{LAY[layer]}_cir[{n}]@({c[0]:.2f},{c[1]:.2f})",d,need))
            else:
                _,p1,p2,hw,n=o; d=dps((x,y),p1,p2); need=HV+hw+CLEAR
                if d+1e-6<need:
                    res.append((f"{LAY[layer]}_seg[{n}]({p1[0]:.1f},{p1[1]:.1f})-({p2[0]:.1f},{p2[1]:.1f})",d,need))
    return res

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

def try_path(name, path):
    self_net=name; issues=[]
    for idx,it in enumerate(path):
        if it[0]=="via":
            c=chk_via(it[1],it[2],self_net)
            if c: issues.append((idx,f"via@({it[1]:.2f},{it[2]:.2f})",c))
        else:
            l,x1,y1,x2,y2=it
            c=chk_seg(l,(x1,y1),(x2,y2),self_net)
            if c: issues.append((idx,f"{LAY[l]}_seg({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f})",c))
    if issues:
        print(f"  REJECT [{len(issues)} conf]")
        for idx,label,confs in issues[:6]:
            print(f"    #{idx} {label}:")
            for c in confs[:2]:
                print(f"       vs {c[0]} d={c[1]:.3f} need={c[2]:.3f}")
        return False
    if not DRY:
        for it in path:
            if it[0]=="via": add_via(nets[name], it[1], it[2])
            else: add_seg(nets[name], it[0], it[1], it[2], it[3], it[4])
    print(f"  APPLY ok ({len(path)} items)")
    return True

def line(layer, *pts):
    return [(layer, pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1]) for i in range(len(pts)-1)]

# ==================== CANDIDATES ====================

# ============ RELAY1_GPIO ============
# Approach U1.8 via clear y=78 horizontal x=[111.5,138]
# Vias at R7.1, R10.1, near U1.8 (x=136.5 or 135.5, y=78.525)
# Need B.Cu trunk from R7+R10 vias to bottom strip then to y=78 corridor

# R1_E: use x=92.5 (full clear vertical) as main trunk
# R7.1 → via (115.34,114.71); B.Cu west to x=92.5; south to y=147; east to x=132.5; north to y=78; east to via near U1.8
# R10.1 → via (116.34,123.24); B.Cu west to x=92.5 path (will join R7's path on x=92.5)
R1_E = (
      # R7.1 escape F.Cu NW
      line(F, (115.84,115.21), (115.34,114.71))
    + [("via", 115.34, 114.71)]
      # B.Cu R7-via west along y=114.71? Need to verify
    + line(B, (115.34,114.71), (115.34,113.0))               # try a tiny B.Cu north first
    + line(B, (115.34,113.0), (108.0,113.0))                 # west at y=113
    + line(B, (108.0,113.0), (108.0,112.0))                  # north to y=112 (clear x=80-106)
    + line(B, (108.0,112.0), (92.5,112.0))                   # west to x=92.5 (y=112 clear x=80-106 ends at 106 — won't reach 92.5 cleanly? but 92.5 < 106 so ok)
      # R10.1 escape
    + line(F, (115.84,122.74), (116.34,123.24))
    + [("via", 116.34, 123.24)]
    + line(B, (116.34,123.24), (116.34,140.0))               # south at x=116.34 to y=140 (y=140 clear x=80-114, but x=116 not in clear horiz at y=140)
    + line(B, (116.34,140.0), (114.0,140.0))                 # west to x=114
    + line(B, (114.0,140.0), (92.5,140.0))                   # west at y=140 to x=92.5
      # Main trunk x=92.5 going from y=112 (R7) to y=140 (R10) connected
    + line(B, (92.5,112.0), (92.5,140.0))                    # x=92.5 fully clear
    + line(B, (92.5,140.0), (92.5,147.0))                    # x=92.5 to bottom strip
      # Bottom strip east to x=132.5
    + line(B, (92.5,147.0), (132.5,147.0))                   # bottom strip clear x=80-160
      # North up x=132.5 (clear y=69-100)
    + line(B, (132.5,147.0), (132.5,100.0))                  # need clear at x=132.5 y=100-147
    + line(B, (132.5,100.0), (132.5,78.0))                   # x=132.5 clear y=69-100
      # East at y=78 (clear x=111.5-138) to U1.8 region
    + line(B, (132.5,78.0), (136.5,78.0))
    + line(B, (136.5,78.0), (136.5,78.525))                  # tiny south to U1.8 level
    + [("via", 136.5, 78.525)]
    + line(F, (136.5,78.525), (137.5,78.525))                # F stub east to U1.8
)

# R1_F: simpler — both R7 & R10 vias connect via short L on B.Cu, then single trunk
# R7-via (115.34,114.71), R10-via (116.34,123.24)
# Connect on B.Cu via diagonal NE jog
R1_F = (
      line(F, (115.84,115.21), (115.34,114.71))
    + [("via", 115.34, 114.71)]
    + line(F, (115.84,122.74), (115.84,123.49))
    + [("via", 115.84, 123.49)]
      # B.Cu small connect from R7-via to R10-via
    + line(B, (115.34,114.71), (115.84,123.49))              # diagonal SE
      # B.Cu from R10-via south to y=147 via clear x=92.5 path
    + line(B, (115.84,123.49), (108.0,123.49))               # west at y=123 (probably blocked)
    + line(B, (108.0,123.49), (108.0,140.0))                 # south at x=108 (cor x=108-110 y=77-108 clear)
    + line(B, (108.0,140.0), (92.5,140.0))                   # west to x=92.5
    + line(B, (92.5,140.0), (92.5,147.0))                    # south to bottom strip
    + line(B, (92.5,147.0), (133.0,147.0))                   # east on bottom strip
    + line(B, (133.0,147.0), (133.0,100.0))                  # north x=133 (clear y=69-100)
    + line(B, (133.0,100.0), (133.0,78.0))
    + line(B, (133.0,78.0), (136.5,78.0))                    # east at y=78
    + line(B, (136.5,78.0), (136.5,78.525))
    + [("via", 136.5, 78.525)]
    + line(F, (136.5,78.525), (137.5,78.525))
)

# ============ BOOT ============
# R2.2 → via (112.73,125.75) SW
# SW1.1 (134.635,132.0) F.Cu only — need to approach on F.Cu
# U1.25 → via (155.00,86.89) south
# R2.2 escape via at (112.73,125.75) (south of pad)
# Then B.Cu west, south, east route to SW1.1
# B_C: full path via x=92.5 corridor
B_C = (
      line(F, (113.48,125.25), (112.73,125.75))               # diag SW
    + [("via", 112.73, 125.75)]
    + line(B, (112.73,125.75), (108.0,125.75))                # west at y=125.75
    + line(B, (108.0,125.75), (108.0,140.0))                  # south at x=108
    + line(B, (108.0,140.0), (92.5,140.0))                    # west to x=92.5
    + line(B, (92.5,140.0), (92.5,147.0))                     # south
      # Bottom strip east to x=134.635 (SW1 column)
    + line(B, (92.5,147.0), (134.635,147.0))
      # north up x=134.635 to SW1.1
    + line(B, (134.635,147.0), (134.635,132.75))              # north (SW1.1 pad south edge at y=131)
    + [("via", 134.635, 132.75)]
    + line(F, (134.635,132.75), (134.635,132.0))              # F stub to SW1.1
      # Continue from bottom strip east to right edge column
    + line(B, (134.635,147.0), (156.5,147.0))                 # east
    + line(B, (156.5,147.0), (156.5,86.89))                   # north x=156.5 (clear y=69-150)
    + line(B, (156.5,86.89), (155.0,86.89))                   # west to via location
    + [("via", 155.0, 86.89)]
    + line(F, (155.0,86.89), (155.0,86.145))                  # F stub north to U1.25
)

# B_D: alternative R2.2 escape via at (112.73,126.0) further south
B_D = (
      line(F, (113.48,125.25), (112.73,126.0))
    + [("via", 112.73, 126.0)]
    + line(B, (112.73,126.0), (108.0,126.0))
    + line(B, (108.0,126.0), (108.0,140.0))
    + line(B, (108.0,140.0), (92.5,140.0))
    + line(B, (92.5,140.0), (92.5,147.0))
    + line(B, (92.5,147.0), (134.635,147.0))
    + line(B, (134.635,147.0), (134.635,132.75))
    + [("via", 134.635, 132.75)]
    + line(F, (134.635,132.75), (134.635,132.0))
    + line(B, (134.635,147.0), (156.5,147.0))
    + line(B, (156.5,147.0), (156.5,86.89))
    + line(B, (156.5,86.89), (155.0,86.89))
    + [("via", 155.0, 86.89)]
    + line(F, (155.0,86.89), (155.0,86.145))
)

# ============ BST_5V ============
# C22.1 (99.0,130.57) → via (99.50,130.07) NE
# U4.1 (145.55,112.605) — clear via spots: (145.05,112.11), (144.80,112.61), (145.55,111.86)
# Best approach: B.Cu trunk → x=156.5 corridor up → west at y=112 (clear x=80-106 NOT useful) or y=130 (x=145-160 clear)
# Try: from bottom strip east to x=156.5, north to y=112.11, west to (145.05,112.11), via, F.Cu south to U4.1
BST_D = (
      line(F, (99.0,130.57), (99.5,130.07))                   # diag NE
    + [("via", 99.5, 130.07)]
    + line(B, (99.5,130.07), (99.5,140.0))                    # south at x=99.5
    + line(B, (99.5,140.0), (92.5,140.0))                     # west to x=92.5
    + line(B, (92.5,140.0), (92.5,147.0))                     # south
    + line(B, (92.5,147.0), (156.5,147.0))                    # bottom strip east
    + line(B, (156.5,147.0), (156.5,112.11))                  # north x=156.5
    + line(B, (156.5,112.11), (145.05,112.11))                # west at y=112 (clear x=80-106 only ?)
    + [("via", 145.05, 112.11)]
    + line(F, (145.05,112.11), (145.55,112.605))              # F stub SE to U4.1
)

# BST_E: approach U4.1 from north via x=145
BST_E = (
      line(F, (99.0,130.57), (99.5,130.07))
    + [("via", 99.5, 130.07)]
    + line(B, (99.5,130.07), (99.5,140.0))
    + line(B, (99.5,140.0), (92.5,140.0))
    + line(B, (92.5,140.0), (92.5,147.0))
    + line(B, (92.5,147.0), (156.5,147.0))
    + line(B, (156.5,147.0), (156.5,130.0))                   # north to y=130
    + line(B, (156.5,130.0), (145.0,130.0))                   # west at y=130 (clear x=145-160)
    + line(B, (145.0,130.0), (145.0,122.0))                   # north at x=145 (clear y=122-150)
      # Need to bridge from y=122 to y=119 area — gap region
    + line(B, (145.0,122.0), (144.5,122.0))                   # west tiny
    + line(B, (144.5,122.0), (144.5,119.0))                   # south at x=144.5 (clear y=98-119)
    + line(B, (144.5,119.0), (144.5,112.61))                  # continue south to via location
    + [("via", 144.8, 112.61)]
    + line(B, (144.5,112.61), (144.8,112.61))                 # final connect on B (might fail — via is on F too)
    + line(F, (144.8,112.61), (145.55,112.605))               # F stub to U4.1
)

# BST_F: simpler — via at (145.55,111.86) just north of U4.1
BST_F = (
      line(F, (99.0,130.57), (99.5,130.07))
    + [("via", 99.5, 130.07)]
    + line(B, (99.5,130.07), (99.5,140.0))
    + line(B, (99.5,140.0), (92.5,140.0))
    + line(B, (92.5,140.0), (92.5,147.0))
    + line(B, (92.5,147.0), (156.5,147.0))
    + line(B, (156.5,147.0), (156.5,130.0))
    + line(B, (156.5,130.0), (145.5,130.0))                   # west at y=130 to x=145.5
    + line(B, (145.5,130.0), (145.5,122.0))                   # south at x=145.5 (clear y=123-150)
    # Need to get to (145.55, 111.86): jog through unclear region
    + line(B, (145.5,122.0), (144.5,122.0))                   # west tiny
    + line(B, (144.5,122.0), (144.5,114.0))                   # south at x=144.5 (clear y=98-119)
    + line(B, (144.5,114.0), (145.05,114.0))                  # east
    + line(B, (145.05,114.0), (145.05,112.11))                # south
    + [("via", 145.05, 112.11)]
    + line(F, (145.05,112.11), (145.55,112.605))
)

# ==================== EXECUTE ====================
results = {}
for name, candidates_named in [
    ("RELAY1_GPIO", [("R1_E", R1_E), ("R1_F", R1_F)]),
    ("BOOT",        [("B_C", B_C),  ("B_D", B_D)]),
    ("BST_5V",      [("BST_D", BST_D), ("BST_E", BST_E), ("BST_F", BST_F)]),
]:
    print(f"\n=== {name} ===")
    placed = False
    for cname, cand in candidates_named:
        print(f"  {cname}:")
        if try_path(name, cand):
            placed = True; break
    results[name] = placed

if not DRY and any(results.values()):
    board.Save(PCB)
    print(f"\nSaved {PCB}")

print(f"\nRESULTS: {results}  DRY={DRY}")
