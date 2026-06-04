"""
70_fix_power_tree.py
Fix bugs criticos del power tree:
1. Net 'Net 2' (auto-generated por Flux) renombrado a VIN_BUCK + todos los pads/tracks
2. U4.6 (EN) y U5.6 (EN) flotantes -> tied a VIN_BUCK (su VIN respectivo)
3. Tracks tie EN-IN cortos (1.27mm vertical) en F.Cu para ambos bucks
4. Track de conexion fisica entre rails Net 2 (U5 side) y VIN_BUCK (U4 side) en B.Cu
"""
import os, pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))

TRACK_W = 250_000  # 0.25mm

# Posiciones (nm)
U4_6 = (150_500_000, 119_270_000)  # EN
U4_7 = (150_500_000, 118_000_000)  # IN (already VIN_BUCK)
U5_6 = (150_500_000, 125_855_000)  # EN
U5_7 = (150_500_000, 124_585_000)  # IN (was Net 2)
BRIDGE_A = (148_221_000, 114_221_000)  # VIN_BUCK B.Cu endpoint
BRIDGE_B = (147_771_000, 114_721_000)  # Net 2 via (B side)

board = pcbnew.LoadBoard(PCB)

# Buscar nets
vin_buck_net = None
net2_net = None
for ni in range(1, board.GetNetInfo().GetNetCount()):
    n = board.GetNetInfo().GetNetItem(ni)
    if not n: continue
    if n.GetNetname() == 'VIN_BUCK':
        vin_buck_net = n
    elif n.GetNetname() == 'Net 2':
        net2_net = n

assert vin_buck_net, "VIN_BUCK net not found"
assert net2_net, "Net 2 net not found"
print(f"VIN_BUCK netcode: {vin_buck_net.GetNetCode()}")
print(f"Net 2    netcode: {net2_net.GetNetCode()}")

# 1. Reasignar todos los pads/tracks de Net 2 a VIN_BUCK
print()
print("=== Step 1: reassign 'Net 2' -> VIN_BUCK ===")
n_pads = 0
n_tracks = 0
for fp in board.GetFootprints():
    for pad in fp.Pads():
        n = pad.GetNet()
        if n and n.GetNetCode() == net2_net.GetNetCode():
            pad.SetNet(vin_buck_net)
            n_pads += 1
            print(f'  pad {fp.GetReference()}.{pad.GetPadName()} -> VIN_BUCK')

for t in board.GetTracks():
    n = t.GetNet()
    if n and n.GetNetCode() == net2_net.GetCode() if hasattr(net2_net,'GetCode') else n.GetNetCode() == net2_net.GetNetCode():
        t.SetNet(vin_buck_net)
        n_tracks += 1

print(f"  Reassigned {n_pads} pads + {n_tracks} tracks")

# 2. Asignar U4.6 y U5.6 (EN) a VIN_BUCK
print()
print("=== Step 2: assign U4.6 and U5.6 (EN) to VIN_BUCK ===")
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref not in ('U4', 'U5'): continue
    for pad in fp.Pads():
        if pad.GetPadName() == '6':
            pad.SetNet(vin_buck_net)
            p = pad.GetPosition()
            print(f'  {ref}.6 (EN) @ ({p.x/1e6:.3f},{p.y/1e6:.3f}) -> VIN_BUCK')

# 3. Tracks tie EN-IN (cortos F.Cu)
print()
print("=== Step 3: add EN-IN tie tracks (F.Cu) ===")
for label, s, e in [
    ('U4 EN-IN tie', U4_6, U4_7),
    ('U5 EN-IN tie', U5_6, U5_7),
]:
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(*s))
    t.SetEnd(pcbnew.VECTOR2I(*e))
    t.SetWidth(TRACK_W)
    t.SetLayer(pcbnew.F_Cu)
    t.SetNet(vin_buck_net)
    board.Add(t)
    print(f'  + {label}: F.Cu ({s[0]/1e6:.3f},{s[1]/1e6:.3f}) -> ({e[0]/1e6:.3f},{e[1]/1e6:.3f})')

# 4. Track de conexion fisica entre rails (B.Cu)
print()
print("=== Step 4: bridge VIN_BUCK rail (U4 side) and former 'Net 2' rail (U5 side) ===")
t = pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(*BRIDGE_A))
t.SetEnd(pcbnew.VECTOR2I(*BRIDGE_B))
t.SetWidth(TRACK_W)
t.SetLayer(pcbnew.B_Cu)
t.SetNet(vin_buck_net)
board.Add(t)
print(f'  + bridge B.Cu ({BRIDGE_A[0]/1e6:.3f},{BRIDGE_A[1]/1e6:.3f}) -> ({BRIDGE_B[0]/1e6:.3f},{BRIDGE_B[1]/1e6:.3f})')

pcbnew.SaveBoard(PCB, board)
print(f"\nSaved: {PCB}")
