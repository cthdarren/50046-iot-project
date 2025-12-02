#pragma once

#include <Arduino.h>
#include "mailer.h"

// number of running average to take
static const int NUM_VALUES = 10;

class WeightManager {

public:
  WeightManager(uint8_t pin, MessageSender* messageSender, unsigned long intervalMs = 1000)
    : sensorPin(pin), sender(messageSender), interval(intervalMs){};

  void begin() {
    for (int i = 0; i < NUM_VALUES; i++) values[i] = 0;
  };

  // Call this repeatedly in loop()
  void update() {
    unsigned long currentMillis = millis();

    // every second check
    if (currentMillis - lastRead >= interval) {
      lastRead = currentMillis;
      int currPressure = analogRead(sensorPin);
      Serial.println(currPressure);
      addValue(currPressure);

      // check if the running sum is filled
      if (!filled) return;

      sender->updatePaper(empty());
    }
  }

private:
  uint8_t sensorPin;
  unsigned long interval;
  unsigned long lastRead = 0;
  MessageSender* sender;

  float values[NUM_VALUES];
  int indexPos = 0;
  float runningSum = 0;
  bool filled = false;

  bool empty() {
    return getAverage() > 3500;
  }

  void addValue(float v) {
    runningSum -= values[indexPos];

    values[indexPos] = v;
    runningSum += v;
  
    indexPos++;
    if (indexPos >= NUM_VALUES) {
      indexPos = 0;
      filled = true;
    }
  }

  float getAverage() {
    if (filled) return runningSum / NUM_VALUES;
    else return runningSum / indexPos;  // not full yet
  }
  
};