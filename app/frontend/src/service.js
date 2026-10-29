import axios from 'axios'
import { today, get_week } from './util/dates.js'

const API_BASE_URL = '/api'

export const get_menus = (isodate, meal) => {
  if (!isodate || !meal) {
    throw 'Not allowed to query the backend without search parameters'
  }
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
  return axios.get(`${API_BASE_URL}/dish?query=${search}&from_date=${today()}`).then((resp) => resp.data)
}

export const get_cached_dishes = (isodate) => {
  if (!isodate) {
    throw 'Not allowed to query the backend without search parameters'
  }
  const week = get_week(0, isodate)
  const [from_date, to_date] = [week[0], week[week.length - 1]]
  const url = `${API_BASE_URL}/menu-range?from_date=${from_date}&to_date=${to_date}`
  return axios.get(url)
    .then(resp => resp.data)
}