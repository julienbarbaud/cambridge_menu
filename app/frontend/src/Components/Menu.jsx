import { get_cached_dishes } from '../service.js'
import { useState, useEffect } from 'react'
import { group_dishes_by } from '../util/helper.js'
import { useNavigate, useLocation } from 'react-router-dom'
import './Menu.css'
import { AnimatePresence, motion } from 'framer-motion'

export const MenuList = ({ date, meal }) => {
  const [cached_dishes, set_cached_dishes] = useState([])
  const location = useLocation()
  let dishes = date && cached_dishes[date]?.[meal] || []
  const chosen_college_menu = decodeURI(location.hash).substring(1)

  // lumping brunch and breakfast together
  if (meal === 'brunch') {
    const breakfast = date && cached_dishes[date]?.['breakfast'] || []
    dishes = dishes.concat(breakfast)
  }

  useEffect(() => {
    if (!date || !meal) return
    if (date in cached_dishes) return // if result is cached, no need to fetch
    get_cached_dishes(date, meal)
      .then(res => {
        const date_groups = group_dishes_by('date', res)
        for (const date_key of Object.keys(date_groups)){
          date_groups[date_key] = group_dishes_by('meal_type', date_groups[date_key])
        }
        // in case the date is not included in the date (no meals on that date),
        // we set an empty date entry anyway to avoid an infinite loop (telling the effect not to re-fetchv)
        set_cached_dishes({ date: [], ...date_groups })
      })
  }, [date, meal, cached_dishes])


  if (date === null) return
  const college_menus = group_dishes_by('college', dishes)
  return(
    <ul id='menu-list'>
      {Object.entries(college_menus).sort((a,b) => a[0].localeCompare(b[0])).map(
        ([college, dishes]) => {
          return(<CollegeMenu
            key={college}
            college_name={college}
            dishes={dishes}
            chosen_college_menu={chosen_college_menu}
            location={location}
          />)
        }
      )}
    </ul>
  )
}

const CollegeMenu = ({ college_name, dishes, chosen_college_menu, location }) => {
  const navigate = useNavigate()
  const courses = group_dishes_by('course', dishes)
  const menu_id = `${college_name}-menu`
  const selected = chosen_college_menu === menu_id

  const handle_college_menu_click = (event) => {
    const newHash = selected ? '' : `#${encodeURIComponent(event.currentTarget.getAttribute('college_menu_id'))}`
    navigate(`${location.pathname}${location.search}${newHash}`, { replace: true })
  }

  const handle_animation_end = () => {
    const cur_element = document.getElementById(menu_id)
    cur_element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return(
    <button className="toggle-menu-button" onClick={handle_college_menu_click} college_menu_id={menu_id}>
      <div id={menu_id} className={`college-menu-card ${selected? 'selected' : 'unselected'}`}>
        <h2>{college_name}</h2>
        <AnimatePresence>
          {selected && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              style={{ overflow: 'hidden' }}
              onAnimationComplete={handle_animation_end}
              className='motion-container'
            >
              <hr className='college-separator'/>
              {Object.entries(courses).map(
                ([name, courses]) => <CourseList
                  key={name}
                  course_name={name==='null' ? 'Miscellaneous courses' : name}
                  courses={courses}
                />
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </button>
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