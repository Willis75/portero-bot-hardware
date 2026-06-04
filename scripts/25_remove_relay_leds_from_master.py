"""
25_remove_relay_leds_from_master.py
Removes LED2/LED3/LED4 + R10/R11/R12 from data/master.json + data/nets_clean.json
so that re-running 30_gen_schematic.py never regenerates them.

Matches the PCB state (commit 78a1970 onward).
- LED2/3/4 + R10/11/12: gone (relay indicators not needed per client).
- RELAY1_LED / RELAY2_LED / RELAY3_LED nets: deleted entirely.
- RELAY1_GPIO / RELAY2_GPIO / RELAY3_GPIO: drop R10.P1 / R11.P1 / R12.P1.
- GND: drop LED2.K / LED3.K / LED4.K.

Run before 30_gen_schematic.py. Idempotent.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(ROOT, "data", "master.json")
NETS = os.path.join(ROOT, "data", "nets_clean.json")

REMOVE_REFS = {"LED2", "LED3", "LED4", "R10", "R11", "R12"}
REMOVE_NETS = {"RELAY1_LED", "RELAY2_LED", "RELAY3_LED"}

master = json.load(open(MASTER, encoding="utf-8"))
nets = json.load(open(NETS, encoding="utf-8"))

before_m = len(master)
master = [c for c in master if c.get("ref") not in REMOVE_REFS]
print(f"master.json: {before_m} -> {len(master)} components (removed {before_m - len(master)})")

before_n = len(nets)
new_nets = []
for n in nets:
    if n["name"] in REMOVE_NETS:
        continue
    pins = [p for p in n["pins"] if p.rsplit(".", 1)[0] not in REMOVE_REFS]
    if not pins:
        continue
    n["pins"] = pins
    new_nets.append(n)

print(f"nets_clean.json: {before_n} -> {len(new_nets)} nets (removed {before_n - len(new_nets)})")

with open(MASTER, "w", encoding="utf-8") as f:
    json.dump(master, f, indent=2, ensure_ascii=False)
with open(NETS, "w", encoding="utf-8") as f:
    json.dump(new_nets, f, indent=2, ensure_ascii=False)

print(f"Saved {MASTER}")
print(f"Saved {NETS}")
