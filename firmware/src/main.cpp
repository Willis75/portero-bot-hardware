// portero-bot-v2 firmware
// ESP32-WROOM-32E + W5500 Ethernet + 3 reles SRD-05VDC
// HTTP API + OTA + WiFi fallback

#include <Arduino.h>
#include <SPI.h>
#include <ETH.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ESPAsyncWebServer.h>
#include <ElegantOTA.h>
#include <esp_task_wdt.h>

#if __has_include("config.h")
  #include "config.h"
#else
  #include "config.example.h"
  #warning "Using config.example.h — crea include/config.h con tus credenciales"
#endif

// === Globals ===
AsyncWebServer server(HTTP_PORT);
volatile bool ethConnected = false;
volatile bool wifiConnected = false;
unsigned long lastRelayActivation[3] = {0, 0, 0};
unsigned long lastHealthcheck = 0;
unsigned long bootTime = 0;

const char* GATE_NAMES[3] = {"entrada", "salida", "peatonal"};
const int GATE_PINS[3] = {PIN_RELAY_ENTRADA, PIN_RELAY_SALIDA, PIN_RELAY_PEATONAL};

// === Ethernet event handler ===
void onEthEvent(arduino_event_id_t event) {
  switch (event) {
    case ARDUINO_EVENT_ETH_START:
      log_i("ETH started");
      ETH.setHostname("portero-bot");
      break;
    case ARDUINO_EVENT_ETH_CONNECTED:
      log_i("ETH connected (link up)");
      break;
    case ARDUINO_EVENT_ETH_GOT_IP:
      log_i("ETH IP: %s", ETH.localIP().toString().c_str());
      ethConnected = true;
      break;
    case ARDUINO_EVENT_ETH_DISCONNECTED:
      log_w("ETH disconnected");
      ethConnected = false;
      break;
    case ARDUINO_EVENT_ETH_STOP:
      log_w("ETH stopped");
      ethConnected = false;
      break;
    default:
      break;
  }
}

// === WiFi event handler ===
void onWiFiEvent(arduino_event_id_t event) {
  switch (event) {
    case ARDUINO_EVENT_WIFI_STA_GOT_IP:
      log_i("WiFi IP: %s", WiFi.localIP().toString().c_str());
      wifiConnected = true;
      break;
    case ARDUINO_EVENT_WIFI_STA_DISCONNECTED:
      log_w("WiFi disconnected, reconnecting...");
      wifiConnected = false;
      WiFi.reconnect();
      break;
    default:
      break;
  }
}

// === Setup helpers ===
void setupRelays() {
  for (int i = 0; i < 3; i++) {
    pinMode(GATE_PINS[i], OUTPUT);
    digitalWrite(GATE_PINS[i], LOW);  // Idle = LOW (opto LED off, BJT off, coil off)
  }
}

void setupEthernet() {
  WiFi.onEvent(onEthEvent);
  // W5500 via SPI on ESP32 (Arduino ESP32 core 2.0.5+)
  SPI.begin(PIN_SPI_SCK, PIN_SPI_MISO, PIN_SPI_MOSI, PIN_ETH_CS);
  if (!ETH.begin(ETH_PHY_W5500, 1, PIN_ETH_CS, PIN_ETH_INT, PIN_ETH_RST,
                 SPI3_HOST, 14000000, PIN_SPI_SCK, PIN_SPI_MISO, PIN_SPI_MOSI)) {
    log_e("ETH.begin() failed!");
    return;
  }
  if (ETH_USE_STATIC_IP) {
    IPAddress ip, gw, sn, dns1, dns2;
    ip.fromString(ETH_STATIC_IP);
    gw.fromString(ETH_GATEWAY);
    sn.fromString(ETH_SUBNET);
    dns1.fromString(ETH_DNS1);
    dns2.fromString(ETH_DNS2);
    ETH.config(ip, gw, sn, dns1, dns2);
  }
}

void setupWiFi() {
  if (!WIFI_ENABLED) return;
  WiFi.onEvent(onWiFiEvent);
  WiFi.mode(WIFI_STA);
  WiFi.setHostname("portero-bot");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  log_i("WiFi connecting to %s...", WIFI_SSID);
}

// === Auth ===
bool checkAuth(AsyncWebServerRequest* request) {
  if (!request->hasHeader("Authorization")) return false;
  String auth = request->header("Authorization");
  String expected = "Bearer " + String(API_TOKEN);
  return auth == expected;
}

// === Gate activation ===
bool activateGate(int idx) {
  if (idx < 0 || idx >= 3) return false;
  unsigned long now = millis();
  if (now - lastRelayActivation[idx] < RELAY_COOLDOWN_MS) {
    log_w("Gate %s: cooldown active (%lums ago)", GATE_NAMES[idx], now - lastRelayActivation[idx]);
    return false;
  }
  log_i("Activating gate: %s", GATE_NAMES[idx]);
  digitalWrite(GATE_PINS[idx], HIGH);
  delay(RELAY_PULSE_MS);
  digitalWrite(GATE_PINS[idx], LOW);
  lastRelayActivation[idx] = millis();
  return true;
}

// === HTTP handlers ===
void handleGate(AsyncWebServerRequest* request, int idx) {
  if (!checkAuth(request)) {
    request->send(401, "application/json", "{\"error\":\"unauthorized\"}");
    return;
  }
  if (activateGate(idx)) {
    String resp = "{\"status\":\"ok\",\"gate\":\"" + String(GATE_NAMES[idx]) + "\",\"uptime_s\":" + String((millis() - bootTime) / 1000) + "}";
    request->send(200, "application/json", resp);
  } else {
    request->send(429, "application/json", "{\"error\":\"cooldown\"}");
  }
}

void handleStatus(AsyncWebServerRequest* request) {
  String json = "{";
  json += "\"uptime_s\":" + String((millis() - bootTime) / 1000) + ",";
  json += "\"eth\":" + String(ethConnected ? "true" : "false") + ",";
  json += "\"wifi\":" + String(wifiConnected ? "true" : "false") + ",";
  json += "\"ip\":\"" + (ethConnected ? ETH.localIP().toString() : (wifiConnected ? WiFi.localIP().toString() : String("none"))) + "\",";
  json += "\"mac\":\"" + (ethConnected ? ETH.macAddress() : WiFi.macAddress()) + "\",";
  json += "\"heap_free\":" + String(ESP.getFreeHeap()) + ",";
  json += "\"rssi\":" + String(WiFi.RSSI()) + ",";
  json += "\"last_activations\":{";
  for (int i = 0; i < 3; i++) {
    json += "\"" + String(GATE_NAMES[i]) + "\":" + String(lastRelayActivation[i] / 1000);
    if (i < 2) json += ",";
  }
  json += "}}";
  request->send(200, "application/json", json);
}

void handleRestart(AsyncWebServerRequest* request) {
  if (!checkAuth(request)) {
    request->send(401, "application/json", "{\"error\":\"unauthorized\"}");
    return;
  }
  request->send(200, "application/json", "{\"status\":\"restarting\"}");
  delay(500);
  ESP.restart();
}

void setupHttpServer() {
  server.on("/api/gate/entrada",  HTTP_POST, [](AsyncWebServerRequest* r){ handleGate(r, 0); });
  server.on("/api/gate/salida",   HTTP_POST, [](AsyncWebServerRequest* r){ handleGate(r, 1); });
  server.on("/api/gate/peatonal", HTTP_POST, [](AsyncWebServerRequest* r){ handleGate(r, 2); });
  server.on("/api/status",        HTTP_GET,  handleStatus);
  server.on("/api/restart",       HTTP_POST, handleRestart);
  server.on("/",                  HTTP_GET, [](AsyncWebServerRequest* r){
    r->send(200, "text/plain", "portero-bot V2 - see /api/status");
  });
  // OTA mounted on /update
  ElegantOTA.begin(&server, OTA_USERNAME, OTA_PASSWORD);
  server.begin();
  log_i("HTTP server listening on port %d", HTTP_PORT);
}

// === Healthcheck ping ===
void sendHealthcheck() {
  if (!HEALTHCHECK_ENABLED) return;
  if (!ethConnected && !wifiConnected) return;
  HTTPClient http;
  http.setTimeout(3000);
  http.begin(HEALTHCHECK_URL);
  int code = http.GET();
  log_d("Healthcheck ping: HTTP %d", code);
  http.end();
}

// === Watchdog ===
void setupWatchdog() {
  esp_task_wdt_init(WATCHDOG_TIMEOUT_S, true);
  esp_task_wdt_add(NULL);
}

// === Main ===
void setup() {
  Serial.begin(115200);
  delay(100);
  log_i("=== portero-bot V2 booting ===");
  log_i("Firmware: %s %s", __DATE__, __TIME__);
  log_i("Chip: %s rev %d, %d MHz", ESP.getChipModel(), ESP.getChipRevision(), getCpuFrequencyMhz());

  bootTime = millis();
  setupRelays();
  setupEthernet();
  setupWiFi();
  setupHttpServer();
  setupWatchdog();

  log_i("=== Boot complete ===");
}

void loop() {
  esp_task_wdt_reset();  // Pet the watchdog
  ElegantOTA.loop();

  // Periodic healthcheck ping
  if (millis() - lastHealthcheck > HEALTHCHECK_PERIOD_MS) {
    sendHealthcheck();
    lastHealthcheck = millis();
  }

  delay(100);
}
