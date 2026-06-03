# Portero Bot — Hardware V2 Schematic Document

**Fecha:** 2026-06-03  
**Versión:** 0.1 (draft para KiCad)  
**Fabricación:** JLCPCB PCBA  
**Dimensiones PCB sugeridas:** 100 × 80 mm, 2 capas

---

## BOM Completa (con LCSC part numbers)

| Ref | Componente | Valor / Parte | LCSC Part | Qty | Notas |
|-----|-----------|---------------|-----------|-----|-------|
| U1 | MCU | ESP32-WROOM-32E | C473012 | 1 | Módulo, no chip pelón |
| U2 | Ethernet Controller | W5500 (LQFP-48) | C32843 | 1 | SPI full-hardware TCP/IP |
| U3 | USB-Serial | CH340C (SOP-16) | C84681 | 1 | Para primer flash + debug |
| U4 | LDO 3.3V | AMS1117-3.3 (SOT-223) | C6186 | 1 | Hasta 800mA |
| U5 | Buck 5V | MP2307DN (SOIC-8) | C14272 | 1 | 3A, 9-24V in → 5V out |
| J1 | Barrel Jack | DC-005 5.5×2.1mm | C16214 | 1 | Entrada poder 9-24V DC |
| J2 | Ethernet | HanRun HR911105A | C12074 | 1 | RJ45 + magnetics + LEDs |
| J3 | MicroUSB | MicroUSB tipo B | C10418 | 1 | Flash inicial + debug |
| J4 | Portón 1 | KF301-2P 5mm | C474883 | 1 | NO + COM (vehicular entrada) |
| J5 | Portón 2 | KF301-2P 5mm | C474883 | 1 | NO + COM (vehicular salida) |
| J6 | Portón 3 | KF301-2P 5mm | C474883 | 1 | NO + COM (peatonal) |
| J7 | UART Debug | Pin header 4p 2.54mm | C49661 | 1 | TX/RX/GND/3V3 |
| K1 | Relé Portón 1 | SRD-05VDC-SL-C | C35449 | 1 | 5V coil, contactos 30VDC/10A |
| K2 | Relé Portón 2 | SRD-05VDC-SL-C | C35449 | 1 | |
| K3 | Relé Portón 3 | SRD-05VDC-SL-C | C35449 | 1 | |
| OK1 | Optoacoplador 1 | PC817 (DIP-4) | C6786 | 1 | Aislamiento GPIO↔relé |
| OK2 | Optoacoplador 2 | PC817 (DIP-4) | C6786 | 1 | |
| OK3 | Optoacoplador 3 | PC817 (DIP-4) | C6786 | 1 | |
| Q1 | Transistor Relé 1 | 2N2222A (TO-92) | C164886 | 1 | Driver bobina relé |
| Q2 | Transistor Relé 2 | 2N2222A (TO-92) | C164886 | 1 | |
| Q3 | Transistor Relé 3 | 2N2222A (TO-92) | C164886 | 1 | |
| D1 | Flyback Relé 1 | 1N4148 (SOD-123) | C81598 | 1 | Protección bobina relé |
| D2 | Flyback Relé 2 | 1N4148 (SOD-123) | C81598 | 1 | |
| D3 | Flyback Relé 3 | 1N4148 (SOD-123) | C81598 | 1 | |
| D4 | Protección entrada | SS34 (SMA) | C8598 | 1 | Diodo Schottky en barril |
| D5 | TVS entrada | SMAJ24CA (SMA) | C17114 | 1 | Surge protection 24V |
| F1 | Fusible PTC | 1A reseteable (1812) | C70069 | 1 | Protección sobrecorriente |
| L1 | Inductor buck | 22µH (CDRH104R) | C338228 | 1 | Para MP2307 |
| X1 | Cristal W5500 | 25 MHz (SMD 5032) | C9002 | 1 | Reloj para W5500 |
| SW1 | Botón BOOT | Tact 3×4mm SMD | C318884 | 1 | ESP32 boot mode |
| SW2 | Botón RESET | Tact 3×4mm SMD | C318884 | 1 | EN pin ESP32 |
| LED1 | Power LED | Verde 0805 | C84256 | 1 | Indicador 3.3V presente |
| LED2 | Relé 1 LED | Rojo 0805 | C84260 | 1 | Indica relé activo |
| LED3 | Relé 2 LED | Rojo 0805 | C84260 | 1 | |
| LED4 | Relé 3 LED | Rojo 0805 | C84260 | 1 | |
| C1-C4 | Desacoplo ESP32 | 100nF (0402) | C1525 | 4 | VDD pins |
| C5-C8 | Desacoplo W5500 | 100nF (0402) | C1525 | 4 | VCC pins |
| C9 | Bulk ESP32 | 10µF (0805) | C15850 | 1 | |
| C10 | Bulk W5500 | 10µF (0805) | C15850 | 1 | |
| C11-C12 | Buck output | 100µF electrolítico | C144986 | 2 | |
| C13 | Buck input | 100µF electrolítico | C144986 | 1 | |
| C14-C15 | Cristal W5500 | 22pF (0402) | C1570 | 2 | Load caps |
| R1 | LED Power | 1kΩ (0402) | C11702 | 1 | |
| R2-R4 | LED Relés | 1kΩ (0402) | C11702 | 3 | |
| R5-R7 | Base transistor | 1kΩ (0402) | C11702 | 3 | GPIO → base Q1-Q3 |
| R8-R10 | Opto input | 330Ω (0402) | C11734 | 3 | LED del PC817 |
| R11-R16 | Pull-ups SPI | 10kΩ (0402) | C25744 | 6 | CS, INT, RST W5500 |
| R17 | USB D+ | 27Ω (0402) | C11702 | 1 | CH340C |
| R18 | USB D- | 27Ω (0402) | C11702 | 1 | CH340C |

---

## Asignación de Pines ESP32

### SPI → W5500
| ESP32 GPIO | W5500 Pin | Función |
|-----------|-----------|---------|
| GPIO18 | SCLK | SPI Clock |
| GPIO23 | MOSI | SPI MOSI |
| GPIO19 | MISO | SPI MISO |
| GPIO5 | SCSn | Chip Select (activo LOW) |
| GPIO26 | INTn | Interrupt (activo LOW) |
| GPIO27 | RSTn | Reset (activo LOW) |

### Relés (a través de optoacopladores)
| ESP32 GPIO | Canal | Portón |
|-----------|-------|--------|
| GPIO32 | K1 | Vehicular Entrada |
| GPIO33 | K2 | Vehicular Salida |
| GPIO25 | K3 | Peatonal |

### USB Serial (CH340C)
| ESP32 GPIO | CH340C Pin |
|-----------|-----------|
| GPIO1 (TXD0) | RXD |
| GPIO3 (RXD0) | TXD |

### Control del ESP32
| Pin | Función |
|-----|---------|
| EN | SW2 (RESET) + 10kΩ pull-up a 3.3V |
| GPIO0 | SW1 (BOOT) + 10kΩ pull-up a 3.3V |

### UART Debug Header (J7)
| Pin | Señal |
|-----|-------|
| 1 | 3.3V |
| 2 | GND |
| 3 | GPIO1 (TX) |
| 4 | GPIO3 (RX) |

---

## Diagrama de Bloques — Conexiones

### Bloque 1: Power Supply

```
J1 (Barrel 9-24V DC)
  │
  ├── D4 (SS34 Schottky, polaridad)
  ├── D5 (SMAJ24CA TVS, surge)
  ├── F1 (PTC 1A)
  │
  └── VIN_RAW
        │
        ├── U5 (MP2307DN Buck)
        │     ├── L1 (22µH)
        │     ├── C11, C12 (100µF output)
        │     ├── C13 (100µF input)
        │     └── → VREG_5V (alimenta: K1/K2/K3 bobinas, CH340C, PC817 collectors)
        │
        └── VREG_5V
              └── U4 (AMS1117-3.3 LDO)
                    └── → VREG_3V3 (alimenta: ESP32, W5500, lógica)

LED1 (verde) con R1 (1kΩ) entre VREG_3V3 y GND — indicador power-on
```

### Bloque 2: ESP32-WROOM-32E

```
U1 (ESP32-WROOM-32E)
  ├── VDD (3.3V) — C1..C4 desacoplo 100nF a GND
  ├── GND
  ├── EN → 10kΩ pull-up a 3V3 + SW2 (RESET) a GND
  ├── GPIO0 → 10kΩ pull-up a 3V3 + SW1 (BOOT) a GND
  ├── GPIO1 (TXD0) → CH340C RXD + J7 pin 3
  ├── GPIO3 (RXD0) → CH340C TXD + J7 pin 4
  ├── GPIO5  → W5500 SCSn
  ├── GPIO18 → W5500 SCLK
  ├── GPIO19 → W5500 MISO
  ├── GPIO23 → W5500 MOSI
  ├── GPIO26 → W5500 INTn
  ├── GPIO27 → W5500 RSTn
  ├── GPIO32 → R5 (1kΩ) → Opto OK1 (Portón 1)
  ├── GPIO33 → R6 (1kΩ) → Opto OK2 (Portón 2)
  └── GPIO25 → R7 (1kΩ) → Opto OK3 (Portón 3)
```

### Bloque 3: W5500 Ethernet Controller

```
U2 (W5500 LQFP-48)
  ├── VCC (3.3V) — C5..C8 desacoplo 100nF a GND, C10 bulk 10µF
  ├── GND
  ├── SCLK ← GPIO18
  ├── MOSI ← GPIO23
  ├── MISO → GPIO19
  ├── SCSn ← GPIO5 (con R11 10kΩ pull-up a 3V3)
  ├── INTn → GPIO26 (con R12 10kΩ pull-up a 3V3)
  ├── RSTn ← GPIO27 (con R13 10kΩ pull-up a 3V3)
  ├── EXRES1 → 12.4kΩ a GND (referencia interna, requerido por datasheet)
  ├── X1/X2 → X1 cristal 25MHz (con C14, C15 22pF a GND)
  └── TPIN+/TPIN-/TPOUT+/TPOUT- → J2 (HanRun HR911105A magnetics integrados)

J2 (HanRun HR911105A)
  ├── Magnetics internos ya integrados — sin componentes externos adicionales
  ├── LED_LINK → indicador link Ethernet (integrado en magjack)
  └── LED_ACT  → indicador actividad (integrado en magjack)
```

### Bloque 4: USB-Serial CH340C

```
J3 (MicroUSB)
  ├── VBUS (5V) → no conectado a VREG_5V (alimentación independiente solo para flash)
  ├── D+ → R17 (27Ω) → CH340C UD+
  ├── D- → R18 (27Ω) → CH340C UD-
  └── GND

U3 (CH340C SOP-16)
  ├── VCC (3.3V)
  ├── GND
  ├── UD+ ← R17 desde USB D+
  ├── UD- ← R18 desde USB D-
  ├── TXD → ESP32 GPIO3 (RXD0)
  └── RXD ← ESP32 GPIO1 (TXD0)

Nota: CH340C tiene oscilador interno — no requiere cristal externo
```

### Bloque 5: Circuito de Relé (×3, idéntico por canal)

Ejemplo para Canal 1 (Portón Vehicular Entrada):

```
ESP32 GPIO32
  │
  R5 (1kΩ)
  │
  OK1 (PC817) — pin 1 (Ánodo LED)
  OK1         — pin 2 (Cátodo LED) → GND
  OK1         — pin 3 (Collector) → R8 (330Ω) → VREG_5V
  OK1         — pin 4 (Emitter)
  │
  R5_base: no necesario (ya R8 limita corriente)
  │
  Base de Q1 (2N2222A) ← Emitter de OK1
  Emitter de Q1 → GND
  Collector de Q1 → Bobina K1 (SRD-05VDC-SL-C)
  
  K1 bobina:
  ├── Pin + → VREG_5V
  ├── Pin - → Collector Q1
  └── D1 (1N4148) en antiparalelo (ánodo a collector, cátodo a 5V)

  K1 contactos:
  ├── COM → J4 Pin 1
  ├── NO  → J4 Pin 2
  └── NC  → no conectado

LED2 (rojo) con R2 (1kΩ) entre GPIO32 y GND — indicador visual relé activo
```

*Mismo circuito para K2/OK2/Q2/D2/LED3/J5 (GPIO33) y K3/OK3/Q3/D3/LED4/J6 (GPIO25)*

---

## Notas de Layout PCB (para el diseñador)

### Separación de planos
- **Zona A (lógica):** ESP32, W5500, CH340C, power supply — GND común
- **Zona B (potencia/relés):** K1-K3, borneras J4-J6 — mismo GND pero rutar lejos de zona A
- Los optoacopladores PC817 son la barrera física entre zonas A y B

### Routing crítico
- Trazas SPI (GPIO5/18/19/23 → W5500): mantener <5cm, paralelas, mismo largo aprox.
- Cristal X1 del W5500: lo más cerca posible al chip, sin cruzar otras trazas
- Magjack J2: rutar diferencial TPIN/TPOUT con impedancia 100Ω diferencial
- Decoupling caps (100nF): lo más cerca posible a cada pin VCC del chip

### Mecánica
- Borneras J4/J5/J6 en el borde de la PCB (acceso de cables desde exterior)
- Barrel jack J1 en esquina, también borde
- RJ45 J2 en borde
- MicroUSB J3 en borde
- SW1 (BOOT) y SW2 (RESET) accesibles sin desmontar de gabinete
- Header UART J7 accesible (para emergencias si OTA falla)
- 4 agujeros de montaje M3 en esquinas (3mm diámetro, pad de cobre para GND)

---

## Firmware — API HTTP (sin cambios respecto al Pico)

El ESP32 expone exactamente la misma API que el Pico actual. **Cero cambios en el bot Node.js.**

```
POST /abrir/vehicular_entrada   → cierra K1 (500ms pulso)
POST /abrir/vehicular_salida    → cierra K2 (500ms pulso)  
POST /abrir/peatonal            → cierra K3 (500ms pulso)
GET  /healthz                   → {"ok": true, "uptime": 12345}
POST /update                    → OTA firmware upload (AsyncElegantOTA)
```

**Stack firmware:**
- PlatformIO + Arduino-ESP32 framework
- `AsyncWebServer_ESP32_W5500` (Ethernet)
- `ESPAsyncWebServer` (HTTP)
- `AsyncElegantOTA` (OTA updates)
- LittleFS para config (IP, auth token)
- IP estática configurada en flash o DHCP reservation en router caseta

---

## Presupuesto estimado JLCPCB (5 unidades)

| Concepto | Costo USD |
|----------|-----------|
| PCB (5 pcs, 2 capas, 100×80mm) | ~$5 |
| Assembly setup | ~$8 |
| Stencil | ~$8 |
| Componentes BOM (×5) | ~$75 |
| Shipping DHL a México | ~$30 |
| **Total** | **~$126 USD** |

Tiempo estimado: 7-10 días fab + 5-7 días envío = **~3 semanas**

---

## Pendientes antes de mandar a fabricar

- [ ] Confirmar el diseñador KiCad (Fiverr/Upwork o hazlo tú)
- [ ] Verificar stock de W5500 (C32843) en LCSC el día del pedido
- [ ] Confirmar dimensiones exactas del gabinete para ajustar PCB
- [ ] Definir si la IP del ESP32 va estática en firmware o por DHCP reservation
- [ ] Primera tirada: bench test OTA antes de instalar en caseta
- [ ] Actualizar `portero-health.sh` si cambia el endpoint de healthcheck
