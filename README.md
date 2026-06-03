# Portero Bot — Hardware V2

Custom PCB and ESP32 firmware for the Claustro4 gate controller system.

## Overview

Replaces the Raspberry Pi Pico + protoboard + commercial relay board with a professional custom PCB.

- **MCU:** ESP32-WROOM-32E
- **Ethernet:** W5500 (SPI) + HanRun HR911105A RJ45
- **Relays:** 3× dry contact (simulates button press on gate opener controllers)
- **Power:** 9-24V DC barrel jack → 5V buck → 3.3V LDO
- **Programming:** MicroUSB (first flash) + OTA over Ethernet (updates)

## Repository Structure

```
hardware/       KiCad schematic + PCB layout + Gerber files
firmware/       PlatformIO ESP32 firmware (C++)
docs/           BOM, schematic reference, Flux.ai prompt
```

## API

The ESP32 exposes an HTTP API compatible with the existing Node.js bot (no changes required):

```
POST /abrir/vehicular_entrada
POST /abrir/vehicular_salida
POST /abrir/peatonal
GET  /healthz
POST /update   (OTA firmware upload)
```

## Related

- Bot: [Willis75/Portero-bot-telegram](https://github.com/Willis75/Portero-bot-telegram)
- Fabrication: JLCPCB PCBA (~$126 USD / 5 units)
