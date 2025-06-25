#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <Adafruit_NeoPixel.h>

// WiFi settings (modify these)
const char* ssid = "freebox_XTSWNL";        // Your WiFi SSID
const char* password = "chouneetfrancoise"; // Your WiFi password
IPAddress staticIP(192, 168, 0, 100);       // Static IP for ESP8266
IPAddress gateway(192, 168, 0, 254);          // Gateway IP
IPAddress subnet(255, 255, 255, 0);         // Subnet mask

// LED strip settings
#define LED_PIN D4           // GPIO2 (D4 on NodeMCU)
#define NUM_LEDS 30         // 5m strip with 60 LEDs/m
#define BRIGHTNESS 50        // 0-255, limit to reduce power draw

// Initialize NeoPixel strip
Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// Initialize web server on port 80
ESP8266WebServer server(80);

// Current LED color (for /status)
uint32_t current_color = 0;

// Parse hex color (e.g., "FF5733" -> uint32_t)
uint32_t parseHexColor(String hex) {
  hex.toUpperCase(); // Normalize to uppercase
  if (hex.length() != 6) {
    Serial.println("Invalid hex color length: " + hex);
    return 0;
  }
  char hexChars[7];
  hex.toCharArray(hexChars, 7);
  unsigned long color = strtoul(hexChars, NULL, 16);
  if (color == 0 && hex != "000000") {
    Serial.println("Invalid hex color format: " + hex);
    return 0;
  }
  uint8_t r = (color >> 16) & 0xFF;
  uint8_t g = (color >> 8) & 0xFF;
  uint8_t b = color & 0xFF;
  return strip.Color(r, g, b);
}

// Set all LEDs to the specified color
void setAllLeds(uint32_t color) {
  for (int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, color);
  }
  strip.show();
  current_color = color;
}

// Handle /all?color=<hex_color>
void handleSetAll() {
  String hex = server.arg("color");
  Serial.println("Requested URL: /all?color=" + hex);
  if (hex.length() != 6) {
    String error = "{\"status\":\"error\",\"message\":\"Invalid color, use ?color=RRGGBB\"}";
    server.send(400, "application/json", error);
    Serial.println(error);
    return;
  }
  uint32_t color = parseHexColor(hex);
  if (color == 0 && hex != "000000") {
    String error = "{\"status\":\"error\",\"message\":\"Invalid hex color format\"}";
    server.send(400, "application/json", error);
    Serial.println(error);
    return;
  }
  setAllLeds(color);
  String response = "{\"status\":\"success\",\"color\":\"" + hex + "\"}";
  server.send(200, "application/json", response);
  Serial.println(response);
}

// Handle /status
void handleStatus() {
  char hex[7];
  sprintf(hex, "%06X", ((current_color >> 16) & 0xFF) | ((current_color >> 8) & 0xFF00) | (current_color & 0xFF0000));
  String response = "{\"status\":\"success\",\"color\":\"" + String(hex) + "\",\"num_leds\":" + String(NUM_LEDS) + "}";
  server.send(200, "application/json", response);
  Serial.println("Status response: " + response);
}

// Handle 404
void handleNotFound() {
  String path = server.uri();
  Serial.println("Not found: " + path);
  server.send(404, "application/json", "{\"status\":\"error\",\"message\":\"Endpoint not found\"}");
}

void setup() {
  // Initialize serial for debugging
  Serial.begin(115200);
  Serial.println("\nStarting LED Server");

  // Initialize LED strip
  strip.begin();
  strip.setBrightness(BRIGHTNESS);
  setAllLeds(strip.Color(0, 0, 0)); // Turn off all LEDs initially
  Serial.println("LED strip initialized");

  // Connect to WiFi
  WiFi.config(staticIP, gateway, subnet);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // Setup server routes
  server.on("/all", HTTP_GET, handleSetAll); // Handle /all?color=<hex_color>
  server.on("/status", HTTP_GET, handleStatus);
  server.onNotFound(handleNotFound);
  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();
}