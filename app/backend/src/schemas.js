import mongoose from "mongoose";

const dish_schema = new mongoose.Schema({
    name: String,
    meal_type: String,
    course: {
        type: String || null,
        default: "Unknown course",
    },
    date: String,
    college: String,
})

export const Dish = mongoose.model("Dish", dish_schema)