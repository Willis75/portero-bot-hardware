"""
72_add_input_decoupling_caps.py
Agrega 3 capacitores faltantes:
- C18 100nF input cap U4 (VIN_BUCK input filtering, cerca U4)
- C19 100nF input cap U5 (VIN_BUCK input filtering, cerca U5)
- C24 100nF decoupling U3.4 CH340C V3 LDO output
Cada uno se clona del footprint C2 (existente 100nF/0603) para preservar settings.
"""
import os, pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))
TRACK_W = 250_000

# (ref, value, x_mm, y_mm, net_pad1, net_pad2)
NEW_CAPS = [
    ('C18', '100nF', 159.0, 116.0, 'VIN_BUCK', 'GND'),  # input cap U4
    ('C19', '100nF', 159.0, 125.0, 'VIN_BUCK', 'GND'),  # input cap U5
    ('C24', '100nF', 159.0, 134.0, 'CH340_V3', 'GND'),  # decoupling CH340 V3
]

# Tracks cortos a conectar:
# C18.1 (159, 116) -> U4.7 IN (150.5, 118): horizontal track ~8.5mm F.Cu
# C18.2 (159, 116) -> GND pour or nearest GND
# Similar para C19/C24
# Para que sea simple:
#   C.1 al pad target via F.Cu directo
#   C.2 a GND via pequeno track + se asume GND zone (si no hay, agregamos via)

board = pcbnew.LoadBoard(PCB)

# Find template footprint (C2, 100nF, 0603)
template = None
for fp in board.GetFootprints():
    if fp.GetReference() == 'C2':
        template = fp
        break
assert template, "Template C2 not found"
print(f'Template C2: {template.GetFPID().GetUniStringLibItemName()}')

# Helper: get net by name
def get_net(name):
    for ni in range(1, board.GetNetInfo().GetNetCount()):
        n = board.GetNetInfo().GetNetItem(ni)
        if n and n.GetNetname() == name:
            return n
    return None

vin_buck_net = get_net('VIN_BUCK')
gnd_net = get_net('GND')

# Create new net for CH340 V3 (no existe en el board)
ch340_v3_net = get_net('CH340_V3')
if ch340_v3_net is None:
    ch340_v3_net = pcbnew.NETINFO_ITEM(board, 'CH340_V3')
    board.Add(ch340_v3_net)
    print(f'Created net CH340_V3 (code={ch340_v3_net.GetNetCode()})')

# Spawn each cap
for ref, val, x, y, n1, n2 in NEW_CAPS:
    nm_x, nm_y = int(x*1e6), int(y*1e6)
    # Clone template
    new_fp = pcbnew.FOOTPRINT(template)
    new_fp.SetReference(ref)
    new_fp.SetValue(val)
    new_fp.SetPosition(pcbnew.VECTOR2I(nm_x, nm_y))
    # Set nets
    nets_to_set = {'1': n1, '2': n2}
    for pad in new_fp.Pads():
        pn = pad.GetPadName()
        if pn in nets_to_set:
            net_obj = vin_buck_net if nets_to_set[pn] == 'VIN_BUCK' else \
                      gnd_net if nets_to_set[pn] == 'GND' else \
                      ch340_v3_net
            pad.SetNet(net_obj)
    board.Add(new_fp)
    print(f'  + {ref} {val} @ ({x},{y}) pad1->{n1} pad2->{n2}')

# Tracks: conectar cada cap.1 al pad target
# C18.1 (159, 116) -> U4.7 (150.5, 118): track F.Cu
# C19.1 (159, 125) -> U5.7 (150.5, 124.585): track F.Cu
# C24.1 (159, 134) -> U3.4 (145.55, 133.71): track F.Cu

TRACKS = [
    # (start_x, start_y, end_x, end_y, layer, net)
    (159.0, 116.0, 150.5, 118.0, pcbnew.F_Cu, vin_buck_net),  # C18.1 -> U4.7
    (159.0, 125.0, 150.5, 124.585, pcbnew.F_Cu, vin_buck_net), # C19.1 -> U5.7
    (159.0, 134.0, 145.55, 133.71, pcbnew.F_Cu, ch340_v3_net), # C24.1 -> U3.4
]

# C24.1 needs to also be assigned to U3.4. Set U3.4 to CH340_V3 net
for fp in board.GetFootprints():
    if fp.GetReference() == 'U3':
        for pad in fp.Pads():
            if pad.GetPadName() == '4':
                pad.SetNet(ch340_v3_net)
                print(f'  U3.4 -> CH340_V3')

# Add tracks
for sx, sy, ex, ey, layer, net in TRACKS:
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(int(sx*1e6), int(sy*1e6)))
    t.SetEnd(pcbnew.VECTOR2I(int(ex*1e6), int(ey*1e6)))
    t.SetWidth(TRACK_W)
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)
    print(f'  + track {board.GetLayerName(layer)} ({sx:.2f},{sy:.2f})->({ex:.2f},{ey:.2f}) net={net.GetNetname()}')

# GND tracks: cap.2 (159, Y) to nearest GND
# Estrategia: short track + via if needed
# Para simpleza, agregamos via cerca de cada GND pad y track corto
# C18.2 (159, 116): nearest GND track? Let's find one
def find_nearest_gnd(pos_x, pos_y, max_d=15):
    best = None
    for t in board.GetTracks():
        n = t.GetNet()
        if not n or n.GetNetname() != 'GND': continue
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition()
            d = ((p.x/1e6-pos_x)**2+(p.y/1e6-pos_y)**2)**0.5
            if d < max_d and (best is None or d < best[0]):
                best = (d, p.x/1e6, p.y/1e6, 'both')
        else:
            layer = board.GetLayerName(t.GetLayer())
            for pt in (t.GetStart(), t.GetEnd()):
                d = ((pt.x/1e6-pos_x)**2+(pt.y/1e6-pos_y)**2)**0.5
                if d < max_d and (best is None or d < best[0]):
                    best = (d, pt.x/1e6, pt.y/1e6, layer)
    return best

for ref, val, x, y, n1, n2 in NEW_CAPS:
    # cap pad 2 GND position (1.6mm offset from center for 1210, but 0603 ~0.85mm)
    # 0603 footprint pads are at offset ~0.825mm from center along X
    pad2_x = x + 0.85
    pad2_y = y
    nearest = find_nearest_gnd(pad2_x, pad2_y)
    if nearest is None:
        print(f'  WARN: no GND track near {ref}.2 ({pad2_x},{pad2_y})')
        continue
    d, gx, gy, glayer = nearest
    print(f'  {ref}.2 ({pad2_x:.2f},{pad2_y:.2f}) -> GND nearest @ ({gx:.3f},{gy:.3f}) [{glayer}] dist={d:.2f}mm')
    # Track from pad2 to nearest GND point
    # Pad2 is F.Cu (SMD top), need to reach GND on F.Cu or via
    if glayer == 'F.Cu':
        # Direct track
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(int(pad2_x*1e6), int(pad2_y*1e6)))
        t.SetEnd(pcbnew.VECTOR2I(int(gx*1e6), int(gy*1e6)))
        t.SetWidth(TRACK_W)
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(gnd_net)
        board.Add(t)
    else:
        # Via at pad2 then B.Cu to gnd point
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pcbnew.VECTOR2I(int(pad2_x*1e6), int(pad2_y*1e6)))
        via.SetWidth(600_000)
        via.SetDrill(300_000)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNet(gnd_net)
        board.Add(via)
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(int(pad2_x*1e6), int(pad2_y*1e6)))
        t.SetEnd(pcbnew.VECTOR2I(int(gx*1e6), int(gy*1e6)))
        t.SetWidth(TRACK_W)
        t.SetLayer(pcbnew.B_Cu)
        t.SetNet(gnd_net)
        board.Add(t)

pcbnew.SaveBoard(PCB, board)
print(f'\nSaved: {PCB}')
