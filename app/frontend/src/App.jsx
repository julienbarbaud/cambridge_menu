import './App.css'
import { Link, Routes, Route, useLocation, useNavigate } from 'react-router-dom'
import { MenuPage } from './Components/MenuPage'
import { SearchPage } from './Components/SearchPage'
import { Footer } from './Components/Footer'



const App = () => {
  const location = useLocation()
  const navigate = useNavigate()

  const on_search_page = location.pathname.startsWith('/search')
  const handle_back_button_click = () => {
    navigate(-1)
  }

  return(
    <>
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
            <Link id="stp-button" className='icon-button' to="/search/stp">da S.T.P.</Link>
          </div>
        </div>
        <Routes>
          <Route path='/' Component={MenuPage}/>
          <Route path='/search' Component={SearchPage}/>
          <Route path='/search/stp' element={<SearchPage initial_search="sticky toffee"/>}/>
        </Routes>
      </div>
      <Footer/>
    </>
  )
}

export default App

// TODO:
// fix back navigation of search page
// fetching week dishes in bulk for smoother UI updates
// error handling (including message on empty search results)
// styling of search page?