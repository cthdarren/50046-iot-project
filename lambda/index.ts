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

async function ensureCubicleExists(dbClient: Client, cubicle_id: number) {
  const result = await dbClient.query("SELECT id FROM cubicles WHERE id = $1", [cubicle_id]);
  if (result.rowCount === 0) {
    throw new Error(`Cubicle ${cubicle_id} does not exist`);
  }
}

export const cubicleEventHandler = async (event: any) => {
  try {
    const dbClient = await getClient();
    await ensureCubicleExists(dbClient, event.cubicle_id);
    await dbClient.query("INSERT INTO cubicle_events (cubicle_id, occupied, toilet_roll_percentage, timestamp) VALUES ($1, $2, $3, CURRENT_TIMESTAMP)", [
      event.cubicle_id,
      event.occupied,
      event.toilet_roll_percentage,
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

export const cubicleStateHandler = async (event: any) => {
  try {
    const dbClient = await getClient();
    await ensureCubicleExists(dbClient, event.cubicle_id);
    await dbClient.query("INSERT INTO cubicle_states (cubicle_id, occupied, toilet_roll_percentage) VALUES ($1, $2, $3) ON CONFLICT (cubicle_id) DO UPDATE SET occupied = $2, toilet_roll_percentage = $3, updated_at = CURRENT_TIMESTAMP", [
      event.cubicle_id,
      event.occupied,
      event.toilet_roll_percentage,
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
