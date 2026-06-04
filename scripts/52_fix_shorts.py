"""
Fix shorts caused by overlapping vias after via-size correction.
Deletes the shorting via from each pair (the one listed second in DRC).
Run: "C:\Program Files\KiCad\10.0\bin\python.exe" scripts/52_fix_shorts.py
"""
import sys
sys.path.insert(0, r"C:\Program Files\KiCad\10.0\bin")
import pcbnew

PCB = r"C:\Users\wumni\Documents\Proyectos\portero-bot-hardware\kicad\portero-bot-v2.kicad_pcb"

board = pcbnew.LoadBoard(PCB)

# Vias to delete: (net_name, x_mm, y_mm) with 0.05mm tolerance
DELETE_VIAS = [
    ("BOOT",         142.0546, 130.3259),
    ("RELAY1_GPIO",  115.2341, 115.2100),
]

TOL = int(0.05 * 1e6)

deleted = []
for track in list(board.GetTracks()):
    if track.GetClass() != "PCB_VIA":
        continue
    net = track.GetNetname()
    pos = track.GetPosition()
    for (tnet, tx, ty) in DELETE_VIAS:
        if (net == tnet
                and abs(pos.x - int(tx * 1e6)) < TOL
                and abs(pos.y - int(ty * 1e6)) < TOL):
            board.Remove(track)
            deleted.append(f"  Removed via [{tnet}] @ ({tx}, {ty})")
            break

if deleted:
    print(f"Deleted {len(deleted)} shorting vias:")
    for d in deleted:
        print(d)
else:
    print("No matching vias found - check coordinates.")

board.Save(PCB)
print(f"Saved: {PCB}")
print("-> File -> Revert in KiCad, then re-run DRC.")
