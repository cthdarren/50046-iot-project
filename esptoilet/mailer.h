#pragma once

#include <PubSubClient.h>
#include <Arduino.h>

class MessageSender {
public:
    MessageSender(PubSubClient& client, size_t queueSize = 10)
        : mqttClient(client), queueSize(queueSize), lastDetected{0} {};

    void begin();

    void updatePaper(bool isEmpty);
    void updateOccupied(bool occupied);

private:
    static const int MAX_CHN_LEN = 128;
    static const int MAX_MSG_LEN = 128;

    bool paperEmpty = false;
    bool cubicleOccupied = false;
    unsigned long lastDetected;

    struct Message {
        char topic[MAX_CHN_LEN];
        char payload[MAX_MSG_LEN];
    };

    PubSubClient& mqttClient;

    TaskHandle_t taskHandle = nullptr;
    QueueHandle_t messageQueue = nullptr;
    size_t queueSize;

    void sendUpdate();
    bool sendAsync(const char* topic, const char* text);

    static void taskFunc(void* param) {
      MessageSender* self = static_cast<MessageSender*>(param);
      self->run();
    }

    // Task loop
    void run();
};