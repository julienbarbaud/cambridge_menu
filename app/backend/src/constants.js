import dotenv from "dotenv"

dotenv.config({path: "../../.env"})

export const MONGODB_URI = process.env.MONGODB_DB_URI
export const MEAL_TYPES = ["breakfast", "brunch", "lunch", "dinner"]