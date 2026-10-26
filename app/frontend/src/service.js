import axios from 'axios'

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
  return axios.get(`${API_BASE_URL}/dish?query=${search}`).then((resp) => resp.data)
}