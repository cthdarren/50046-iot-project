"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const pg_1 = require("pg");
// Validate required environment variables
const requiredEnvVars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME'];
for (const envVar of requiredEnvVars) {
    if (!process.env[envVar]) {
        throw new Error(`Missing required environment variable: ${envVar}`);
    }
}
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
        // Reset connection state and close client on error to prevent connection leaks
        if (isConnected) {
            try {
                await client.end();
            }
            catch (endError) {
                // Ignore errors when closing connection
            }
            isConnected = false;
        }
        return { status: "error", message: error instanceof Error ? error.message : String(error) };
    }
};
exports.handler = handler;
