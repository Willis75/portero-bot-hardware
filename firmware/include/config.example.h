#pragma once
// Copia este archivo a config.h y rellena con credenciales reales.
// config.h esta gitignored.

// === Network ===
// Static IP for Ethernet (preferir static para 24/7, no depende DHCP del router)
#define ETH_USE_STATIC_IP   true
#define ETH_STATIC_IP       "192.168.1.50"
#define ETH_GATEWAY         "192.168.1.1"
#define ETH_SUBNET          "255.255.255.0"
#define ETH_DNS1            "1.1.1.1"
#define ETH_DNS2            "8.8.8.8"

// WiFi backup (si Ethernet falla)
#define WIFI_ENABLED        true
#define WIFI_SSID           "TU_WIFI_SSID"
#define WIFI_PASSWORD       "TU_WIFI_PASSWORD"

// === Auth ===
// Token Bearer para autenticar requests HTTP
// Generate: openssl rand -hex 32
#define API_TOKEN           "REEMPLAZA_CON_TOKEN_HEX_32_BYTES"

// === OTA ===
#define OTA_USERNAME        "admin"
#define OTA_PASSWORD        "REEMPLAZA_CON_PASS_FUERTE"

// === Healthchecks.io (opcional - heartbeat externo) ===
#define HEALTHCHECK_ENABLED true
#define HEALTHCHECK_URL     "https://hc-ping.com/REEMPLAZA-CON-UUID"
#define HEALTHCHECK_PERIOD_MS  60000  // 60 segundos

// === Hardware: pin assignments (NO cambiar - hardware fijo V2) ===
// ESP32-WROOM-32E -> W5500 SPI
#define PIN_ETH_CS          5
#define PIN_ETH_INT         26
#define PIN_ETH_RST         27
#define PIN_SPI_SCK         18
#define PIN_SPI_MISO        19
#define PIN_SPI_MOSI        23

// Reles (GPIO output)
#define PIN_RELAY_ENTRADA   32  // K1 - portón entrada
#define PIN_RELAY_SALIDA    33  // K2 - portón salida
#define PIN_RELAY_PEATONAL  25  // K3 - portón peatonal

// LEDs indicadores (en hardware solo LED1=3V3 y LED5=5V; ningun GPIO controla LED)
// LEDs son indicadores power-on directamente conectados al rail

// === Timing ===
#define RELAY_PULSE_MS      500     // Duracion del cierre de contacto (simula presionar botón)
#define RELAY_COOLDOWN_MS   2000    // Tiempo minimo entre activaciones del mismo relé
#define WATCHDOG_TIMEOUT_S  5       // Task watchdog
#define HTTP_PORT           80
