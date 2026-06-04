"""
60_clean_and_export_dsn.py
Wipes ALL tracks + vias from the PCB (keeps footprints, zones, edge cuts,
silkscreen, pads) and exports a fresh Specctra .dsn for freerouting.

The clearance rule in portero-bot-v2.kicad_dru is already 0.10mm, so the
exported DSN will carry that constraint to freerouting.

Run: "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts/60_clean_and_export_dsn.py
"""
import os
import pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))
DSN = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.dsn"))

board = pcbnew.LoadBoard(PCB)

tracks = list(board.GetTracks())
print(f"Before: {len(tracks)} tracks+vias")

track_count = 0
via_count = 0
for t in tracks:
    if isinstance(t, pcbnew.PCB_VIA):
        via_count += 1
    else:
        track_count += 1
    board.Remove(t)

print(f"Removed: {track_count} tracks, {via_count} vias")
print(f"After: {len(list(board.GetTracks()))} tracks+vias")

pcbnew.SaveBoard(PCB, board)
print(f"Saved cleaned PCB: {PCB}")

ok = pcbnew.ExportSpecctraDSN(board, DSN)
print(f"ExportSpecctraDSN -> {DSN} (ok={ok})")
assert os.path.exists(DSN), "DSN was not written"
print(f"DSN size: {os.path.getsize(DSN)} bytes")
