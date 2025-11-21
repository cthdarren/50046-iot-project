"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const pg_1 = require("pg");
// Create client outside handler to reuse connections across invocations
const client = new pg_1.Client({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
});
let isConnected = false;
const handler = async (event) => {
    try {
        // Connect only if not already connected
        if (!isConnected) {
            await client.connect();
            isConnected = true;
        }
        await client.query("INSERT INTO sensor_data (payload) VALUES ($1)", [
            JSON.stringify(event),
        ]);
        return { status: "ok" };
    }
    catch (error) {
        // Reset connection state on error to allow reconnection on next invocation
        isConnected = false;
        return { status: "error", message: error instanceof Error ? error.message : String(error) };
    }
};
exports.handler = handler;
