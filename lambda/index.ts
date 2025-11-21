import { Client } from "pg";

export const handler = async (event: any) => {
  const client = new Client({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
  });

  try {
    await client.connect();
    await client.query("INSERT INTO sensor_data (payload) VALUES ($1)", [
      JSON.stringify(event),
    ]);
    return { status: "ok" };
  } catch (error) {
    // Optionally log the error or handle it as needed
    return { status: "error", message: error instanceof Error ? error.message : String(error) };
  } finally {
    await client.end();
  }
};
