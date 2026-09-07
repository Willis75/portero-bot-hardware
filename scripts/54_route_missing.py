r"""
Route the 5 missing connections via B.Cu bypasses.
Run: "C:\Program Files\KiCad\10.0\bin\python.exe" scripts/54_route_missing.py
"""
import sys
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"
board = pcbnew.LoadBoard(PCB)

W  = int(0.25 * 1e6)   # trace width 0.25mm
VD = int(0.60 * 1e6)   # via pad 0.6mm
VH = int(0.30 * 1e6)   # via drill 0.3mm

def mm(v): return int(v * 1e6)
def pt(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))

def track(net, layer, x1, y1, x2, y2):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pt(x1, y1)); t.SetEnd(pt(x2, y2))
    t.SetLayer(layer); t.SetWidth(W); t.SetNet(net)
    board.Add(t)

def via(net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pt(x, y))
    v.SetWidth(VD); v.SetDrill(VH)
    v.SetNet(net)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(v)

F, B = pcbnew.F_Cu, pcbnew.B_Cu

# ── 1. RELAY1_GPIO: R7pad1(115.84,115.21) → R10pad1(115.84,122.74) → U1pad8(137.5,78.525)
n = board.FindNet("RELAY1_GPIO")
# stub left from R7 → via1, then B.Cu to via2 near R10, stub to R10
track(n, F, 115.84, 115.21,  113.0, 115.21)
via(n, 113.0, 115.21)
track(n, B, 113.0, 115.21,   113.0, 122.74)
via(n, 113.0, 122.74)
track(n, F, 113.0, 122.74,   115.84, 122.74)
# B.Cu up from via1 to U1 area
track(n, B, 113.0, 115.21,   113.0,  78.0)
track(n, B, 113.0,  78.0,    137.0,  78.0)
via(n, 137.0, 78.0)
track(n, F, 137.0, 78.0,     137.5,  78.525)

# ── 2. BOOT: R2pad2(113.48,125.25) → SW1pad1(134.635,132.0) → U1pad25(155.0,86.145)
n = board.FindNet("BOOT")
# R2 → left via → B.Cu south → B.Cu east to SW1
track(n, F, 113.48, 125.25,  111.5, 125.25)
via(n, 111.5, 125.25)
track(n, B, 111.5, 125.25,   111.5, 133.5)
track(n, B, 111.5, 133.5,    134.635, 133.5)
track(n, B, 134.635, 133.5,  134.635, 132.0)   # up to SW1 PTH pad
# SW1 → north on B.Cu → east → via near U1pad25
track(n, B, 134.635, 132.0,  134.635,  86.145)
track(n, B, 134.635,  86.145, 154.5,   86.145)
via(n, 154.5, 86.145)
track(n, F, 154.5, 86.145,   155.0,   86.145)

# ── 3. BST_5V: C22pad1(98.575,130.57) → U4pad1(145.55,112.605)
n = board.FindNet("BST_5V")
track(n, F, 98.575, 130.57,  96.5, 130.57)
via(n, 96.5, 130.57)
track(n, B, 96.5, 130.57,    96.5, 111.0)
track(n, B, 96.5, 111.0,     144.5, 111.0)
via(n, 144.5, 111.0)
track(n, F, 144.5, 111.0,    145.55, 112.605)

board.Save(PCB)
print("Done — 3 nets routed (RELAY1_GPIO, BOOT, BST_5V)")
print("File -> Revert in KiCad, then re-run DRC.")
