#pragma once

#include <Arduino.h>
#include "mailer.h"

class DetectManager {

public:
  DetectManager(uint8_t pin, MessageSender* messageSender, unsigned long intervalMs = 1000)
    : detectPin(pin), sender(messageSender), interval(intervalMs), lastRead(0), occupied(false){};

  void begin() {
    pinMode(detectPin, INPUT);
  };

  // Call this repeatedly in loop()
  void update() {
    unsigned long currentMillis = millis();

    // every interval
    if (currentMillis - lastRead >= interval) {
      lastRead = currentMillis;
      bool detected = detect();
      sender->updateOccupied(detected);
    }
  }

private:
  uint8_t detectPin;
  unsigned long interval;
  unsigned long lastRead;
  MessageSender* sender;

  // cubicle status
  bool occupied;

  bool detect() {
    return digitalRead(detectPin) == LOW;
  }
  
};