"""
Analyze actual B.Cu and F.Cu obstacles at key routing corridors.
Also deletes zero-drill <no net> vias and cleans our 3 target nets.
Run before writing a new routing script.
"""
import sys
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"
board = pcbnew.LoadBoard(PCB)
F, B = pcbnew.F_Cu, pcbnew.B_Cu
TARGET_NETS = {"RELAY1_GPIO", "BOOT", "BST_5V"}

# ── 1. Delete zero-drill <no net> vias (missed by script 51)
removed_bad = 0
for t in list(board.GetTracks()):
    if t.GetClass() != "PCB_VIA":
        continue
    if t.GetNetname() != "":
        continue
    w = t.GetWidth()
    if w < int(0.4 * 1e6):
        board.Remove(t)
        removed_bad += 1
print(f"Removed {removed_bad} zero-drill <no net> vias")

# ── 2. Delete all target net tracks/vias
removed_net = 0
for t in list(board.GetTracks()):
    if t.GetNetname() in TARGET_NETS:
        board.Remove(t)
        removed_net += 1
print(f"Removed {removed_net} target net tracks/vias")

board.Save(PCB)
print("Saved clean board.")

# ── 3. Analyze obstacles (use same board object, already cleaned)

def mm(v): return int(v * 1e6)
TOL = int(0.5 * 1e6)  # 0.5mm clearance check radius

# Collect all obstacles (tracks + vias, excluding our nets)
obstacles_b = []  # (x1, y1, x2, y2, net) for tracks; ("VIA", x, y, net, w) for vias
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
        s = t.GetStart()
        e = t.GetEnd()
        x1, y1 = s.x / 1e6, s.y / 1e6
        x2, y2 = e.x / 1e6, e.y / 1e6
        if t.GetLayer() == B:
            obstacles_b.append((x1, y1, x2, y2, net))
        elif t.GetLayer() == F:
            obstacles_f.append((x1, y1, x2, y2, net))

# ── 4. Check specific proposed paths for collisions
# Clearance needed: 0.15mm track clearance + 0.125mm half-width = 0.275mm from track center

def segment_hits(x1, y1, x2, y2, obs, clear=0.35):
    """Check if proposed horizontal or vertical segment hits any obstacle."""
    hits = []
    cx1, cx2 = min(x1, x2), max(x1, x2)
    cy1, cy2 = min(y1, y2), max(y1, y2)
    for o in obs:
        if o[0] == "VIA":
            _, vx, vy, net, vw = o
            r = vw / 2 + clear
            # Check if via center is within expanded bounding box
            if (cx1 - r) <= vx <= (cx2 + r) and (cy1 - r) <= vy <= (cy2 + r):
                # More precise: distance from via center to segment
                if cx1 == cx2:  # vertical segment
                    if cy1 <= vy <= cy2 and abs(vx - cx1) < r:
                        hits.append(f"VIA [{net}] @({vx:.2f},{vy:.2f}) w={vw:.2f}")
                else:  # horizontal segment
                    if cx1 <= vx <= cx2 and abs(vy - cy1) < r:
                        hits.append(f"VIA [{net}] @({vx:.2f},{vy:.2f}) w={vw:.2f}")
        else:
            ox1, oy1, ox2, oy2, net = o
            ocx1, ocx2 = min(ox1, ox2), max(ox1, ox2)
            ocy1, ocy2 = min(oy1, oy2), max(oy1, oy2)
            # Expanded bounding boxes overlap?
            if (cx1 - clear) < (ocx2 + clear) and (cx2 + clear) > (ocx1 - clear) and \
               (cy1 - clear) < (ocy2 + clear) and (cy2 + clear) > (ocy1 - clear):
                hits.append(f"TRACK [{net}] ({ox1:.2f},{oy1:.2f})-({ox2:.2f},{oy2:.2f})")
    return hits

print("\n=== OBSTACLE ANALYSIS ===")
print("Checking proposed routing paths (0.35mm clearance radius)\n")

# RELAY1_GPIO paths to check
print("--- RELAY1_GPIO ---")
# R7pad1 north escape: (115.84, 115.21) → (115.84, 114.0)
h = segment_hits(115.84, 115.21, 115.84, 114.0, obstacles_f)
print(f"F.Cu R7 north escape (115.84 y=115.21→114.0): {len(h)} hits")
for x in h: print(f"  {x}")

# R7 via at (115.84, 114.0) — what's around it on B.Cu?
h = segment_hits(115.84, 114.0, 115.84, 114.0, obstacles_b)
print(f"B.Cu via at (115.84, 114.0) clearance: {len(h)} hits")
for x in h: print(f"  {x}")

# R7 escape west on B.Cu — scan from x=115.84 to x=79, y=114.0
h = segment_hits(79.0, 114.0, 115.84, 114.0, obstacles_b)
print(f"B.Cu west at y=114.0 (79→115.84): {len(h)} hits")
for x in h: print(f"  {x}")

# Try y=112.0 instead
h = segment_hits(79.0, 112.0, 115.84, 112.0, obstacles_b)
print(f"B.Cu west at y=112.0 (79→115.84): {len(h)} hits")
for x in h: print(f"  {x}")

# Try y=110.0
h = segment_hits(79.0, 110.0, 115.84, 110.0, obstacles_b)
print(f"B.Cu west at y=110.0 (79→115.84): {len(h)} hits")
for x in h: print(f"  {x}")

# Try x=79 north (114→78.5)
h = segment_hits(79.0, 78.5, 79.0, 114.0, obstacles_b)
print(f"B.Cu north on x=79 (y=114→78.5): {len(h)} hits")
for x in h: print(f"  {x}")

# Try x=82 north
h = segment_hits(82.0, 78.5, 82.0, 114.0, obstacles_b)
print(f"B.Cu north on x=82 (y=114→78.5): {len(h)} hits")
for x in h: print(f"  {x}")

# B.Cu east at y=78.5 to U1 (x=79→137)
h = segment_hits(79.0, 78.5, 137.0, 78.5, obstacles_b)
print(f"B.Cu east at y=78.5 (x=79→137): {len(h)} hits")
for x in h: print(f"  {x}")

# R10 south escape: (115.84, 122.74) → (115.84, 124.0)
h = segment_hits(115.84, 122.74, 115.84, 124.0, obstacles_f)
print(f"F.Cu R10 south escape (115.84 y=122.74→124.0): {len(h)} hits")
for x in h: print(f"  {x}")

# R10 via at (115.84, 124.0) B.Cu area
h = segment_hits(115.84, 124.0, 115.84, 124.0, obstacles_b)
print(f"B.Cu via at (115.84, 124.0) clearance: {len(h)} hits")
for x in h: print(f"  {x}")

# Can we connect R10 west at y=124.0?
h = segment_hits(79.0, 124.0, 115.84, 124.0, obstacles_b)
print(f"B.Cu west at y=124.0 (79→115.84): {len(h)} hits")
for x in h: print(f"  {x}")

# Try y=125.0
h = segment_hits(79.0, 125.0, 115.84, 125.0, obstacles_b)
print(f"B.Cu west at y=125.0 (79→115.84): {len(h)} hits")
for x in h: print(f"  {x}")

print("\n--- BOOT ---")
# R2pad2 escape: (113.48, 125.25) north
h = segment_hits(113.48, 124.0, 113.48, 125.25, obstacles_f)
print(f"F.Cu R2 north escape (y=125.25→124.0): {len(h)} hits")
for x in h: print(f"  {x}")

# Via at (113.48, 124.0) B.Cu
h = segment_hits(113.48, 124.0, 113.48, 124.0, obstacles_b)
print(f"B.Cu via at (113.48, 124.0): {len(h)} hits")
for x in h: print(f"  {x}")

# BOOT south on B.Cu to y=148
h = segment_hits(113.48, 124.0, 113.48, 148.0, obstacles_b)
print(f"B.Cu south x=113.48 (y=124→148): {len(h)} hits")
for x in h: print(f"  {x}")

# BOOT south on B.Cu at x=111 to y=148
h = segment_hits(111.0, 124.0, 111.0, 148.0, obstacles_b)
print(f"B.Cu south x=111 (y=124→148): {len(h)} hits")
for x in h: print(f"  {x}")

# BOOT east at y=148 to SW1 (x=134.635)
h = segment_hits(111.0, 148.0, 134.635, 148.0, obstacles_b)
print(f"B.Cu east y=148 (x=111→134.635): {len(h)} hits")
for x in h: print(f"  {x}")

# BOOT north x=134.635 to SW1 pad at y=132
h = segment_hits(134.635, 132.0, 134.635, 148.0, obstacles_b)
print(f"B.Cu north x=134.635 (y=148→132): {len(h)} hits")
for x in h: print(f"  {x}")

# Can we go east from SW1 to x=165 at y=132?
h = segment_hits(134.635, 132.0, 165.0, 132.0, obstacles_b)
print(f"B.Cu east y=132 (x=134.635→165): {len(h)} hits")
for x in h: print(f"  {x}")

# Right edge x=165 north to U1pad25 level
h = segment_hits(165.0, 86.145, 165.0, 132.0, obstacles_b)
print(f"B.Cu north x=165 (y=132→86.145): {len(h)} hits")
for x in h: print(f"  {x}")

# Try right edge at x=163
h = segment_hits(163.0, 86.145, 163.0, 132.0, obstacles_b)
print(f"B.Cu north x=163 (y=132→86.145): {len(h)} hits")
for x in h: print(f"  {x}")

# West from x=165 to U1pad25 at (155.0, 86.145)
h = segment_hits(155.0, 86.145, 165.0, 86.145, obstacles_b)
print(f"B.Cu west y=86.145 (x=165→155): {len(h)} hits")
for x in h: print(f"  {x}")

print("\n--- BST_5V ---")
# C22pad1 (98.575, 130.57) escape north
h = segment_hits(98.575, 129.0, 98.575, 130.57, obstacles_f)
print(f"F.Cu C22 north escape (y=130.57→129.0): {len(h)} hits")
for x in h: print(f"  {x}")

# Via at (98.575, 129.0)
h = segment_hits(98.575, 129.0, 98.575, 129.0, obstacles_b)
print(f"B.Cu via at (98.575, 129.0): {len(h)} hits")
for x in h: print(f"  {x}")

# Scan corridors at various Y levels on B.Cu for safe east runs
for y_test in [105.0, 107.0, 109.0, 111.0, 113.0]:
    h = segment_hits(98.575, y_test, 145.0, y_test, obstacles_b)
    print(f"B.Cu east y={y_test} (x=98.575→145): {len(h)} hits")
    for x in h: print(f"  {x}")

# North from via at y=129 to various Y levels
for y_test in [107.0, 109.0, 105.0]:
    h = segment_hits(98.575, y_test, 98.575, 129.0, obstacles_b)
    print(f"B.Cu north x=98.575 (y=129→{y_test}): {len(h)} hits")
    for x in h: print(f"  {x}")

# Try different X for BST_5V east run
for x_start in [95.0, 97.0, 96.0]:
    for y_test in [105.0, 107.0]:
        h = segment_hits(x_start, y_test, 145.0, y_test, obstacles_b)
        if len(h) == 0:
            print(f"CLEAR: B.Cu east x={x_start}→145 y={y_test}")

# U4pad1 approach from north
h = segment_hits(144.0, 107.0, 144.0, 113.0, obstacles_b)
print(f"B.Cu south x=144 (y=107→113): {len(h)} hits")
for x in h: print(f"  {x}")

h = segment_hits(145.0, 107.0, 145.0, 113.0, obstacles_b)
print(f"B.Cu south x=145 (y=107→113): {len(h)} hits")
for x in h: print(f"  {x}")

# F.Cu short stub from via to U4pad1
h = segment_hits(144.0, 112.0, 145.55, 112.605, obstacles_f)
print(f"F.Cu stub to U4pad1 (144,112)→(145.55,112.605): {len(h)} hits")
for x in h: print(f"  {x}")

print("\n=== DONE ===")
