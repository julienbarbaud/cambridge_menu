import dotenv from "dotenv"

// Only load local .env file if we aren't in production
if (process.env.NODE_ENV !== "production") {
  dotenv.config({ path: "../../.env" });
}

export const MONGODB_URI = process.env.MONGODB_DB_URI
export const MEAL_TYPES = ["breakfast", "brunch", "lunch", "dinner"]