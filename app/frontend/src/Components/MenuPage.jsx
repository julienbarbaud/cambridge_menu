import { DateList } from './Selectors'
import { MealList } from './Selectors'
import { MenuList } from './Menu'
import { useSearchParams } from 'react-router-dom'
import { today, get_date_string } from '../util/dates'
import './MenuPage.css'

export const MenuPage = () => {
  const default_date = today()
  // choosing to rely on search params rather than state so the query state can be saved in histroy, shared, etc...
  const [search_params, set_search_params] = useSearchParams(`?meal_type=lunch&date=${default_date}`)
  const create_setter = (field_name) => (val) => {
    const new_params = new URLSearchParams(search_params)
    new_params.set(field_name, val)
    set_search_params(new_params)
  }
  const chosen_date = search_params.get('date')
  const set_chosen_date = create_setter('date')
  const chosen_meal = search_params.get('meal_type')
  const set_chosen_meal = create_setter('meal_type')

  return(
    <div>
      <DateList chosen_date={chosen_date} set_date={set_chosen_date}/>
      <h2 id="date-marker">{get_date_string(chosen_date)}</h2>
      <MealList chosen_meal={chosen_meal} set_chosen_meal={set_chosen_meal}/>
      <MenuList date={chosen_date} meal={chosen_meal}/>
    </div>
  )
}