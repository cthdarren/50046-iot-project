#pragma once

#include "mailer.h"
#include <PubSubClient.h>
#include <Arduino.h>
#include "certificate.h"
#include <ArduinoJson.h>


void MessageSender::begin() {
  messageQueue = xQueueCreate(queueSize, sizeof(Message));

  xTaskCreate(
    taskFunc,        // task function
    "MessageSender", // name
    8192,            // stack size
    this,            // parameter
    7,               // priority
    &taskHandle     // task handle
  );
}

bool MessageSender::sendAsync(const char* topic, const char* text) {
  Message m;
  strncpy(m.payload, text, sizeof(m.payload));
  strncpy(m.topic, topic, sizeof(m.topic));
  return xQueueSend(messageQueue, &m, 0) == pdTRUE;
}

// Task loop
void MessageSender::run() {
  Message msg;

  for (;;) {
    // Blocking wait until a message is available
    if (xQueueReceive(messageQueue, &msg, portMAX_DELAY) == pdTRUE) {
      while (!mqttClient.connected()) {
        if (mqttClient.connect(THINGNAME)) {
          Serial.println("\nConnected to AWS IoT.");
          break;
        } else {
          Serial.printf("Failed, rc=%d\n", mqttClient.state());
          delay(500);
        }
      }
      if (!mqttClient.publish(msg.topic, msg.payload, false)) {
        Serial.println("Message failed.");
      }
      else {
        Serial.println(msg.topic);
        Serial.println(msg.payload);
      }
    }
  }
};

void  MessageSender::updatePaper(bool isEmpty) {
  if (isEmpty) {
    if (!paperEmpty) {
      paperEmpty = true;
      sendUpdate();
      Serial.println("Paper changed to empty");
    }
  }
  else {
    if (paperEmpty) {
      paperEmpty = false;
      sendUpdate();
      Serial.println("Paper changed to full");
    }
  }
};

void  MessageSender::updateOccupied(bool detected) {
  unsigned long currentMillis = millis();
  if (detected) {
    Serial.println("Last detected updated");
    lastDetected = currentMillis;
  }
  if (detected) {
    if (!cubicleOccupied) {
      cubicleOccupied = true;
      sendUpdate();
      Serial.println("Status changed to occupied");
    }
  }
  else {
    if (cubicleOccupied && (currentMillis - lastDetected > 30000)) {
      cubicleOccupied = false;
      sendUpdate();
      Serial.println("Status changed to free");
    }
  }
};

void MessageSender::sendUpdate() {
  StaticJsonDocument<150> doc;
  doc["cubicle_id"] = 2;
  doc["occupied"] = cubicleOccupied;
  doc["toilet_roll_percentage"] = paperEmpty? 20 : 80;
  char output[150];
  serializeJson(doc, output, sizeof(output)); 
  sendAsync("cubicle/2/events", output);
}
