"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const pg_1 = require("pg");
const handler = async (event) => {
    const client = new pg_1.Client({
        host: process.env.DB_HOST,
        user: process.env.DB_USER,
        password: process.env.DB_PASSWORD,
        database: process.env.DB_NAME,
    });
    await client.connect();
    await client.query("INSERT INTO sensor_data (payload) VALUES ($1)", [
        JSON.stringify(event),
    ]);
    await client.end();
    return { status: "ok" };
};
exports.handler = handler;
