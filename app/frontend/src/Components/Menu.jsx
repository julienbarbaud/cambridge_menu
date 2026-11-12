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
  const GLIDE_SECONDS = 0.8
  const MU = 1/100  // spring constant for hand-made scrolling animation
  const root = document.documentElement

  const handle_college_menu_click = (event) => {
    const newHash = selected ? '' : `#${encodeURIComponent(event.currentTarget.getAttribute('college_menu_id'))}`
    navigate(`${location.pathname}${location.search}${newHash}`, { replace: true })
  }


  useEffect(() => {
    if (!selected) return
    const el = document.getElementById(menu_id)
    if (!el) return

    const start_x = el.getBoundingClientRect().top
    const dampened_spring_motion = t => (1 + MU * t) * start_x * Math.exp(-MU * t)
    const glide_ms = GLIDE_SECONDS * 1000

    const scroll_by = (delta) => {
      const max_y = Math.max(0, root.scrollHeight - window.innerHeight)
      const y = Math.min(Math.max(window.scrollY + delta, 0), max_y)
      if (Math.abs(y - window.scrollY) >= 0.5) window.scrollTo({ top: y, behavior: 'instant' })
    }

    const rows = ['t,dt,x_before,moved_since_last_write,scrollY,error']   // debug, see below
    let frame, start_time = null, last_now = null, last_after = start_x

    const step = (now) => {
      start_time ??= now
      const t = now - start_time
      const dt = last_now === null ? 0 : now - last_now
      last_now = now

      const x = el.getBoundingClientRect().top
      const error = x - dampened_spring_motion(t)
      rows.push([t, dt, x, x - last_after, window.scrollY, error].map(v => v.toFixed(1)).join(','))

      if (t < glide_ms) {
        scroll_by(error)        // only scroll toward the top, never back
        frame = requestAnimationFrame(step)
      } else {
        scroll_by(x)                            // land exactly on the top
        console.log(rows.join('\n'))
      }
      last_after = el.getBoundingClientRect().top
    }
    frame = requestAnimationFrame(step)

    const stop = () => cancelAnimationFrame(frame)
    window.addEventListener('wheel', stop, { passive: true })
    window.addEventListener('touchstart', stop, { passive: true })
    window.addEventListener('keydown', stop)
    return () => {
      stop()
      window.removeEventListener('wheel', stop)
      window.removeEventListener('touchstart', stop)
      window.removeEventListener('keydown', stop)
    }
  }, [selected, menu_id])

  // useEffect(() => {
  //   if (!selected) return
  //   const el = document.getElementById(menu_id)
  //   if (!el) return

  //   let frame
  //   let last_now = null
  //   let start_t = null
  //   let last_x = el.getBoundingClientRect().top
  //   const start_x = last_x
  //   const dampened_spring_motion = t => (1 + MU * t) * start_x * Math.exp(-MU*t)
  //   const step = (now) => {
  //     start_t ??= now
  //     const t = now - start_t
  //     const dt = last_now === null ? 0 : now - last_now
  //     last_now = now

  //     const beforeTop = el.getBoundingClientRect().top
  //     const beforeScroll = window.scrollY

  //     const target = dampened_spring_motion(t + dt)
  //     const dx = target - beforeTop
  //     // the page is short while cards collapse and expand, and iOS accepts a scroll past its end
  //     // (rubber-bands it for a frame, then springs back), so never ask for more than exists
  //     const viewport_h = Math.max(window.innerHeight, root.clientHeight)   // the larger one: conservative
  //     const max_y = Math.max(0, root.scrollHeight - viewport_h)
  //     const y = Math.min(Math.max(window.scrollY + (beforeTop - target), 0), max_y)
  //     if (Math.abs(y - window.scrollY) >= 0.5) window.scrollTo({ top: y, behavior: 'instant' })
  //     // window.scrollBy({
  //     //   top: -dx,
  //     //   behavior: 'instant'
  //     // })

  //     const afterTop = el.getBoundingClientRect().top
  //     const afterScroll = window.scrollY

  //     // Log every fourth frame to keep the console manageable
  //     if (Math.round(t / 16) % 4 === 0) {
  //       console.log({
  //         time: t.toFixed(1),
  //         target: target.toFixed(2),
  //         beforeTop: beforeTop.toFixed(2),
  //         afterTop: afterTop.toFixed(2),
  //         requestedScroll: (-dx).toFixed(2),
  //         actualScroll: (afterScroll - beforeScroll).toFixed(2),
  //         remainingError: (target - afterTop).toFixed(2),
  //         scrollY: afterScroll,
  //         max: document.documentElement.scrollHeight - window.innerHeight
  //       })
  //     }

  //     frame = requestAnimationFrame(step)
  //   }
  //   frame = requestAnimationFrame(step)

  //   const stop = () => cancelAnimationFrame(frame)
  //   const stop_timer = setTimeout(stop, GLIDE_SECONDS * 1000)
  //   // let the user take over if they scroll themselves
  //   window.addEventListener('wheel', stop, { passive: true })
  //   window.addEventListener('touchstart', stop, { passive: true })
  //   window.addEventListener('keydown', stop)
  //   return () => {
  //     stop()
  //     clearTimeout(stop_timer)
  //     window.removeEventListener('wheel', stop)
  //     window.removeEventListener('touchstart', stop)
  //     window.removeEventListener('keydown', stop)
  //   }
  // }, [selected, menu_id])

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