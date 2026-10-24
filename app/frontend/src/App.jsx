import './App.css'
import { DateList, MealList } from './Components/Selectors'
import { useSearchParams } from 'react-router-dom'
import { MenuList  } from './Components/Menu'



const App = () => {
  // choosing to rely on search params rather than state so the query state can be saved in histroy, shared, etc...
  const [search_params, set_search_params] = useSearchParams('?meal_type=lunch&date=2026-10-22')
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
    <div className="page">
      <h1 id='site-header'>Cambr'eats</h1>
      <h4 id='site-subheader'>All the colleges' menus, in one place</h4>
      <DateList chosen_date={chosen_date} set_date={set_chosen_date}/>
      <MealList chosen_meal={chosen_meal} set_chosen_meal={set_chosen_meal}/>
      <MenuList date={chosen_date} meal={chosen_meal}/>
    </div>
  )
}

export default App

// TODO:
// styling
// search bar + sticky toffee pudding button
// error handling (including message on empty search results)