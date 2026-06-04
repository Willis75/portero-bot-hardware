"""
26_fix_j2_pinmap.py
Replaces the anonymous "J2.~" pin references in data/nets_clean.json with
explicit pin numbers per the HR911105A datasheet (verified against KiCad
Connector.kicad_sym symbol "RJ45_Hanrun_HR911105A_Horizontal").

Mapping (MAC side of integrated transformer):
  Pin 1 = TD+  -> ETH_TX_P
  Pin 2 = TD-  -> ETH_TX_N
  Pin 3 = RD+  -> ETH_RX_P
  Pin 4 = TCT  -> 3V3 (transmit center tap)
  Pin 5 = RCT  -> 3V3 (receive center tap)
  Pin 6 = RD-  -> ETH_RX_N
  Pins 7,8,9-12 left NC (LEDs ethernet unused).
  SH pads -> GND (already mapped via J2.SHIELD).

Run after 25_remove_relay_leds_from_master.py and before 30_gen_schematic.py.
Idempotent.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NETS = os.path.join(ROOT, "data", "nets_clean.json")

J2_PIN_BY_NET = {
    "ETH_TX_P": "1",
    "ETH_TX_N": "2",
    "ETH_RX_P": "3",
    "ETH_RX_N": "6",
}

J2_3V3_PINS = ["4", "5"]

nets = json.load(open(NETS, encoding="utf-8"))

updated = []
for n in nets:
    name = n["name"]
    new_pins = []
    changed = False
    for p in n["pins"]:
        if p == "J2.~":
            if name in J2_PIN_BY_NET:
                new_pins.append(f"J2.{J2_PIN_BY_NET[name]}")
                changed = True
                continue
            if name == "3V3":
                continue
            new_pins.append(p)
        else:
            new_pins.append(p)
    if name == "3V3" and any(p.startswith("J2.") for p in n["pins"]):
        if "J2.4" not in new_pins:
            new_pins.append("J2.4")
            changed = True
        if "J2.5" not in new_pins:
            new_pins.append("J2.5")
            changed = True
        new_pins = [p for p in new_pins if p != "J2.~"]
    n["pins"] = new_pins
    if changed:
        updated.append((name, new_pins))

with open(NETS, "w", encoding="utf-8") as f:
    json.dump(nets, f, indent=2, ensure_ascii=False)

print(f"Updated nets: {len(updated)}")
for name, pins in updated:
    j2_pins = [p for p in pins if p.startswith("J2.")]
    print(f"  {name}: J2 pins = {j2_pins}")

remaining = sum(1 for n in nets for p in n["pins"] if p == "J2.~")
print(f"Remaining J2.~ entries: {remaining}")
