import { Client } from "pg";

export const handler = async (event: any) => {
  const client = new Client({
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
