import './App.css'
import { Link, Routes, Route, useLocation, useNavigate } from 'react-router-dom'
import { MenuPage } from './Components/MenuPage'
import { SearchPage } from './Components/SearchPage'



const App = () => {
  const location = useLocation()
  const navigate = useNavigate()

  const on_search_page = location.pathname === '/search'
  const handle_back_button_click = () => {
    if (location.key !== 'default') navigate(-1)
    navigate('/')
  }

  return(
    <div className="page">
      <div className='top-section'>
        <div className='header-block'>
          <h1 id='site-header'>Cambr'eats</h1>
          <h4 id='site-subheader'>All the colleges' menus, in one place</h4>
        </div>
        <div id="search-section">
          {
            on_search_page
              ? <button id='back-button' className='icon-button' onClick={handle_back_button_click}>back</button>
              : <Link id='search-button' className='icon-button' to="/search">search</Link>
          }
          <Link id="stp-button" className='icon-button' to="/search?query=sticky+toffee">da S.T.P.</Link>
        </div>
      </div>
      <Routes>
        <Route path='/' Component={MenuPage}/>
        <Route path='/search' Component={SearchPage}/>
      </Routes>

    </div>
  )
}

export default App

// TODO:
// fix back navigation of search page
// fetching week dishes in bulk for smoother UI updates
// error handling (including message on empty search results)
// styling of search page?