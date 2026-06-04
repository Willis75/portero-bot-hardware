"""
Final routing for RELAY1_GPIO, BOOT, BST_5V.
Strategy based on actual obstacle analysis (script 56b).

RELAY1_GPIO: escape vias at x=115.0 (away from RELAY3_GPIO B.Cu at x=116.21),
  go south on B.Cu to y=148, west to x=80, north to y=63 (above 5V B.Cu track),
  east to U1pad8 area, then south + via.

BOOT: R2 diagonal escape to avoid pad cluster, via, B.Cu south to y=148,
  east to SW1, continue east to x=163, north to y=86, via, F.Cu stub to U1pad25.

BST_5V: C22 north escape, via, B.Cu south to y=148, east to x=144,
  north to y=113, via, F.Cu stub to U4pad1.
"""
import sys
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"

# Snapshot tracks before modifying to avoid SWIG iterator corruption
board = pcbnew.LoadBoard(PCB)
all_tracks = list(board.GetTracks())

TARGET_NETS = {"RELAY1_GPIO", "BOOT", "BST_5V"}
for t in all_tracks:
    if t.GetNetname() in TARGET_NETS:
        board.Remove(t)

W  = int(0.25 * 1e6)
VD = int(0.60 * 1e6)
VH = int(0.30 * 1e6)
F, B = pcbnew.F_Cu, pcbnew.B_Cu

def mm(v): return int(v * 1e6)
def pt(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

def trk(net, layer, x1, y1, x2, y2):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pt(x1, y1)); t.SetEnd(pt(x2, y2))
    t.SetLayer(layer); t.SetWidth(W); t.SetNet(net)
    board.Add(t)

def via(net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pt(x, y))
    v.SetWidth(VD); v.SetDrill(VH); v.SetNet(net)
    v.SetLayerPair(F, B)
    board.Add(v)

# ── RELAY1_GPIO ──────────────────────────────────────────────────────────────
# Pads: R7pad1(115.84,115.21) R10pad1(115.84,122.74) U1pad8(137.5,78.525)
#
# Via placement at x=115.0 keeps 0.71mm from RELAY3_GPIO B.Cu (x=116.21)
# y=148 bottom strip is clear; x=80 left edge is clear north to y=78.5
# East run at y=63 is above the 5V B.Cu vertical (x=101.35, y=65→81.95)
#
n = board.FindNet("RELAY1_GPIO")

# R7: escape north → west stub → via
trk(n, F, 115.84, 115.21, 115.84, 114.5)   # north in inter-row gap
trk(n, F, 115.84, 114.5,  115.0,  114.5)   # west stub (avoids RELAY3_GPIO @116.21)
via(n, 115.0, 114.5)

# R10: escape south → west stub → via
trk(n, F, 115.84, 122.74, 115.84, 124.0)   # south in inter-row gap
trk(n, F, 115.84, 124.0,  115.0,  124.0)   # west stub
via(n, 115.0, 124.0)

# B.Cu south trunk: R7 via → R10 junction → bottom strip
trk(n, B, 115.0, 114.5,  115.0, 148.0)     # south (passes through R10 via at 124.0)

# Bottom strip west to left edge
trk(n, B, 115.0, 148.0,  80.0, 148.0)

# Left edge north, above 5V track (ends at y=65, our east run at y=63)
trk(n, B,  80.0, 148.0,  80.0,  63.0)

# East above 5V track, then south to U1pad8 level
trk(n, B,  80.0,  63.0, 137.0,  63.0)
trk(n, B, 137.0,  63.0, 137.0,  78.5)
via(n, 137.0, 78.5)
trk(n, F, 137.0,  78.5, 137.5,  78.525)    # F.Cu stub to U1pad8

# ── BOOT ─────────────────────────────────────────────────────────────────────
# Pads: R2pad2(113.48,125.25) SW1pad1(134.635,132.0) U1pad25(155.0,86.145)
#
# R2 is hemmed in:
#   East at y=125.25 → R11pad1[RELAY1_GPIO] at x=115.84 (short!)
#   West at y=125.25 → C6pad2[GND] at x=109.42 (short if extended)
#   North at x=113.48 → R1pad2[EN] at y=122.74 (short!)
#   South at x=113.48 → R3pad2[GND] at y=127.76 (short!)
#
# Escape: diagonal NE then south-east to avoid all nearby pads
# Go to (116.5, 127.5) via 45° diagonal, then south-east to via at (117.0, 133.0)
# Then B.Cu to SW1, east to bottom strip, east to right edge, north to U1pad25
#
n = board.FindNet("BOOT")

# R2 diagonal escape — skirt between pad clusters
# Step 1: small diagonal NE (away from R3pad2 at 113.48,127.76 and R11pad1 at 115.84,125.25)
trk(n, F, 113.48, 125.25, 116.5, 128.25)   # 45° diagonal SE to gap area
# Step 2: via in the gap
via(n, 116.5, 128.25)

# B.Cu south from via to bottom strip (staying at x=116.5, avoiding ETH_XO at x=113.45)
trk(n, B, 116.5, 128.25, 116.5, 148.0)

# Bottom strip east to SW1 column
trk(n, B, 116.5, 148.0, 134.635, 148.0)

# North to SW1 PTH pad
trk(n, B, 134.635, 148.0, 134.635, 132.0)

# Continue east to right edge on bottom strip (avoids dense B.Cu in y=130-145)
trk(n, B, 134.635, 148.0, 163.0, 148.0)

# Right edge north to U1pad25 level
trk(n, B, 163.0, 148.0, 163.0,  86.145)

# West to just right of UART0_RX (x=155.74); stop at x=156.5
trk(n, B, 163.0,  86.145, 156.5, 86.145)
via(n, 156.5, 86.145)

# F.Cu west stub to U1pad25 (UART0_RX is on B.Cu only, no F.Cu conflict)
trk(n, F, 156.5, 86.145, 155.0, 86.145)

# ── BST_5V ───────────────────────────────────────────────────────────────────
# Pads: C22pad1(98.575,130.57) U4pad1(145.55,112.605)
#
# C22 escape north: LED_3V3_PWR track near y=128.66 on F.Cu
# Go north on F.Cu to y=129.5 (clear), then west to x=97 (avoids 5V B.Cu via),
# via at (97.0, 129.5), B.Cu south to y=148, east to x=145, north to y=113,
# via, F.Cu stub to U4pad1.
#
n = board.FindNet("BST_5V")

# F.Cu escape: slightly west to avoid LED_3V3_PWR track at y≈128.66
trk(n, F, 98.575, 130.57, 97.0, 130.57)   # west stub
trk(n, F, 97.0, 130.57,   97.0, 129.5)    # north escape (clear of LED_3V3_PWR)
via(n, 97.0, 129.5)

# B.Cu south to bottom strip
trk(n, B, 97.0, 129.5, 97.0, 148.0)

# East to U4 column
trk(n, B, 97.0, 148.0, 145.0, 148.0)

# North to U4pad1 level (B.Cu south at x=144/145 is CLEAR per analysis)
trk(n, B, 145.0, 148.0, 145.0, 113.5)
via(n, 145.0, 113.5)

# F.Cu stub to U4pad1 (at 145.55, 112.605) — approach from south
trk(n, F, 145.0, 113.5, 145.55, 112.605)

board.Save(PCB)
print("Saved. File -> Revert in KiCad, then run DRC.")
