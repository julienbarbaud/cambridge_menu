import { useState } from 'react'
import { get_week, get_week_day, get_short_slash_date } from '../util/dates.js'
import './Selectors.css'

export const DateList = ({ chosen_date, set_date }) => {
  const [week_shift, set_week_shift] = useState(0)
  const handle_previous_click = () => {
    set_week_shift(week_shift-1)
  }
  const handle_next_click = () => {
    set_week_shift(week_shift+1)
  }

  const chosen_week = get_week(week_shift, chosen_date)

  return(<div className='date-selection-section'>
    <button id='previous-dates-button' className='date-navigation-button' onClick={handle_previous_click}/>
    <ul className='selector-list' id='date-list'>
      {chosen_week.map(day => <DateSelector
        key={day}
        chosen_date={chosen_date}
        date={day}
        set_date={set_date}
        set_week_shift={set_week_shift}
      />)}
    </ul>
    <button id='next-dates-button' className='date-navigation-button' onClick={handle_next_click}/>
  </div>
  )
}


export const DateSelector = ({ date, chosen_date, set_date , set_week_shift }) => {
  const week_day = get_week_day(date)
  const formatted_date = get_short_slash_date(date)
  const handle_click = () => {
    set_date(date)
    set_week_shift(0)
  }
  return(
    <li>
      <button className={date===chosen_date ? 'selected' : ''} onClick={handle_click}>
        <p className='day-label'>{week_day}</p>
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