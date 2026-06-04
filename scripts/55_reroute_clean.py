"""
Remove bad routes from script 54, then add cleaner routes avoiding known B.Cu conflicts.
"""
import sys
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"
board = pcbnew.LoadBoard(PCB)

W  = int(0.25 * 1e6)
VD = int(0.60 * 1e6)
VH = int(0.30 * 1e6)

def mm(v): return int(v * 1e6)
def pt(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

def add_track(net, layer, x1, y1, x2, y2):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pt(x1, y1)); t.SetEnd(pt(x2, y2))
    t.SetLayer(layer); t.SetWidth(W); t.SetNet(net)
    board.Add(t); return t

def add_via(net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pt(x, y))
    v.SetWidth(VD); v.SetDrill(VH); v.SetNet(net)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(v); return v

F, B = pcbnew.F_Cu, pcbnew.B_Cu
TOL = int(0.5 * 1e6)

# ── 1. Delete all tracks/vias from the 3 target nets (clean slate)
TARGET_NETS = {"RELAY1_GPIO", "BOOT", "BST_5V"}
removed = 0
for t in list(board.GetTracks()):
    if t.GetNetname() in TARGET_NETS:
        board.Remove(t)
        removed += 1
print(f"Removed {removed} existing tracks/vias for target nets")

# ── 2. Re-route using safe paths
# Strategy:
#   - Escape F.Cu to B.Cu via short stubs in inter-row gaps
#   - Route B.Cu along LEFT EDGE (x=79) and BOTTOM STRIP (y=148) and RIGHT EDGE (x=163)
#   - These perimeter areas are clear of freerouting traces

# ── NET: RELAY1_GPIO
# R7pad1(115.84,115.21) — escape NORTH to via at y=114.0 (inter-row gap y=113.2-114.71)
# R10pad1(115.84,122.74) — escape SOUTH to via at y=123.5 (inter-row gap y=123.24-124.75)
# U1pad8(137.5,78.525)
n = board.FindNet("RELAY1_GPIO")

# R7 escape north -> via -> B.Cu west -> left edge trunk
add_track(n, F, 115.84, 115.21, 115.84, 114.0)
add_via(n, 115.84, 114.0)
add_track(n, B, 115.84, 114.0, 79.0, 114.0)   # west on B.Cu

# R10 escape south -> via -> B.Cu west -> join left edge
add_track(n, F, 115.84, 122.74, 115.84, 123.5)
add_via(n, 115.84, 123.5)
add_track(n, B, 115.84, 123.5, 79.0, 123.5)   # west on B.Cu
add_track(n, B, 79.0, 123.5, 79.0, 114.0)     # north along left edge to R7 junction

# Left edge trunk north to U1 level, then east
add_track(n, B, 79.0, 114.0, 79.0, 78.5)      # north along left edge
add_track(n, B, 79.0, 78.5,  137.0, 78.5)     # east to U1 pad8 column
add_via(n, 137.0, 78.5)
add_track(n, F, 137.0, 78.5, 137.5, 78.525)   # short F.Cu stub to U1pad8

# ── NET: BOOT
# R2pad2(113.48,125.25) — escape NORTH to via at y=124.0 (clear zone)
# SW1pad1(134.635,132.0) — PTH
# U1pad25(155.0,86.145)
n = board.FindNet("BOOT")

# R2 escape north to via
add_track(n, F, 113.48, 125.25, 113.48, 124.0)
add_via(n, 113.48, 124.0)
# B.Cu south to y=140 (below all passives), east to SW1, north to SW1pad1
add_track(n, B, 113.48, 124.0, 113.48, 140.0)
add_track(n, B, 113.48, 140.0, 134.635, 140.0)
add_track(n, B, 134.635, 140.0, 134.635, 132.0)  # up to SW1 PTH

# SW1 -> east along y=140 -> right edge -> north -> U1pad25
add_track(n, B, 134.635, 132.0, 134.635, 140.0)  # already there (SW1 branch)
add_track(n, B, 134.635, 140.0, 163.0, 140.0)    # east to right edge
add_track(n, B, 163.0, 140.0,  163.0, 86.145)    # north along right edge
add_track(n, B, 163.0, 86.145, 155.5, 86.145)    # west to near U1pad25
add_via(n, 155.5, 86.145)
add_track(n, F, 155.5, 86.145, 155.0, 86.145)    # short F.Cu to U1pad25

# ── NET: BST_5V
# C22pad1(98.575,130.57) -> U4pad1(145.55,112.605)
# Escape NORTH to y=129 (inter-row gap), route north to y=107 (above SW_BUCK via at y=111),
# east to U4 column, south to U4pad1
n = board.FindNet("BST_5V")

add_track(n, F, 98.575, 130.57, 98.575, 129.0)   # north escape
add_via(n, 98.575, 129.0)
add_track(n, B, 98.575, 129.0, 98.575, 107.0)    # north to y=107 (above SW_BUCK via)
add_track(n, B, 98.575, 107.0, 144.0, 107.0)     # east to U4 area
add_track(n, B, 144.0, 107.0, 144.0, 112.0)      # south to U4pad1 level
add_via(n, 144.0, 112.0)
add_track(n, F, 144.0, 112.0, 145.55, 112.605)   # short F.Cu to U4pad1

board.Save(PCB)
print("Saved. File -> Revert in KiCad, then re-run DRC.")
