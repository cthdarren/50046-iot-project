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
// Store database configuration
const dbConfig = {
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
};
// Create client outside handler to reuse connections across invocations
let client = null;
async function getClient() {
    if (!client) {
        client = new pg_1.Client(dbConfig);
        await client.connect();
    }
    return client;
}
const handler = async (event) => {
    try {
        const dbClient = await getClient();
        await dbClient.query("INSERT INTO sensor_data (payload) VALUES ($1)", [
            JSON.stringify(event),
        ]);
        return { status: "ok" };
    }
    catch (error) {
        // Reset client on error to allow reconnection on next invocation
        if (client) {
            try {
                await client.end();
            }
            catch (endError) {
                // Ignore errors when closing connection
            }
            client = null;
        }
        return { status: "error", message: error instanceof Error ? error.message : String(error) };
    }
};
exports.handler = handler;
