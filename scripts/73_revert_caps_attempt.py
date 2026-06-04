"""
73_revert_caps_attempt.py
Revierte script 72: elimina C18, C19, C24 + sus tracks + reset U3.4 to no net.
"""
import os, pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))
board = pcbnew.LoadBoard(PCB)

# Remove footprints C18, C19, C24
removed_fps = 0
for fp in list(board.GetFootprints()):
    if fp.GetReference() in ('C18', 'C19', 'C24'):
        board.Remove(fp)
        removed_fps += 1
        print(f'  removed footprint {fp.GetReference()}')

# Reset U3.4 to no net
for fp in board.GetFootprints():
    if fp.GetReference() == 'U3':
        for pad in fp.Pads():
            if pad.GetPadName() == '4':
                pad.SetNetCode(0)
                print('  U3.4 reset to no net')

# Remove tracks on CH340_V3 net (the new net we created)
removed_tracks = 0
for t in list(board.GetTracks()):
    n = t.GetNet()
    if n and n.GetNetname() == 'CH340_V3':
        board.Remove(t)
        removed_tracks += 1

# Remove tracks: the C18/C19 horizontal tracks we added (X=159 to ~150)
# Identification: F.Cu, X-start near 159 and net VIN_BUCK
# Also the GND tracks we added at C18/C19/C24 pad2
TARGETS = [
    # (start ~, end ~, layer name, net name)
    ((159.0, 116.0), (150.5, 118.0), 'F.Cu', 'VIN_BUCK'),
    ((159.0, 125.0), (150.5, 124.585), 'F.Cu', 'VIN_BUCK'),
    # GND tracks from new caps
    ((159.85, 116.0), (154.908, 120.473), 'F.Cu', 'GND'),
    ((159.85, 125.0), (163.949, 129.757), 'F.Cu', 'GND'),
    ((159.85, 134.0), (163.949, 129.757), 'F.Cu', 'GND'),
]
TOL = 50_000

def match(p, target):
    return abs(p[0] - target[0]*1e6) < TOL and abs(p[1] - target[1]*1e6) < TOL

for t in list(board.GetTracks()):
    if isinstance(t, pcbnew.PCB_VIA): continue
    s, e = t.GetStart(), t.GetEnd()
    layer = board.GetLayerName(t.GetLayer())
    net_name = t.GetNet().GetNetname() if t.GetNet() else ''
    for t_s, t_e, t_layer, t_net in TARGETS:
        if layer != t_layer or net_name != t_net: continue
        if (match((s.x, s.y), t_s) and match((e.x, e.y), t_e)) or \
           (match((s.x, s.y), t_e) and match((e.x, e.y), t_s)):
            board.Remove(t)
            removed_tracks += 1
            break

print(f'\nRemoved {removed_fps} footprints + {removed_tracks} tracks')

# Remove the CH340_V3 net we created (deletion is tricky in pcbnew; we can just leave it as orphan or skip)
# It will be cleaned up next time KiCad saves

pcbnew.SaveBoard(PCB, board)
print(f'Saved: {PCB}')
