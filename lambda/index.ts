import { Client } from "pg";

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
let client: Client | null = null;

async function getClient(): Promise<Client> {
  if (!client) {
    client = new Client(dbConfig);
    await client.connect();
  }
  return client;
}

export const handler = async (event: any) => {
  try {
    const dbClient = await getClient();
    await dbClient.query("INSERT INTO sensor_data (payload) VALUES ($1)", [
      JSON.stringify(event),
    ]);
    return { status: "ok" };
  } catch (error) {
    // Reset client on error to allow reconnection on next invocation
    if (client) {
      try {
        await client.end();
      } catch (endError) {
        // Ignore errors when closing connection
      }
      client = null;
    }
    return { status: "error", message: error instanceof Error ? error.message : String(error) };
  }
};
