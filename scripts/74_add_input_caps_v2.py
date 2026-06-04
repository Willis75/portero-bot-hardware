"""
74_add_input_caps_v2.py
Coloca C18 y C19 (100nF input caps de bucks) en espacio libre entre Q2/Q3 y U4/U5 IN pads.

Layout:
  Q2 (Q3) [bbox right=140.17]  C18 (C19)  U4.2 (U5.2) [@145.55]
                                  ^
                            (X=143, Y=118 o 124.5)
Cap rotado 180° para que pad 1 (VIN_BUCK) este del lado U4/U5.
"""
import os, pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))
TRACK_W = 250_000

# (ref, value, center_x_mm, center_y_mm, rotation_deg, pad1_net, pad2_net)
NEW_CAPS = [
    ('C18', '100nF', 143.0, 118.000, 180.0, 'VIN_BUCK', 'GND'),  # input cap U4
    ('C19', '100nF', 143.0, 124.585, 180.0, 'VIN_BUCK', 'GND'),  # input cap U5
]

board = pcbnew.LoadBoard(PCB)

# Template footprint (C2 0603 100nF)
template = None
for fp in board.GetFootprints():
    if fp.GetReference() == 'C2':
        template = fp
        break
assert template

# Net helpers
def get_net(name):
    for ni in range(1, board.GetNetInfo().GetNetCount()):
        n = board.GetNetInfo().GetNetItem(ni)
        if n and n.GetNetname() == name:
            return n
    return None

vin_buck = get_net('VIN_BUCK')
gnd = get_net('GND')

# Place caps
for ref, val, cx, cy, rot, n1, n2 in NEW_CAPS:
    nm_x, nm_y = int(cx*1e6), int(cy*1e6)
    new_fp = pcbnew.FOOTPRINT(template)
    new_fp.SetReference(ref)
    new_fp.SetValue(val)
    new_fp.SetPosition(pcbnew.VECTOR2I(nm_x, nm_y))
    new_fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    for pad in new_fp.Pads():
        pn = pad.GetPadName()
        if pn == '1':
            pad.SetNet(vin_buck)
        elif pn == '2':
            pad.SetNet(gnd)
    board.Add(new_fp)
    # After SetOrientation, pad positions are updated
    # Get actual pad positions
    pad_positions = {}
    for pad in new_fp.Pads():
        p = pad.GetPosition()
        pad_positions[pad.GetPadName()] = (p.x, p.y)
    print(f'  + {ref} 100nF @ ({cx},{cy}) rot={rot}')
    for pn, (px, py) in pad_positions.items():
        print(f'    pad {pn} -> ({px/1e6:.3f},{py/1e6:.3f})')

# Tracks: connect cap pad 1 (VIN_BUCK, right side after 180 rot) to U4.2/U5.2
TRACKS = [
    # C18 pad 1 should be at (143.825, 118) after 180 rotation
    # U4.2 is at (145.55, 118.0)
    ('C18.1 -> U4.2', 143.825, 118.000, 145.55, 118.0, pcbnew.F_Cu, vin_buck),
    # C18 pad 2 GND at (142.175, 118) -> Q2.1 (E=GND)
    # Q2.1 position needs calc but let's go via to B.Cu where GND tracks are
    # C19 pad 1 at (143.825, 124.585)
    ('C19.1 -> U5.2', 143.825, 124.585, 145.55, 124.585, pcbnew.F_Cu, vin_buck),
]

for label, sx, sy, ex, ey, layer, net in TRACKS:
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(int(sx*1e6), int(sy*1e6)))
    t.SetEnd(pcbnew.VECTOR2I(int(ex*1e6), int(ey*1e6)))
    t.SetWidth(TRACK_W)
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)
    print(f'  + track {label}: {board.GetLayerName(layer)} ({sx},{sy})->({ex},{ey})')

# GND connection: find nearest GND pad/track to (142.175, 118) and (142.175, 124.585)
# Q1, Q2, Q3 emitters are GND. Let's find them.
def find_q_gnd(center_y):
    # Q transistors have pad 1=E=GND. We need to find which Q is at our row.
    # Q1 @ 114.7, Q2 @ 120.49, Q3 @ 126.28
    closest = None
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref not in ('Q1','Q2','Q3'): continue
        for pad in fp.Pads():
            if pad.GetPadName() == '1':  # Emitter = GND in 2N2222A
                p = pad.GetPosition()
                d = abs(p.y/1e6 - center_y)
                if closest is None or d < closest[0]:
                    closest = (d, p.x/1e6, p.y/1e6, ref)
    return closest

for ref, val, cx, cy, rot, n1, n2 in NEW_CAPS:
    # GND pad is at (cx - 0.825, cy) after 180 rotation (left side)
    pad2_x = cx - 0.825
    pad2_y = cy
    # Find nearest GND Q transistor emitter
    closest = find_q_gnd(cy)
    if closest:
        d, qx, qy, qref = closest
        # Track from cap pad 2 to Q emitter
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(int(pad2_x*1e6), int(pad2_y*1e6)))
        t.SetEnd(pcbnew.VECTOR2I(int(qx*1e6), int(qy*1e6)))
        t.SetWidth(TRACK_W)
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(gnd)
        board.Add(t)
        print(f'  + GND track {ref}.2 ({pad2_x:.2f},{pad2_y:.2f}) -> {qref}.1 ({qx:.2f},{qy:.2f})')

pcbnew.SaveBoard(PCB, board)
print(f'\nSaved: {PCB}')
