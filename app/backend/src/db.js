import mongoose from "mongoose";
import { MONGODB_URI } from "./constants.js";

export const connect_db = () => mongoose.connect(MONGODB_URI, {family: 4})