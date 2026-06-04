"""
66_connect_j3_gnd.py
Conecta J3.5 (GND) al track GND existente en B.Cu @ (116.614, 135.883).
Path: F.Cu (pad J3.5) -> via -> B.Cu hasta target.
"""
import os, pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))

# Coordenadas en nm
J3_5      = (116_000_000, 148_000_000)   # pad J3.5 (F.Cu top SMD)
VIA_POS   = (116_000_000, 146_500_000)   # 1.5mm salida del pad, F.Cu->B.Cu
TARGET    = (116_614_000, 135_883_000)   # punto GND existente en B.Cu

TRACK_W   = 250_000   # 0.25mm (Default netclass)
VIA_DIAM  = 600_000   # 0.6mm
VIA_DRILL = 300_000   # 0.3mm

board = pcbnew.LoadBoard(PCB)

# Encontrar GND netcode
gnd_nc = None
for ni in range(1, board.GetNetInfo().GetNetCount()):
    n = board.GetNetInfo().GetNetItem(ni)
    if n and n.GetNetname() == 'GND':
        gnd_nc = ni
        gnd_net = n
        break
assert gnd_nc, "GND net not found"
print(f"GND netcode: {gnd_nc}")

added = 0

# 1. Track F.Cu desde pad J3.5 a via
t1 = pcbnew.PCB_TRACK(board)
t1.SetStart(pcbnew.VECTOR2I(*J3_5))
t1.SetEnd(pcbnew.VECTOR2I(*VIA_POS))
t1.SetWidth(TRACK_W)
t1.SetLayer(pcbnew.F_Cu)
t1.SetNet(gnd_net)
board.Add(t1)
added += 1
print(f"  + F.Cu track {J3_5[0]/1e6:.2f},{J3_5[1]/1e6:.2f} -> {VIA_POS[0]/1e6:.2f},{VIA_POS[1]/1e6:.2f}")

# 2. Via F.Cu->B.Cu
via = pcbnew.PCB_VIA(board)
via.SetPosition(pcbnew.VECTOR2I(*VIA_POS))
via.SetWidth(VIA_DIAM)
via.SetDrill(VIA_DRILL)
via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
via.SetNet(gnd_net)
board.Add(via)
added += 1
print(f"  + VIA   {VIA_POS[0]/1e6:.2f},{VIA_POS[1]/1e6:.2f} (0.6/0.3mm)")

# 3. Track B.Cu desde via hasta target
t2 = pcbnew.PCB_TRACK(board)
t2.SetStart(pcbnew.VECTOR2I(*VIA_POS))
t2.SetEnd(pcbnew.VECTOR2I(*TARGET))
t2.SetWidth(TRACK_W)
t2.SetLayer(pcbnew.B_Cu)
t2.SetNet(gnd_net)
board.Add(t2)
added += 1
print(f"  + B.Cu track {VIA_POS[0]/1e6:.2f},{VIA_POS[1]/1e6:.2f} -> {TARGET[0]/1e6:.2f},{TARGET[1]/1e6:.2f}")

print(f"\nAdded {added} items (2 tracks + 1 via).")
pcbnew.SaveBoard(PCB, board)
print(f"Saved: {PCB}")
