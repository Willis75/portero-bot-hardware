"""
Remove dangling track stubs left after deleting shorting vias.
"""
import sys
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"

board = pcbnew.LoadBoard(PCB)

# Dangling stubs to delete: (net_name, layer_name, end_x_mm, end_y_mm)
# Use the reported @position as one endpoint of the stub
STUBS = [
    ("RELAY1_GPIO", "F.Cu", 115.8400, 115.2100),
    ("BOOT",        "F.Cu", 141.6776, 129.9489),
    ("BOOT",        "B.Cu", 142.0546, 130.3259),
]

TOL = int(0.1 * 1e6)

layer_ids = {
    "F.Cu": pcbnew.F_Cu,
    "B.Cu": pcbnew.B_Cu,
}

deleted = []
for track in list(board.GetTracks()):
    if track.GetClass() != "PCB_TRACK":
        continue
    net  = track.GetNetname()
    lyr  = track.GetLayer()
    s    = track.GetStart()
    e    = track.GetEnd()
    for (tnet, tlyr, tx, ty) in STUBS:
        if net != tnet or lyr != layer_ids.get(tlyr):
            continue
        xi, yi = int(tx * 1e6), int(ty * 1e6)
        if (abs(s.x - xi) < TOL and abs(s.y - yi) < TOL) or \
           (abs(e.x - xi) < TOL and abs(e.y - yi) < TOL):
            board.Remove(track)
            deleted.append(f"  Removed stub [{tnet}] on {tlyr} @ ({tx}, {ty})")
            break

print(f"Deleted {len(deleted)} dangling stubs:")
for d in deleted:
    print(d)

board.Save(PCB)
print(f"Saved: {PCB}")
print("-> File -> Revert in KiCad, re-run DRC.")
