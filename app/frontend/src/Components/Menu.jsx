import { get_cached_dishes } from '../service.js'
import { useState, useEffect } from 'react'
import { group_dishes_by } from '../util/helper.js'
import './Menu.css'

export const MenuList = ({ date, meal }) => {
  const [cached_dishes, set_cached_dishes] = useState([])
  let dishes = date && cached_dishes[date]?.[meal] || []
  // lumping brunch and breakfast together
  if (meal === 'brunch') {
    const breakfast = date && cached_dishes[date]?.['breakfast'] || []
    dishes = dishes.concat(breakfast)
  }
  console.log(dishes)

  useEffect(() => {
    if (!date || !meal) return
    if (date in cached_dishes) return // if result is cached, no need to fetch
    get_cached_dishes(date, meal)
      .then(res => {
        const date_groups = group_dishes_by('date', res)
        for (const date_key of Object.keys(date_groups)){
          date_groups[date_key] = group_dishes_by('meal_type', date_groups[date_key])
        }
        set_cached_dishes(date_groups)
      })
  }, [date, meal, cached_dishes])

  if (date === null) return
  console.log(`dishes: ${dishes}`)
  const college_menus = group_dishes_by('college', dishes)
  return(
    <ul id='menu-list'>
      {Object.entries(college_menus).sort((a,b) => a[0].localeCompare(b[0])).map(
        ([college, dishes]) => {
          return(<CollegeMenu key={college} college_name={college} dishes={dishes}/>)
        }
      )}
    </ul>
  )
}

const CollegeMenu = ({ college_name, dishes }) => {
  const courses = group_dishes_by('course', dishes)
  return(
    <div className='college-menu-card'>
      <h2>{college_name}</h2>
      <hr className='college-separator'/>
      {Object.entries(courses).map(([name, courses]) => <CourseList key={name} course_name={name==='null' ? 'Miscellaneous courses' : name} courses={courses}/>)}
    </div>
  )
}

const CourseList = ({ course_name, courses }) => {
  return(
    <div className="course-section">
      <h3>{course_name.toUpperCase()}</h3>
      <ul className='course-list'>
        {courses.map(course => <li key={course._id} className='course-item'>{course.name}</li>)}
      </ul>
    </div>
  )
}