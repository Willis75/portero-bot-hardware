"""
65_fix_via_clearance.py
Resuelve la clearance violation entre via VIN_BUCK @ (152.0, 118.0) y track BOOT
en B.Cu @ (152.39, 125.4): mueve la via 0.3mm a la izquierda y arrastra los
endpoints de tracks que coinciden exactamente con la posicion vieja para que la
conexion electrica se preserve.
"""
import os, pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))

OLD_X, OLD_Y = 152_000_000, 118_000_000  # nm
NEW_X, NEW_Y = 151_700_000, 118_000_000  # nm — 0.3mm a la izquierda
TOL = 50_000  # 50 um match tolerance

board = pcbnew.LoadBoard(PCB)

def close(a, b, tol=TOL):
    return abs(a - b) <= tol

moved_vias = 0
moved_endpoints = 0
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        if close(p.x, OLD_X) and close(p.y, OLD_Y):
            t.SetPosition(pcbnew.VECTOR2I(NEW_X, NEW_Y))
            moved_vias += 1
            print(f"  via {p.x/1e6:.3f},{p.y/1e6:.3f} -> {NEW_X/1e6:.3f},{NEW_Y/1e6:.3f}")
    else:
        s, e = t.GetStart(), t.GetEnd()
        if close(s.x, OLD_X) and close(s.y, OLD_Y):
            t.SetStart(pcbnew.VECTOR2I(NEW_X, NEW_Y))
            moved_endpoints += 1
            print(f"  track start {s.x/1e6:.3f},{s.y/1e6:.3f} -> {NEW_X/1e6:.3f},{NEW_Y/1e6:.3f}")
        if close(e.x, OLD_X) and close(e.y, OLD_Y):
            t.SetEnd(pcbnew.VECTOR2I(NEW_X, NEW_Y))
            moved_endpoints += 1
            print(f"  track end {e.x/1e6:.3f},{e.y/1e6:.3f} -> {NEW_X/1e6:.3f},{NEW_Y/1e6:.3f}")

print(f"\nMoved {moved_vias} via(s), {moved_endpoints} track endpoint(s).")
pcbnew.SaveBoard(PCB, board)
print(f"Saved: {PCB}")
