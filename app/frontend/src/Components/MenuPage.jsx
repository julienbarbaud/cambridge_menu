import { DateList } from './Selectors'
import { MealList } from './Selectors'
import { MenuList } from './Menu'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { today, get_date_string } from '../util/dates'
import './MenuPage.css'

export const MenuPage = () => {
  const default_date = today()
  const navigate = useNavigate()
  // choosing to rely on search params rather than state so the query state can be saved in histroy, shared, etc...
  const [search_params] = useSearchParams(`?meal_type=lunch&date=${default_date}`)
  const create_setter = (field_name) => (val) => {
    const new_params = new URLSearchParams(search_params)
    new_params.set(field_name, val)

    navigate(
      {
        pathname: location.pathname,
        search: `?${new_params.toString()}`,
        hash: location.hash,
      },
      { replace: true }
    )
  }
  const chosen_date = search_params.get('date')
  const set_chosen_date = create_setter('date')
  const chosen_meal = search_params.get('meal_type')
  const set_chosen_meal = create_setter('meal_type')

  // //auto scroll to correct college when the date or meal changes (to do later if we keep selectors sticky on top)
  // useEffect(() => {
  //   if (location.hash) {
  //     const id = location.hash.replace('#', '')

  //     // requestAnimationFrame ensures React has finished painting the DOM
  //     requestAnimationFrame(() => {
  //       const element = document.getElementById(id)
  //       if (element) {
  //         element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  //       }
  //     })
  //   }
  // }, [chosen_date, chosen_meal])




  return(
    <div>
      <DateList chosen_date={chosen_date} set_date={set_chosen_date}/>
      <h2 id="date-marker">{get_date_string(chosen_date)}</h2>
      <MealList chosen_meal={chosen_meal} set_chosen_meal={set_chosen_meal}/>
      <MenuList date={chosen_date} meal={chosen_meal}/>
    </div>
  )
}