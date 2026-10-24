import axios from 'axios'
import { short_isoformat } from './util/dates.js'

const API_BASE_URL = '/api'

export const get_menus = (date, meal) => {
  if (!date || !meal) {
    throw 'Not allowed to query the backend without search parameters'
  }
  const isodate = short_isoformat(new Date(date))
  meal = meal.toLowerCase()
  const meal_query_param = ['brunch', 'breakfast'].includes(meal) ?
    'meal_type=brunch&meal_type=breakfast' :
    `meal_type=${meal}`
  const url = `${API_BASE_URL}/dish?date=${isodate}&${meal_query_param}`
  return axios.get(url).then(resp => {
    return resp.data
  })
}

export const get_search_matches = (search) => {
  return axios.get(`${API_BASE_URL}/dish?query=${search}`).then((resp) => resp.data)
}