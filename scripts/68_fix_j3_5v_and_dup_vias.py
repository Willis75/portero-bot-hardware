"""
68_fix_j3_5v_and_dup_vias.py
1. Elimina vias duplicadas en (116, 144.5) — mantiene solo 1
2. Conecta J3.1 (5V @ 113.4, 148.0) al track 5V en B.Cu @ (113.46, 137.025)
   path: F.Cu corto -> via -> B.Cu vertical
"""
import os, pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))

DUP_X, DUP_Y = 116_000_000, 144_500_000
DUP_TOL = 100_000

J3_1      = (113_400_000, 148_000_000)
VIA_POS   = (113_400_000, 146_500_000)  # 1.5mm arriba del pad J3.1
TARGET    = (113_460_000, 137_025_000)  # punto 5V B.Cu existente

TRACK_W   = 250_000
VIA_DIAM  = 600_000
VIA_DRILL = 300_000

board = pcbnew.LoadBoard(PCB)

# Encontrar netcodes
nets = {}
for ni in range(1, board.GetNetInfo().GetNetCount()):
    n = board.GetNetInfo().GetNetItem(ni)
    if n:
        nets[n.GetNetname()] = n
v5_net  = nets['5V']
print(f"5V netcode: {v5_net.GetNetCode()}")

# 1. Eliminar duplicados en (116, 144.5) — mantener 1
dups = []
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        if abs(p.x - DUP_X) <= DUP_TOL and abs(p.y - DUP_Y) <= DUP_TOL:
            dups.append(t)
print(f"Found {len(dups)} duplicate vias at (116, 144.5)")
removed = 0
for v in dups[1:]:  # mantener primera
    board.Remove(v)
    removed += 1
print(f"  removed {removed} duplicates, kept 1")

# 2. Conectar J3.1 (5V)
t1 = pcbnew.PCB_TRACK(board)
t1.SetStart(pcbnew.VECTOR2I(*J3_1))
t1.SetEnd(pcbnew.VECTOR2I(*VIA_POS))
t1.SetWidth(TRACK_W)
t1.SetLayer(pcbnew.F_Cu)
t1.SetNet(v5_net)
board.Add(t1)
print(f"  + F.Cu track J3.1 -> via")

via = pcbnew.PCB_VIA(board)
via.SetPosition(pcbnew.VECTOR2I(*VIA_POS))
via.SetWidth(VIA_DIAM)
via.SetDrill(VIA_DRILL)
via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
via.SetNet(v5_net)
board.Add(via)
print(f"  + VIA @ ({VIA_POS[0]/1e6:.3f},{VIA_POS[1]/1e6:.3f})")

t2 = pcbnew.PCB_TRACK(board)
t2.SetStart(pcbnew.VECTOR2I(*VIA_POS))
t2.SetEnd(pcbnew.VECTOR2I(*TARGET))
t2.SetWidth(TRACK_W)
t2.SetLayer(pcbnew.B_Cu)
t2.SetNet(v5_net)
board.Add(t2)
print(f"  + B.Cu track via -> target ({TARGET[0]/1e6:.3f},{TARGET[1]/1e6:.3f})")

pcbnew.SaveBoard(PCB, board)
print(f"\nSaved: {PCB}")
