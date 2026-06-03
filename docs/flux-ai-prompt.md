# Flux.ai Prompt — Portero Bot PCB V2

Copia y pega esto en Flux.ai al crear un nuevo proyecto.

---

Design a 2-layer PCB (100×80mm) for a gate controller system with the following specs:

## Overview
IoT gate controller with Ethernet connectivity. Controls 3 relay channels (dry contact / button simulation for gate openers). Programmed via USB initially, then OTA over Ethernet.

## Main Components

- **MCU:** ESP32-WROOM-32E module
- **Ethernet:** W5500 (LQFP-48) via SPI + HanRun HR911105A RJ45 magjack (integrated magnetics)
- **USB-Serial:** CH340C (SOP-16) on MicroUSB connector
- **Power:** Barrel jack DC 9-24V input → MP2307DN buck converter (5V/3A) → AMS1117-3.3 LDO (3.3V)
- **Relays:** 3× SRD-05VDC-SL-C (5V coil), each driven by PC817 optocoupler + 2N2222A transistor + 1N4148 flyback diode
- **Protection:** SS34 Schottky diode + SMAJ24CA TVS on barrel input + 1A PTC resettable fuse

## Pin Assignments (ESP32)

SPI to W5500:
- GPIO18 → SCLK
- GPIO23 → MOSI
- GPIO19 → MISO
- GPIO5  → SCSn (CS)
- GPIO26 → INTn
- GPIO27 → RSTn

Relay channels:
- GPIO32 → Relay 1 (via optocoupler PC817)
- GPIO33 → Relay 2 (via optocoupler PC817)
- GPIO25 → Relay 3 (via optocoupler PC817)

UART (USB-Serial CH340C):
- GPIO1 (TXD0) → CH340C RXD
- GPIO3 (RXD0) → CH340C TXD

Control:
- EN pin → 10kΩ pull-up to 3.3V + reset button to GND
- GPIO0  → 10kΩ pull-up to 3.3V + boot button to GND

## Power Architecture

```
Barrel Jack (9-24V) → SS34 → SMAJ24CA TVS → PTC 1A fuse
  → MP2307DN buck (22µH inductor, 2×100µF out) → 5V rail
    → AMS1117-3.3 LDO → 3.3V rail

5V powers: relay coils (K1/K2/K3), CH340C VCC, PC817 collector side
3.3V powers: ESP32-WROOM-32E, W5500, logic
```

## Relay Circuit (repeat ×3, identical)

```
ESP32 GPIO → 1kΩ resistor → PC817 LED anode
PC817 LED cathode → GND
PC817 collector → 330Ω → 5V
PC817 emitter → 2N2222A base
2N2222A emitter → GND
2N2222A collector → relay coil (−)
Relay coil (+) → 5V
1N4148 flyback diode across relay coil (anode at collector, cathode at 5V)
Relay NO + COM contacts → 2-pin screw terminal (KF301-2P, 5mm pitch)
Red LED + 1kΩ from GPIO to GND (relay status indicator)
```

## W5500 Ethernet Circuit

- W5500 powered at 3.3V, decoupling: 4×100nF + 10µF bulk
- 25MHz crystal with 22pF load caps on X1/X2
- EXRES1 pin → 12.4kΩ to GND (required by datasheet)
- SPI lines with 10kΩ pull-ups on SCSn, INTn, RSTn
- Differential pairs TPIN+/TPIN− and TPOUT+/TPOUT− routed to HR911105A magjack
- Route differential pairs at 100Ω differential impedance

## Connectors (all on PCB edges)

- J1: DC-005 barrel jack (9-24V in) — corner
- J2: HanRun HR911105A RJ45 magjack — edge
- J3: MicroUSB type B — edge
- J4/J5/J6: KF301-2P 5mm screw terminals (relay outputs, one per gate) — edge
- J7: 4-pin 2.54mm header (3.3V / GND / TX / RX) — debug UART
- SW1: boot button (GPIO0 to GND)
- SW2: reset button (EN to GND)

## Indicators

- LED1: green, power-on (3.3V rail, 1kΩ series)
- LED2/3/4: red, relay active status (one per channel, 1kΩ series from GPIO)

## Layout Guidelines

- Separate ground planes: logic zone (ESP32, W5500, CH340C) vs power zone (relays, screw terminals). PC817 optocouplers are the galvanic barrier between zones.
- Keep SPI traces short (<5cm), matched length
- Place 25MHz crystal as close as possible to W5500, no crossing traces
- Decoupling caps as close as possible to each VCC pin
- 4× M3 mounting holes in corners (copper-poured GND pad)
- Silkscreen labels on screw terminals: "ENTRADA / SALIDA / PEATONAL"
- Silkscreen label for barrel jack polarity (+ center)

## JLCPCB PCBA Notes

- All components available in LCSC catalog
- Prefer JLCPCB "Basic Parts" where possible to minimize extended part fees
- Key LCSC part numbers:
  - ESP32-WROOM-32E: C473012
  - W5500: C32843
  - CH340C: C84681
  - MP2307DN: C14272
  - AMS1117-3.3: C6186
  - HR911105A: C12074
  - SRD-05VDC-SL-C: C35449
  - PC817: C6786
