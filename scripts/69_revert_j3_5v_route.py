"""
69_revert_j3_5v_route.py
Revierte el ruteo 5V automatico de script 68 que cruzaba RELAY3_COIL_LOW + BST_3V3.
Mantiene: tracks GND y las vias GND fijas.
Borra:
  - F.Cu (113.4, 148) -> (113.4, 146.5) [solo el nuevo]
  - VIA @ (113.4, 146.5)
  - B.Cu (113.4, 146.5) -> (113.46, 137.025)
"""
import os, pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))
TOL = 50_000  # 50um

board = pcbnew.LoadBoard(PCB)

# Targets a eliminar (start, end o pos)
targets = [
    ('TRACK', 'F.Cu', (113_400_000, 148_000_000), (113_400_000, 146_500_000)),
    ('TRACK', 'B.Cu', (113_400_000, 146_500_000), (113_460_000, 137_025_000)),
    ('VIA',   None,   (113_400_000, 146_500_000), None),
]

def match_point(p, target, tol=TOL):
    return abs(p.x - target[0]) <= tol and abs(p.y - target[1]) <= tol

def match_segment(s, e, t_s, t_e, tol=TOL):
    # match either direction
    return (match_point(s, t_s, tol) and match_point(e, t_e, tol)) or \
           (match_point(s, t_e, tol) and match_point(e, t_s, tol))

removed = 0
for t in list(board.GetTracks()):
    n = t.GetNet()
    if not n or n.GetNetname() != '5V': continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        for kind, layer, pos, _ in targets:
            if kind != 'VIA': continue
            if match_point(p, pos):
                board.Remove(t)
                removed += 1
                print(f'  removed VIA @ ({p.x/1e6:.3f},{p.y/1e6:.3f})')
                break
    else:
        layer_name = board.GetLayerName(t.GetLayer())
        s, e = t.GetStart(), t.GetEnd()
        for kind, layer, t_s, t_e in targets:
            if kind != 'TRACK' or layer != layer_name: continue
            if match_segment(s, e, t_s, t_e):
                board.Remove(t)
                removed += 1
                print(f'  removed {layer_name} ({s.x/1e6:.3f},{s.y/1e6:.3f})->({e.x/1e6:.3f},{e.y/1e6:.3f})')
                break

print(f'\nRemoved {removed} items.')
pcbnew.SaveBoard(PCB, board)
print(f'Saved: {PCB}')
