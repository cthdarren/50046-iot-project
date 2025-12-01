import { Client } from "pg";

// Store database configuration
// Note: DB_PASSWORD should be retrieved from Secrets Manager in production
const dbConfig = {
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD || process.env.DB_USER, // Fallback for testing
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
  const result = await dbClient.query("SELECT id FROM cubicles WHERE id = $1", [
    cubicle_id,
  ]);
  if (result.rowCount === 0) {
    throw new Error(`Cubicle ${cubicle_id} does not exist`);
  }
}

export const cubicleEventHandler = async (event: any) => {
  try {
    const dbClient = await getClient();
    await ensureCubicleExists(dbClient, event.cubicle_id);
    await dbClient.query(
      "INSERT INTO cubicle_events (cubicle_id, occupied, toilet_roll_percentage, timestamp) VALUES ($1, $2, $3, CURRENT_TIMESTAMP)",
      [event.cubicle_id, event.occupied, event.toilet_roll_percentage],
    );
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
    return {
      status: "error",
      message: error instanceof Error ? error.message : String(error),
    };
  }
};

export const cubicleStateHandler = async (event: any) => {
  try {
    const dbClient = await getClient();
    await ensureCubicleExists(dbClient, event.cubicle_id);
    await dbClient.query(
      "INSERT INTO cubicle_states (cubicle_id, occupied, toilet_roll_percentage) VALUES ($1, $2, $3) ON CONFLICT (cubicle_id) DO UPDATE SET occupied = $2, toilet_roll_percentage = $3, updated_at = CURRENT_TIMESTAMP",
      [event.cubicle_id, event.occupied, event.toilet_roll_percentage],
    );
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
    return {
      status: "error",
      message: error instanceof Error ? error.message : String(error),
    };
  }
};

// Main handler function that AWS Lambda will invoke
export const handler = async (event: any) => {
  console.log("Received event:", JSON.stringify(event, null, 2));

  // For IoT Core messages, the event structure is the message payload
  // Determine which handler to use based on the event data
  try {
    // Check if this is a state update or event
    if (event.cubicle_id !== undefined) {
      // If we have cubicle data, process both state and event
      const stateResult = await cubicleStateHandler(event);
      const eventResult = await cubicleEventHandler(event);

      return {
        statusCode: 200,
        body: JSON.stringify({
          state: stateResult,
          event: eventResult,
        }),
      };
    }

    // Generic handler for testing or other message types
    console.log("Event processed (no cubicle_id found)");
    return {
      statusCode: 200,
      body: JSON.stringify({ message: "Event received", event }),
    };
  } catch (error) {
    console.error("Error processing event:", error);
    return {
      statusCode: 500,
      body: JSON.stringify({
        error: error instanceof Error ? error.message : String(error),
      }),
    };
  }
};
