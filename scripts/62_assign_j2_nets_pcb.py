"""
62_assign_j2_nets_pcb.py
Assigns nets to J2 (HR911105A RJ45) pads directly on the PCB via pcbnew API.
This bypasses regenerating the schematic — the .kicad_pcb is now the canonical
source of these connections. Idempotent.

Pad -> Net:
  1 -> ETH_TX_P
  2 -> ETH_TX_N
  3 -> ETH_RX_P
  4 -> 3V3
  5 -> 3V3
  6 -> ETH_RX_N
  7,8,9-12 -> no_connect (left unassigned)
  SH (x2) -> GND

Run: "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts/62_assign_j2_nets_pcb.py
"""
import os
import pcbnew

PCB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kicad", "portero-bot-v2.kicad_pcb"))

PAD_NET = {
    "1": "ETH_TX_P",
    "2": "ETH_TX_N",
    "3": "ETH_RX_P",
    "4": "3V3",
    "5": "3V3",
    "6": "ETH_RX_N",
    "SH": "GND",
}

board = pcbnew.LoadBoard(PCB)

netinfo_by_name = {}
for code, ni in board.GetNetInfo().NetsByName().items():
    netinfo_by_name[ni.GetNetname()] = ni

missing = [n for n in set(PAD_NET.values()) if n not in netinfo_by_name]
if missing:
    print(f"ERROR: nets not present in PCB: {missing}")
    print("Available nets:", sorted(netinfo_by_name.keys())[:20], "...")
    raise SystemExit(1)

assigned = 0
for fp in board.GetFootprints():
    if fp.GetReference() != "J2":
        continue
    print(f"J2 footprint: {fp.GetFPID().GetLibItemName()}")
    for pad in fp.Pads():
        num = pad.GetNumber()
        if num in PAD_NET:
            net = netinfo_by_name[PAD_NET[num]]
            pad.SetNet(net)
            print(f"  pad {num:4s} -> {PAD_NET[num]}")
            assigned += 1
        else:
            print(f"  pad {num:4s} -> (left no-connect)")
    break

print(f"\nAssigned {assigned} pads.")
pcbnew.SaveBoard(PCB, board)
print(f"Saved: {PCB}")
