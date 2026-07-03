/**
 * MongoDB initialisation script — runs once on first container start.
 *
 * Creates the application database, a dedicated user with read/write
 * access, and pre-creates collections with indexes.
 *
 * The app user is stored in the target database (not admin), so the
 * backend must use ``authSource=responsible_rag`` in the MONGO_URI.
 */

// Switch to the application database (creates it if it doesn't exist)
const appDb = process.env.MONGO_INITDB_DATABASE || "responsible_rag";
db = db.getSiblingDB(appDb);

// Create the application user (idempotent — fails silently if exists)
db.createUser({
  user: process.env.MONGO_APP_USER || "rag",
  pwd: process.env.MONGO_APP_PASSWORD || "ragpassword",
  roles: [{ role: "readWrite", db: appDb }],
});

// Pre-create collections with indexes
db.createCollection("users");
db.createCollection("profiles");
db.createCollection("consent");
db.createCollection("conversations");
db.createCollection("messages");
db.createCollection("feedback");

// ── Indexes ──────────────────────────────────────────────────────────────
db.users.createIndex({ email: 1 }, { unique: true });
db.profiles.createIndex({ user_id: 1 }, { unique: true });
db.consent.createIndex({ user_id: 1 }, { unique: true });
db.conversations.createIndex({ user_id: 1, updated_at: -1 });
db.messages.createIndex({ conversation_id: 1, created_at: 1 });
db.feedback.createIndex({ created_at: -1 });
