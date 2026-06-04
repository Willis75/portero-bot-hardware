"""
61_import_ses.py
Imports the freerouting .ses session back into the cleaned .kicad_pcb.

Run: "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts/61_import_ses.py
"""
import os
import pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))
SES = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.ses"))

board = pcbnew.LoadBoard(PCB)
before = len(list(board.GetTracks()))
print(f"Tracks/vias before: {before}")

ok = pcbnew.ImportSpecctraSES(board, SES)
print(f"ImportSpecctraSES ok={ok}")

after = len(list(board.GetTracks()))
print(f"Tracks/vias after: {after} (added {after - before})")

pcbnew.SaveBoard(PCB, board)
print(f"Saved PCB: {PCB}")
