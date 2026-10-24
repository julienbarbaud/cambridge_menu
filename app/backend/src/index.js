import express from "express"
import { Dish } from "./schemas.js"
import { connect_db } from "./db.js"
import { validate_isodate, validate_meal_type } from "./validators.js"

const app = express()
connect_db()

app.use(express.json())

app.get("/api", (request, response) => {
    return response.send("backend api serving menus of cambridge colleges")
})

app.get("/api/dish", (request, response) => {
    const {date: isodate, meal_type} = request.query
    console.log(isodate)
    const filter = {}
    if (isodate) {
        if (!validate_isodate()) {
            return response.status(400).json({error: `invalid isoformat date ${isodate}`})
        }
        filter.date = isodate
    }
    if (meal_type) {
        let query
        if (Array.isArray(meal_type)) {
            const unsupported_meal_type = meal_type.find((meal) => !validate_meal_type(meal))
            if (unsupported_meal_type){
                //if one meal in the list is invalid, throw error
                return response.status(400).json({error: `unknown meal type ${unsupported_meal_type}`})
            }
            query = {$in: meal_type}
        }
        else {
            if (!validate_meal_type(meal_type)) {
                return response.status(400).json({error: `unknown meal type ${meal_type}`})
            }
            query = meal_type
        }
        filter.meal_type = query
    }
    console.log(filter)
    Dish.find(filter).then((data) =>{
        return response.json(data)
    })
})

app.get("/api/menus/:isodate", (request, response) => {
    const query_date = new Date(request.params.isodate)
    Dish.find({date : query_date})
        .then((data) => response.json(data))
})

const PORT = 3001
app.listen(PORT, () => {
    console.log("server running on port ", PORT)
})