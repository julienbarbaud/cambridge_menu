import { get_week, short_isoformat } from '../util/dates.js'
import './Selectors.css'

export const DateList = ({ chosen_date, set_date }) => {
  //const today = new Date()
  const week = get_week()
  return(
    <ul className='selector-list' id='date-list'>
      {week.map(day => <DateSelector key={day.toISOString()} chosen_date={chosen_date} date={day} set_date={set_date}/>)}
    </ul>
  )
}


export const DateSelector = ({ date, chosen_date, set_date }) => {
  const day = date.toDateString().split(' ')[0]
  const formatted_date = `${date.getMonth()}/${date.getDate()}`
  const handle_click = () => {
    console.log(date.toDateString())
    set_date(short_isoformat(date))
  }
  return(
    <li>
      <button className={short_isoformat(date)===chosen_date ? 'selected' : ''} onClick={handle_click}>
        <p className='day-label'>{day}</p>
        <p className='date-label'>{formatted_date}</p>
      </button>
    </li>
  )
}

export const MealList = ({ chosen_meal, set_chosen_meal }) => {
  const meals = ['Brunch', 'Lunch', 'Dinner']
  return(
    <div id='meal-list' className='selector-list'>
      {meals.map(meal => <MealSelector
        key={meal}
        meal_name={meal}
        chosen_meal={chosen_meal}
        set_meal={set_chosen_meal}
      />)}
    </div>
  )
}

const MealSelector = ({ meal_name, chosen_meal, set_meal }) => {
  const handle_click = () => set_meal(meal_name.toLowerCase())
  const class_name = `meal-selector ${chosen_meal === meal_name.toLowerCase() ? 'selected' : ''}`
  return(
    <button className={class_name} onClick={handle_click}>
      {meal_name}
    </button>
  )
}