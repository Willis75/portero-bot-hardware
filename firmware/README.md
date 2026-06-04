# portero-bot V2 firmware

Firmware ESP32 para hardware V2 (PCB custom con W5500 Ethernet + 3 relés).

## Setup primera vez

1. **Instalar PlatformIO**:
   ```
   pip install platformio
   ```
   O instalar extensión PlatformIO en VSCode.

2. **Crear `include/config.h`** copiando `config.example.h`:
   ```
   cp include/config.example.h include/config.h
   ```

3. **Llenar credenciales** en `include/config.h`:
   - `API_TOKEN`: generar con `openssl rand -hex 32`
   - `WIFI_SSID` / `WIFI_PASSWORD`: red WiFi backup
   - `ETH_STATIC_IP`: IP fija para Ethernet en la red del condominio
   - `OTA_USERNAME` / `OTA_PASSWORD`: para subir firmware OTA
   - `HEALTHCHECK_URL`: opcional (healthchecks.io)

4. **Build + flash via USB** (primera vez):
   ```
   cd firmware/
   pio run --target upload --upload-port COM4   # ajustar COM port
   pio device monitor
   ```

5. **Después flash via OTA** (sin desconectar):
   - Web UI: http://192.168.1.50/update
   - O CLI: `pio run --target upload --upload-protocol espota --upload-port 192.168.1.50`

## API HTTP

Todos los `POST` requieren header `Authorization: Bearer <API_TOKEN>`.

| Método | Endpoint | Función |
|---|---|---|
| POST | `/api/gate/entrada` | Activa relé K1 (portón entrada) |
| POST | `/api/gate/salida` | Activa relé K2 (portón salida) |
| POST | `/api/gate/peatonal` | Activa relé K3 (portón peatonal) |
| GET  | `/api/status` | Healthcheck JSON (uptime, IP, heap, rssi) |
| POST | `/api/restart` | Reset suave del ESP32 |
| GET  | `/update` | UI web OTA (basic auth) |

### Ejemplo curl

```bash
TOKEN="tu_token_de_32_bytes_hex"
curl -X POST -H "Authorization: Bearer $TOKEN" http://192.168.1.50/api/gate/entrada
# Response: {"status":"ok","gate":"entrada","uptime_s":12345}

curl http://192.168.1.50/api/status
# Response: {"uptime_s":12345,"eth":true,"wifi":false,"ip":"192.168.1.50","heap_free":234567,...}
```

## 24/7 Features

- **Brownout detector** (2.43V) → reset si rail 3.3V baja
- **Task Watchdog** (5s) → reset si firmware hang
- **Ethernet primary + WiFi fallback** automático
- **Static IP** (no depende DHCP)
- **Cooldown 2s** entre activaciones del mismo relé (evita re-trigger accidental)
- **Pulse 500ms** simula presión de botón
- **OTA con rollback** (AsyncElegantOTA)
- **Healthchecks.io ping** cada 60s para detectar offline

## Hardware pin map (NO modificar)

```
GPIO 32 → RELAY1 (entrada)
GPIO 33 → RELAY2 (salida)
GPIO 25 → RELAY3 (peatonal)
GPIO 5  → ETH_CS (W5500)
GPIO 18 → SPI_SCK
GPIO 19 → SPI_MISO
GPIO 23 → SPI_MOSI
GPIO 26 → ETH_INT
GPIO 27 → ETH_RST
GPIO 0  → BOOT (button SW1)
EN      → RESET (button SW2)
RX/TX 0 → UART debug (CH340 USB)
```

## Troubleshooting

- **Boot loop**: verificar VIN ≥ 9V, brownout detector activo
- **Ethernet not connecting**: revisar cable RJ45, link LED en magjack, ETH_RST cycle
- **WiFi only**: si Ethernet falla, firmware sigue por WiFi backup
- **OTA fails**: verificar partition table tiene OTA0 + OTA1 slots (16MB flash)
