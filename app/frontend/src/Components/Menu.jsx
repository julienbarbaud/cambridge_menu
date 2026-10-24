import { get_menus } from '../service.js'
import { useState, useEffect } from 'react'
import { group_dishes_by } from '../util/helper.js'
import './Menu.css'

export const MenuList = ({ date, meal }) => {
  const [dishes, set_dishes] = useState([])
  useEffect(() => {
    if (date===null) return
    get_menus(date, meal)
      .then(res => set_dishes(res))
  }, [date, meal])
  if (date === null) return
  console.log(`dishes: ${dishes}`)
  const college_menus = group_dishes_by('college', dishes)
  return(
    <ul id='menu-list'>
      {Object.entries(college_menus).map(
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
      {Object.entries(courses).map(([name, courses]) => <CourseList course_name={name} courses={courses}/>)}
    </div>
  )
}

const CourseList = ({ course_name, courses }) => {
  return(
    <div className="course-section">
      <h3>{course_name.toUpperCase()}</h3>
      <ul className='course-list'>
        {courses.map(course => <li className='course-item'>{course.name}</li>)}
      </ul>
    </div>
  )
}