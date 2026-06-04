"""
Analyze B.Cu and F.Cu obstacles at key routing corridors.
Run AFTER 56a_clean.py.
"""
import sys
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"
board = pcbnew.LoadBoard(PCB)
F, B = pcbnew.F_Cu, pcbnew.B_Cu
TARGET_NETS = {"RELAY1_GPIO", "BOOT", "BST_5V"}

obstacles_b = []
obstacles_f = []

for t in board.GetTracks():
    net = t.GetNetname()
    if net in TARGET_NETS:
        continue
    cls = t.GetClass()
    if cls == "PCB_VIA":
        pos = t.GetPosition()
        x, y = pos.x / 1e6, pos.y / 1e6
        w = t.GetWidth() / 1e6
        obstacles_b.append(("VIA", x, y, net, w))
        obstacles_f.append(("VIA", x, y, net, w))
    elif cls == "PCB_TRACK":
        s, e = t.GetStart(), t.GetEnd()
        x1, y1 = s.x / 1e6, s.y / 1e6
        x2, y2 = e.x / 1e6, e.y / 1e6
        if t.GetLayer() == B:
            obstacles_b.append((x1, y1, x2, y2, net))
        elif t.GetLayer() == F:
            obstacles_f.append((x1, y1, x2, y2, net))

def hits(x1, y1, x2, y2, obs, clear=0.35):
    cx1, cx2 = min(x1, x2), max(x1, x2)
    cy1, cy2 = min(y1, y2), max(y1, y2)
    result = []
    for o in obs:
        if o[0] == "VIA":
            _, vx, vy, net, vw = o
            r = max(vw / 2, 0.3) + clear
            if cx1 == cx2:  # vertical
                if (cy1 - r) <= vy <= (cy2 + r) and abs(vx - cx1) < r:
                    result.append(f"VIA[{net}]@({vx:.2f},{vy:.2f})")
            else:  # horizontal
                if (cx1 - r) <= vx <= (cx2 + r) and abs(vy - cy1) < r:
                    result.append(f"VIA[{net}]@({vx:.2f},{vy:.2f})")
        else:
            ox1, oy1, ox2, oy2, net = o
            ocx1, ocx2 = min(ox1, ox2), max(ox1, ox2)
            ocy1, ocy2 = min(oy1, oy2), max(oy1, oy2)
            # Bounding box overlap with clearance
            if (cx1 - clear) < (ocx2 + clear) and (cx2 + clear) > (ocx1 - clear) and \
               (cy1 - clear) < (ocy2 + clear) and (cy2 + clear) > (ocy1 - clear):
                result.append(f"TRACK[{net}]({ox1:.2f},{oy1:.2f})-({ox2:.2f},{oy2:.2f})")
    return result

def check(label, x1, y1, x2, y2, obs):
    h = hits(x1, y1, x2, y2, obs)
    status = "CLEAR" if not h else f"{len(h)} HITS"
    print(f"  [{status}] {label}")
    for item in h:
        print(f"    {item}")

print("=== RELAY1_GPIO ===")
print("F.Cu escapes:")
check("R7 north (115.84,115.21→114.0)", 115.84, 115.21, 115.84, 114.0, obstacles_f)
check("R10 south (115.84,122.74→124.0)", 115.84, 122.74, 115.84, 124.0, obstacles_f)
check("F.Cu stub to U1pad8 (137.0,78.5→137.5,78.525)", 137.0, 78.5, 137.5, 78.525, obstacles_f)

print("B.Cu vias placement:")
check("Via@(115.84,114.0) zone", 115.84, 114.0, 115.84, 114.0, obstacles_b)
check("Via@(115.84,124.0) zone", 115.84, 124.0, 115.84, 124.0, obstacles_b)
check("Via@(137.0,78.5) zone", 137.0, 78.5, 137.0, 78.5, obstacles_b)

print("B.Cu horizontal options y=114:")
for y in [112.0, 113.0, 114.0, 115.0]:
    check(f"west y={y} (79→115.84)", 79.0, y, 115.84, y, obstacles_b)

print("B.Cu horizontal options y=124:")
for y in [124.0, 125.0, 126.0]:
    check(f"west y={y} (79→115.84)", 79.0, y, 115.84, y, obstacles_b)

print("B.Cu vertical left-edge options:")
for x in [79.0, 80.0, 81.0, 82.0]:
    check(f"north x={x} (y=126→78.5)", x, 78.5, x, 126.0, obstacles_b)

print("B.Cu east at y=78.5:")
check("east y=78.5 (79→137)", 79.0, 78.5, 137.0, 78.5, obstacles_b)
check("east y=77.0 (79→137)", 79.0, 77.0, 137.0, 77.0, obstacles_b)

print("\n=== BOOT ===")
print("F.Cu escapes:")
check("R2 north (113.48,125.25→124.0)", 113.48, 125.25, 113.48, 124.0, obstacles_f)
check("F.Cu stub to U1pad25 (155.5,86.145→155.0,86.145)", 155.5, 86.145, 155.0, 86.145, obstacles_f)

print("B.Cu via at (113.48,124.0):")
check("Via@(113.48,124.0)", 113.48, 124.0, 113.48, 124.0, obstacles_b)

print("B.Cu south options from R2 via:")
for x in [113.48, 111.0, 109.0, 107.0]:
    check(f"south x={x} (y=124→148)", x, 124.0, x, 148.0, obstacles_b)

print("B.Cu east options at y=148:")
for y in [146.0, 147.0, 148.0, 149.0]:
    check(f"east y={y} (x=109→135)", 109.0, y, 135.0, y, obstacles_b)

print("B.Cu north to SW1 at x=134.635:")
check("north x=134.635 (y=148→132)", 134.635, 148.0, 134.635, 132.0, obstacles_b)

print("B.Cu east from SW1 to right edge:")
for y in [130.0, 131.0, 132.0, 133.0]:
    check(f"east y={y} (x=134.635→166)", 134.635, y, 166.0, y, obstacles_b)

print("B.Cu right edge north:")
for x in [163.0, 165.0, 166.0]:
    check(f"north x={x} (y=132→86)", x, 86.0, x, 132.0, obstacles_b)

print("B.Cu west to U1pad25:")
for y in [86.145, 85.0, 84.0]:
    check(f"west y={y} (x=163→155.5)", 155.5, y, 163.0, y, obstacles_b)

print("\n=== BST_5V ===")
print("F.Cu escape from C22pad1:")
check("C22 north (98.575,130.57→129.0)", 98.575, 129.0, 98.575, 130.57, obstacles_f)

print("B.Cu via at (98.575,129.0):")
check("Via@(98.575,129.0)", 98.575, 129.0, 98.575, 129.0, obstacles_b)

print("B.Cu north options:")
for yt in [105.0, 107.0, 109.0]:
    for x in [98.575, 96.0, 94.0]:
        check(f"north x={x} (y=129→{yt})", x, yt, x, 129.0, obstacles_b)

print("B.Cu east options at various Y:")
for y in [103.0, 104.0, 105.0, 107.0, 109.0]:
    check(f"east y={y} (x=96→145)", 96.0, y, 145.0, y, obstacles_b)

print("B.Cu south to U4pad1 vicinity:")
for x in [143.0, 144.0, 145.0]:
    for yt in [103.0, 105.0, 107.0]:
        check(f"south x={x} from y={yt} to y=113", x, yt, x, 113.0, obstacles_b)

print("F.Cu stub to U4pad1:")
check("stub (144,112)→(145.55,112.605)", 144.0, 112.0, 145.55, 112.605, obstacles_f)
check("stub (143,112)→(145.55,112.605)", 143.0, 112.0, 145.55, 112.605, obstacles_f)

print("\n=== DONE ===")
