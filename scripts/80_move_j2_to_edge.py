"""
80_move_j2_to_edge.py
Mueve J2 (Hanrun HR911105A RJ45) al borde derecho del PCB.
- Posicion antigua: center (158.44, 95.54), rotation 0°, cara apunta +Y (dentro del PCB)
- Posicion nueva: center (174.4, 110), rotation 270° (90° CW), cara apunta +X (borde derecho)
- Cara queda al borde del PCB en X=187 -> cable Ethernet se puede enchufar

Pasos:
1. Move + rotate J2
2. Eliminar tracks viejos de ETH_TX_P/N, ETH_RX_P/N, GND y 3V3 que conectaban a J2 viejo
3. Agregar tracks nuevos cortos desde nuevas posiciones J2 a U2 W5500 + 3V3 + GND
"""
import os, pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))
board = pcbnew.LoadBoard(PCB)

NEW_J2_CENTER = (174_400_000, 110_000_000)  # nm
NEW_J2_ROT_DEG = 90  # 90° CCW (in KiCad screen view) -> face from +Y points to +X

# Find J2 and remember old pad positions
j2 = None
old_pad_positions = {}
for fp in board.GetFootprints():
    if fp.GetReference() == 'J2':
        j2 = fp
        for pad in fp.Pads():
            p = pad.GetPosition()
            old_pad_positions[pad.GetPadName()] = (p.x, p.y)
        break
assert j2

print(f'Old J2 center: ({j2.GetPosition().x/1e6:.2f}, {j2.GetPosition().y/1e6:.2f})')
print(f'Old J2 rotation: {j2.GetOrientation().AsDegrees()} deg')
print(f'Old pads:')
for pn, (x, y) in old_pad_positions.items():
    print(f'  pad {pn} @ ({x/1e6:.2f}, {y/1e6:.2f})')

# === STEP 1: Move + rotate J2 ===
j2.SetPosition(pcbnew.VECTOR2I(*NEW_J2_CENTER))
j2.SetOrientation(pcbnew.EDA_ANGLE(NEW_J2_ROT_DEG, pcbnew.DEGREES_T))

# Get new pad positions
new_pad_positions = {}
for pad in j2.Pads():
    p = pad.GetPosition()
    new_pad_positions[pad.GetPadName()] = (p.x, p.y)
print()
print(f'New J2 center: ({j2.GetPosition().x/1e6:.2f}, {j2.GetPosition().y/1e6:.2f})')
print(f'New J2 rotation: {j2.GetOrientation().AsDegrees()} deg')
print(f'New pads:')
for pn, (x, y) in new_pad_positions.items():
    print(f'  pad {pn} @ ({x/1e6:.2f}, {y/1e6:.2f})')

# === STEP 2: Delete tracks that connected to OLD J2 pad positions ===
# Tracks of nets ETH_TX_P, ETH_TX_N, ETH_RX_P, ETH_RX_N, 3V3, GND that touch old pad positions
TARGETS_NETS = {'ETH_TX_P','ETH_TX_N','ETH_RX_P','ETH_RX_N','3V3','GND'}
TOL = 50_000  # 50um

def near(p, target):
    return abs(p.x - target[0]) <= TOL and abs(p.y - target[1]) <= TOL

old_pad_pts = list(old_pad_positions.values())

removed_tracks = 0
for t in list(board.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T:
        # Check if via is at old pad position
        p = t.GetPosition()
        for target in old_pad_pts:
            if near(p, target):
                n = t.GetNet()
                if n and n.GetNetname() in TARGETS_NETS:
                    board.Remove(t)
                    removed_tracks += 1
                    break
    else:
        s = t.GetStart()
        e = t.GetEnd()
        n = t.GetNet()
        if not n or n.GetNetname() not in TARGETS_NETS: continue
        for target in old_pad_pts:
            if near(s, target) or near(e, target):
                board.Remove(t)
                removed_tracks += 1
                break

print()
print(f'Removed {removed_tracks} old tracks/vias connected to old J2 position')

pcbnew.SaveBoard(PCB, board)
print(f'Saved: {PCB}')
print()
print('NOTA: J2 movido pero TRACKS ETH/3V3/GND NO conectados aun.')
print('Run script 81 to add new tracks from new J2 to U2 W5500 + 3V3 + GND.')
