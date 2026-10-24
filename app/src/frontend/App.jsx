import './App.css';
import {get_week} from './util/dates';

const DateList = () => {
  const today = new Date();
  const week = get_week()
  return(
    <ul>
      {week.map((day, i) => <li key={i}>
          {day.toDateString().split(" ").slice(0,-1).join(" ")}
        </li>)}
    </ul>
  )
}


const App = () => {
  return <>
    <DateList/>
  </>
}

export default App
