import { MEAL_TYPES } from "./constants.js"

export const validate_isodate = isodate => {
  try {
    const date = new Date(isodate)
    return true
  }
  catch {
    return false
  }
}

export const validate_meal_type = (meal_type) => {
  return MEAL_TYPES.includes(meal_type)
}