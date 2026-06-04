"""
82_fix_j2_user_position.py
Limpia 2 detalles tras movimiento manual del J2 por el user:
1. Elimina GND track huerfano @ (142.16, 99.75)-(139.90, 102.15)
2. Conecta J2 SH superior (171.05, 87.63) con SH inferior (171.05, 103.12) via F.Cu
"""
import os, pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))
TRACK_W = 250_000  # 0.25mm
TOL = 50_000

board = pcbnew.LoadBoard(PCB)

def near(p, target):
    return abs(p.x - target[0]) <= TOL and abs(p.y - target[1]) <= TOL

# 1. Find and remove dangling GND track
target_s = (int(142.1625 * 1e6), int(99.7500 * 1e6))
target_e = (int(139.9006 * 1e6), int(102.1458 * 1e6))

removed = 0
for t in list(board.GetTracks()):
    if t.Type() != pcbnew.PCB_TRACE_T: continue
    n = t.GetNet()
    if not n or n.GetNetname() != 'GND': continue
    s = t.GetStart()
    e = t.GetEnd()
    if (near(s, target_s) and near(e, target_e)) or (near(s, target_e) and near(e, target_s)):
        board.Remove(t)
        removed += 1
        print(f'  Removed dangling GND track: ({s.x/1e6:.3f},{s.y/1e6:.3f}) -> ({e.x/1e6:.3f},{e.y/1e6:.3f})')

print(f'Removed {removed} dangling tracks')

# 2. Get GND net
gnd_net = None
for ni in range(1, board.GetNetInfo().GetNetCount()):
    n = board.GetNetInfo().GetNetItem(ni)
    if n and n.GetNetname() == 'GND':
        gnd_net = n
        break

# Add track J2 SH sup -> SH inf (F.Cu, vertical at X=171.05)
SH_SUP = (int(171.05 * 1e6), int(87.63 * 1e6))
SH_INF = (int(171.05 * 1e6), int(103.12 * 1e6))

t = pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(*SH_SUP))
t.SetEnd(pcbnew.VECTOR2I(*SH_INF))
t.SetWidth(TRACK_W)
t.SetLayer(pcbnew.F_Cu)
t.SetNet(gnd_net)
board.Add(t)
print(f'  Added F.Cu track SH_sup (171.05, 87.63) -> SH_inf (171.05, 103.12)')

pcbnew.SaveBoard(PCB, board)
print(f'\nSaved: {PCB}')
