# BOM Instructions — Portero Bot V2 para JLCPCB

## Paso 1: Marcar THT como DNP

Estos componentes NO van a JLCPCB Assembly (tú los soldarás manual):

```
Q1, Q2, Q3, K1, K2, K3, J1, J3, J4, J5, J6, J7, F1, SW1, SW2, J2
```

En BOM editado para JLCPCB, eliminar estas filas (mover a hoja "Manual Assembly").

## Paso 2: Buscar LCSC# en JLCPCB Parts Library

URL: https://jlcpcb.com/parts

Para cada componente SMD:
1. Pegar el valor o nombre en el search
2. Filtrar por:
   - Library type: **Basic** primero (ahorra $3 setup fee), Extended si no hay
   - Package/footprint: debe matchear (ej. 0603, 1210, SOIC-8, etc.)
   - Stock: >100 unidades
3. Copiar el `C#####` (LCSC Part Number)
4. Pegar en columna LCSC del BOM CSV

## Paso 3: Componentes críticos a buscar EXACTO

```
U1 ESP32-WROOM-32E-N16    → Buscar EXACT "ESP32-WROOM-32E-N16"
                            Verificar N16 (16MB flash, no N8 ni N4)
U2 W5500                  → WIZnet, package LQFP-48
U3 CH340C                 → WCH, SOIC-16, no CH340G ni CH340N
U4, U5 MP2307DN           → MPS Semi, package SOIC-8 EP
                            CRÍTICO: verificar versión "DN-HW-LF-Z"
Y1 25MHz crystal 3225     → 4 pads, ±20ppm tolerance ok
D1 SS34                   → Schottky 3A 40V, SMA
D2 SMAJ24CA               → TVS bidirectional 24V, SMA
D3,4,5 1N4148WS           → SOD-323, fast switching
ISO1-3 PC817              → DIP-4 (NO SOP-4), Sharp/Lite-On
```

## Paso 4: Footprints comunes (Basic Parts típicos)

| Valor | Footprint | LCSC search |
|---|---|---|
| Resistencias 0603 1% | 0603 | "R 0603 1% [valor]" |
| Cap 100nF 0603 X7R | 0603 | "100nF 0603 50V X7R" |
| Cap 100uF 1210 X5R | 1210 | "100uF 1210 X5R" |
| LED 0603 verde | 0603 | "LED 0603 green" |
| LED 0603 rojo | 0603 | "LED 0603 red" |

## Paso 5: Verificación final

Antes de subir BOM a JLCPCB:
- [ ] Todas las filas SMD tienen LCSC# (excepto DNP)
- [ ] No quedan "Extended Parts" sin necesidad (cada uno = $3 setup)
- [ ] Stock confirmado en JLCPCB (>30 unidades por componente)
- [ ] Quantity para 5 PCBs: multiplicar refs (ej. 8 resistores * 5 = 40 ud)

## Paso 6: Subir a JLCPCB

1. Order PCB → Upload `portero-bot-v2-GERBERS.zip`
2. PCB Specs:
   - Layers: **2**
   - Dimensions: 117.5 × 104.5 mm (auto-detect del Gerber)
   - Thickness: 1.6mm
   - Solder mask: green (cheapest)
   - Surface finish: HASL lead-free (cheapest) o ENIG (mejor para SMD)
   - Quantity: 5
3. Assembly Service:
   - Enable PCB Assembly
   - Side: Top only (componentes solo F.Cu)
   - Quantity: 5
   - Upload BOM (CSV) + CPL (CSV)
4. Confirm parts → revisar matches → checkout

## Costos esperados

- 5 PCBs (sin assembly): ~$10 + shipping ~$25 = $35
- 5 PCBs con SMD assembly: ~$80-120 según extended parts
- Setup fees: $8 stencil + $0.0017/joint * ~200 joints = $0.34
- Total ~$45-130

## Mi paste-friendly template ya casi listo

Si quieres, te genero un script que toma tu `docs/Portero-Bot-V2_BOM-revisado.xlsx` (que ya tiene LCSC#) y lo mergea con este CSV automaticamente.
