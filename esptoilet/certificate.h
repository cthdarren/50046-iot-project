#pragma once

#define THINGNAME "sensor-device-001" 

const char AWS_IOT_ENDPOINT[] = "XXXX-ats.iot.ap-southeast-1.amazonaws.com";

// Certificates
static const char AWS_CERT_CA[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
XXXX
-----END CERTIFICATE-----
)EOF";

static const char AWS_CERT_CRT[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
XXXX
-----END CERTIFICATE-----
)EOF";

static const char AWS_CERT_PRIVATE[] PROGMEM = R"EOF(
-----BEGIN RSA PRIVATE KEY-----
XXXX
-----END RSA PRIVATE KEY-----
)EOF";