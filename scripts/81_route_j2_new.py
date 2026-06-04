"""
81_route_j2_new.py
Conecta los pads nuevos del J2 (movido al borde derecho) con tracks F.Cu cortos
hacia los track endpoints existentes de cada net.
"""
import os, pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))
TRACK_W = 250_000

board = pcbnew.LoadBoard(PCB)

def get_net(name):
    for ni in range(1, board.GetNetInfo().GetNetCount()):
        n = board.GetNetInfo().GetNetItem(ni)
        if n and n.GetNetname() == name: return n
    return None

# Routing tasks: (start_x, start_y, end_x, end_y, layer, net_name)
# All tracks F.Cu from new J2 pads to existing endpoint of each net
ROUTES = [
    # J2.1 ETH_TX_P (174.40, 110.00) -> (146.887, 95.540) B.Cu  — use F.Cu first then via, or direct
    ('ETH_TX_P', (174.40, 110.00), (146.887, 95.540), pcbnew.B_Cu),
    ('ETH_TX_N', (171.86, 108.74), (150.393, 93.000), pcbnew.F_Cu),
    ('ETH_RX_P', (174.40, 107.46), (159.980, 94.545), pcbnew.F_Cu),
    ('ETH_RX_N', (171.86, 103.66), (164.775, 95.664), pcbnew.F_Cu),
    # J2.4 (3V3) - 2 routes (to make pads 4 and 5 connected)
    ('3V3', (171.86, 106.20), (163.515, 107.500), pcbnew.B_Cu),
    # J2.5 (3V3) - connect to J2.4 with short F.Cu track
    ('3V3', (174.40, 104.92), (171.86, 106.20), pcbnew.F_Cu),
    # J2.SH (GND) - 2 shield pads need to connect to GND
    # J2 SH at (177.71, 97.81) and (177.71, 113.30)
    # Existing GND track endpoint at (155.13, 98.85)
    ('GND', (177.71, 97.81), (155.13, 98.85), pcbnew.B_Cu),
    ('GND', (177.71, 113.30), (177.71, 97.81), pcbnew.F_Cu),
]

added = 0
for net_name, start, end, layer in ROUTES:
    net = get_net(net_name)
    if not net:
        print(f'  ERROR: net {net_name} not found')
        continue
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(int(start[0]*1e6), int(start[1]*1e6)))
    t.SetEnd(pcbnew.VECTOR2I(int(end[0]*1e6), int(end[1]*1e6)))
    t.SetWidth(TRACK_W)
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)
    layer_name = board.GetLayerName(layer)
    print(f'  + {layer_name} {net_name}: ({start[0]:.2f},{start[1]:.2f})->({end[0]:.2f},{end[1]:.2f})')
    added += 1

print(f'\nAdded {added} tracks')
pcbnew.SaveBoard(PCB, board)
print(f'Saved: {PCB}')
