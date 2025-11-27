// Minimal bridge: subscribe to MQTT topics and invoke local lambda HTTP endpoint.
import mqtt from "mqtt";
import axios from "axios";

const host = process.env.MQTT_HOST || "mqtt";
const port = process.env.MQTT_PORT || "1883";
const lambdaUrl = process.env.LAMBDA_INVOKE_URL || "http://lambda:8080/invoke";

const client = mqtt.connect(`mqtt://${host}:${port}`);

client.on("connect", () => {
  console.log("Bridge connected to MQTT broker");
  client.subscribe("sensors/#", (err) => {
    if (err) console.error("Subscription error", err);
  });
});

client.on("message", async (topic, message) => {
  const payloadStr = message.toString();
  let payload = payloadStr;
  try {
    payload = JSON.parse(payloadStr);
  } catch (err) {
    // Failed to parse JSON; using original string as fallback payload.
    console.warn("Failed to parse MQTT message as JSON:", err, "Payload:", payloadStr);
  }
  const event = { topic, payload, received_at: new Date().toISOString() };
  try {
    const resp = await axios.post(lambdaUrl, event, { timeout: 5000 });
    console.log("Lambda response", resp.data);
  } catch (e) {
    console.error("Failed invoking lambda", (e && e.message) || e);
  }
});

client.on("error", (err) => {
  console.error("MQTT error", err);
});
