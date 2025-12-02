import { Pool, PoolClient } from "pg";

// Store database configuration
const dbConfig = {
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD || process.env.DB_USER,
  database: process.env.DB_NAME,
  ssl: {
    rejectUnauthorized: false,
  },
  // Connection pool settings optimized for Lambda
  max: 1, // Lambda containers are single-threaded, so 1 connection per container is optimal
  min: 0, // Allow connections to be released when idle
  idleTimeoutMillis: 120000, // 2 minutes - keep connection alive between invocations
  connectionTimeoutMillis: 10000, // 10 seconds
  allowExitOnIdle: true, // Allow Lambda to exit cleanly
};

// Create pool outside handler to reuse connections across invocations
let pool: Pool | null = null;

function getPool(): Pool {
  if (!pool) {
    console.log("[getPool] Creating new connection pool");
    pool = new Pool(dbConfig);

    // Handle pool errors to prevent crashes
    pool.on("error", (err) => {
      console.error("[Pool] Unexpected error on idle client", err);
      // Don't reset pool here - let it try to recover
    });

    // Log connection events for debugging
    pool.on("connect", () => {
      console.log("[Pool] New client connected");
    });

    pool.on("remove", () => {
      console.log("[Pool] Client removed from pool");
    });
  }
  return pool;
}

// Prepared statements will be created automatically on first use by pg library
// No need to pre-prepare them

async function ensureCubicleExists(
  client: PoolClient,
  cubicle_id: number,
): Promise<void> {
  try {
    const result = await client.query({
      name: "check_cubicle",
      text: "SELECT id FROM cubicles WHERE id = $1",
      values: [cubicle_id],
    });

    if (result.rowCount === 0) {
      throw new Error(`Cubicle ${cubicle_id} does not exist`);
    }
  } catch (error) {
    console.error(
      `[ensureCubicleExists] Error checking cubicle ${cubicle_id}:`,
      error,
    );
    throw error;
  }
}

async function cubicleEventHandler(event: any, client: PoolClient) {
  try {
    console.log(
      `[cubicleEventHandler] Starting for cubicle_id: ${event.cubicle_id}`,
    );

    const result = await client.query({
      name: "insert_event",
      text: "INSERT INTO cubicle_events (cubicle_id, occupied, toilet_roll_percentage, timestamp) VALUES ($1, $2, $3, CURRENT_TIMESTAMP)",
      values: [event.cubicle_id, event.occupied, event.toilet_roll_percentage],
    });

    console.log(
      `[cubicleEventHandler] Event inserted successfully. Rows affected: ${result.rowCount}`,
    );
    return { status: "ok" };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error("[cubicleEventHandler] Error:", errorMessage);
    return {
      status: "error",
      message: errorMessage,
    };
  }
}

async function cubicleStateHandler(event: any, client: PoolClient) {
  try {
    console.log(
      `[cubicleStateHandler] Starting for cubicle_id: ${event.cubicle_id}`,
    );

    const result = await client.query({
      name: "upsert_state",
      text: "INSERT INTO cubicle_states (cubicle_id, occupied, toilet_roll_percentage) VALUES ($1, $2, $3) ON CONFLICT (cubicle_id) DO UPDATE SET occupied = $2, toilet_roll_percentage = $3, updated_at = CURRENT_TIMESTAMP",
      values: [event.cubicle_id, event.occupied, event.toilet_roll_percentage],
    });

    console.log(
      `[cubicleStateHandler] State upserted successfully. Rows affected: ${result.rowCount}`,
    );
    return { status: "ok" };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error("[cubicleStateHandler] Error:", errorMessage);
    return {
      status: "error",
      message: errorMessage,
    };
  }
}

// Process a single event with database operations
async function processEvent(event: any) {
  const currentPool = getPool();
  const client = await currentPool.connect();

  try {
    // Begin transaction for atomicity
    await client.query("BEGIN");

    // Validate cubicle exists
    await ensureCubicleExists(client, event.cubicle_id);

    // Process both state and event updates
    const stateResult = await cubicleStateHandler(event, client);
    const eventResult = await cubicleEventHandler(event, client);

    // Commit transaction
    await client.query("COMMIT");

    console.log("Transaction committed successfully");
    return {
      statusCode: 200,
      body: JSON.stringify({
        state: stateResult,
        event: eventResult,
      }),
    };
  } catch (error) {
    // Rollback on error
    try {
      await client.query("ROLLBACK");
      console.log("Transaction rolled back");
    } catch (rollbackError) {
      console.error("Error during rollback:", rollbackError);
    }

    console.error("Error processing event:", error);
    return {
      statusCode: 500,
      body: JSON.stringify({
        error: error instanceof Error ? error.message : String(error),
      }),
    };
  } finally {
    // Always release the client back to the pool
    client.release();
  }
}

// Main handler function that AWS Lambda will invoke
export const handler = async (event: any) => {
  console.log("Received event:", JSON.stringify(event, null, 2));
  console.log("DB Config:", {
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    database: process.env.DB_NAME,
  });

  try {
    // Handle single event
    if (event.cubicle_id !== undefined) {
      console.log(`Processing event for cubicle_id: ${event.cubicle_id}`);
      return await processEvent(event);
    }

    // Handle batch of events (if IoT sends multiple messages)
    if (Array.isArray(event.Records)) {
      console.log(`Processing batch of ${event.Records.length} events`);
      const results = await Promise.all(
        event.Records.map(async (record: any) => {
          const payload =
            typeof record.body === "string"
              ? JSON.parse(record.body)
              : record.body;
          return processEvent(payload);
        }),
      );

      return {
        statusCode: 200,
        body: JSON.stringify({
          message: "Batch processed",
          results,
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
    console.error(
      "Error stack:",
      error instanceof Error ? error.stack : "No stack trace",
    );
    return {
      statusCode: 500,
      body: JSON.stringify({
        error: error instanceof Error ? error.message : String(error),
      }),
    };
  }
};

// Graceful shutdown handler for Lambda
export const shutdown = async () => {
  if (pool) {
    console.log("[shutdown] Closing connection pool");
    await pool.end();
    pool = null;
  }
};
