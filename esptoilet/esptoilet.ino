#include <HTTPClient.h>

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include "mailer.h"
#include "detect_manager.h"
#include "weight_manager.h"
#include "certificate.h"
#include "time.h"

#define IRPIN 33  // using GPIO2
#define WEIGHTPIN 32  // using GPIO4

// WIFI
WiFiClientSecure net;
const char* WIFI_SSID  = "slowwifi";
const char* WIFI_PASSWORD  = "888888889";

// MQTT
PubSubClient client(net);

// MAILER
MessageSender sender(client);
DetectManager detectmanager{IRPIN, &sender};
WeightManager weightManager{WEIGHTPIN, &sender};

void connectWiFi();
void connectAWS();

void setup() {
  Serial.begin(115200);
  delay(10);
  connectAWS();

  // init background
  sender.begin();
  detectmanager.begin();
  weightManager.begin();

  Serial.println("Started successfully");
}

// main loop
void loop() {
  client.loop();
  detectmanager.update();
  weightManager.update();
  delay(1);
}

// helper functions
void connectWiFi() {
  WiFi.disconnect(true);
  Serial.printf("Starting connect to SSID: %s\n", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED ) {
    Serial.print(".");
    delay(500);
  }
  Serial.println("\nWiFi connected (PEAP). IP: ");
  Serial.println(WiFi.localIP());
}

void connectAWS() {
  connectWiFi();

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Cannot connect to AWS: WiFi not connected.");
    return;
  }

  net.setCACert(AWS_CERT_CA);
  net.setCertificate(AWS_CERT_CRT);
  net.setPrivateKey(AWS_CERT_PRIVATE);

  client.setServer(AWS_IOT_ENDPOINT, 8883);

  Serial.println("Connecting to AWS IoT...");
  while (!client.connected()) {
    if (client.connect(THINGNAME)) {
      Serial.println("\nConnected to AWS IoT.");
      break;
    } else {
      Serial.printf("Failed, rc=%d\n", client.state());
      delay(500);
    }
  }
}