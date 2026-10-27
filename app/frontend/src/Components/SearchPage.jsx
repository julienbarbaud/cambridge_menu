import { useEffect, useState } from 'react'
import { group_dishes_by } from '../util/helper'
import { get_search_matches } from '../service'
import { get_short_slash_date } from '../util/dates.js'
import { Link } from 'react-router-dom'
import './SearchPage.css'

export const SearchPage = ({ initial_search }) => {
  const [results, set_results] = useState([])
  const [search, set_search] = useState(initial_search ? initial_search : '')

  useEffect(() => {
    if (search.length<2) return
    // the ignore flag is here to avoid stale request results
    let ignore = false
    get_search_matches(search)
      .then(res => {
        if (!ignore) {
          set_results(res)
        }
      })
    // cleanup function: if search is updated again before the request completes, ignore it (it's outdated)
    return () => { ignore = true }
  }, [search])

  const handle_search_change = (event) => {
    set_search(event.target.value)
    if (event.target.value.length < 2) set_results([])
  }

  const handle_submit_form = (event) => {
    event.preventDefault()
    console.log(search)
    get_search_matches(search).then(res => set_results(res))
  }

  return(
    <>
      <form onSubmit={handle_submit_form}>
        <label htmlFor="search-bar">Search: </label>
        <input type="text" id="search-bar" name="search=bar" value ={search} onChange={handle_search_change}></input>
      </form>
      <SearchResults results={results}/>
    </>
  )
}

const SearchResults = ({ results }) => {
  if (!results || results.length === 0) return null
  const college_matches = group_dishes_by('college', results)
  return(<ul>
    {Object.entries(college_matches).map(([college, results]) => <CollegeResults college={college} results={results}/>)}
  </ul>)
}

const CollegeResults = ({ college, results }) => {

  return(<div>
    <h2>{college}</h2>
    <ul className='college-results-list'>
      {results.map(dish => <li key={dish._id}>
        <Link className="meal-link" to={`/?date=${dish.date}&meal_type=${dish.meal_type}`}>
          <b>{get_short_slash_date(dish.date)}</b> ({dish.meal_type}): {dish.name}
        </Link>
      </li>)}
    </ul>
  </div>)
}