# CLAUDE.md — Portero Bot Hardware V2

Contexto para continuar el rediseño del PCB en Claude Code.

## Qué es este proyecto
Controlador IoT de portón (sistema Claustro4). PCB de 2 capas que reemplaza un
Raspberry Pi Pico + protoboard + placa de relés comercial.

- **MCU:** ESP32-WROOM-32E (U1)
- **Ethernet:** W5500 SPI (U2) + RJ45 con magnetics HR911105A (J2) + cristal 25 MHz (Y1)
- **USB-Serial:** CH340C (U3) + MicroUSB (J3)
- **Alimentación:** barril DC 9–24 V (J1) → 2× buck MP2307 (U4=5 V, U5=3.3 V)
- **Salidas:** 3 relés SRD-05VDC (K1–K3) → borneras KF301 (J4–J6),
  manejados por 2N2222 (Q1–Q3) y aislados con optoacopladores PC817 (ISO1–ISO3)
- **Protección:** Schottky SS34 (D1) + TVS SMAJ24CA (D2) + PTC (F1)

## Estado actual
El diseño venía de **Flux.ai** (suscripción demasiado cara). Se migró a **KiCad** (gratis).
El esquemático fue **reconstruido desde el export `.edif` de Flux** (netlist completo:
77 componentes, 60 redes, 256 pines) y regenerado como proyecto KiCad.

### Estructura
```
source-flux/        Export original de Flux (.edif, .flx, gerbers, BOM, pick&place)
data/               Netlist procesado (nets_clean.json, instances.json, master.json)
scripts/            Pipeline reproducible (ver abajo)
kicad/              Esquemático generado (.kicad_sch + .kicad_pro)
docs/               Revisión de diseño, BOM revisado, referencia, prompt de Flux
hardware/           (vacío) destino del PCB layout en KiCad
firmware/           (vacío) firmware PlatformIO ESP32
```

### Pipeline reproducible
```bash
pip install kiutils openpyxl python-docx          # dependencias
python3 scripts/10_parse_edif.py        # .edif -> data/nets_clean.json + instances.json
python3 scripts/20_build_master.py      # + valores/LCSC/footprints -> data/master.json
python3 scripts/30_gen_schematic.py     # -> kicad/portero-bot-v2.kicad_sch + .kicad_pro
```
El esquemático conecta por **etiquetas globales** (dos pines con la misma etiqueta =
misma red). Pines de potencia con varios pads (ESP32 GND, W5500 AVDD/AGND...) se
expanden a todos sus pads.

## Correcciones YA aplicadas (vs el diseño de Flux)
1. **L1, L2** → footprint de inductor de potencia 6×6 mm (estaban en 0603, imposible para buck de 3 A).
2. **C16,17,20,21,22,23** → 1210 (condensadores de bulk de los buck).
3. **F1** → PTC 1.1 A (estaba 0.5 A).
4. Valores raros normalizados (`0.01Mohms` → 10k, `muF` → uF).

## Pendientes / decisiones abiertas (IMPORTANTE)
1. **Correr ERC en KiCad** — no se pudo validar electrónicamente al generar el archivo.
2. **J2 (RJ45 HR911105A):** en Flux sus pines son anónimos (`~`), así que sus PADS no se
   mapearon. Asignar TXP/TXN/RXP/RXN y center-tap a 3V3 según datasheet del HR911105A.
3. **C2,3,6,7,8,9,10,11:** confirmar si son **100 nF** (desacople) o 100 µF. Flux los dejó
   como 100 µF en 0603 (imposible). Casi seguro 100 nF.
4. **3.3 V — discrepancia:** `docs/schematic-reference.md` dice AMS1117 LDO, pero el diseño
   real de Flux usa un **segundo buck MP2307** (U5). Decidir cuál se queda.
5. **Polaridad LEDs/diodos y pines del relé** (A1/A2/COM/NO): best-effort, confirmar con footprint.
6. **CH340C pin V3** y **MP2307 COMP/SS:** añadir componentes de datasheet si faltaban.

## Cómo seguir (sugerido)
- Abrir `kicad/portero-bot-v2.kicad_pro` en **KiCad 8** y correr **ERC**.
- Resolver los pendientes 2–6.
- `Tools → Update PCB from Schematic` para crear el PCB (footprints + ratsnest).
- Rutear respetando: **keep-out de la antena del ESP32**, **pares Ethernet TX/RX**
  cortos y simétricos con GND continuo debajo, **cobre + vías térmicas** bajo los MP2307.
- DRC → exportar Gerbers → JLCPCB/PCBWay.

### Tareas donde Claude Code ayuda mucho
- Instalar `kicad-cli` y correr ERC / exportar netlist para **verificar conectividad** de verdad.
- Ajustar los mapas de pines en `scripts/30_gen_schematic.py` y regenerar.
- Empezar el firmware en `firmware/` (API HTTP ya definida en `README.md`).
