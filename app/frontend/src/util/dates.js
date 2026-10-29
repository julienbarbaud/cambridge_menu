import { addWeeks, addDays, startOfToday, startOfWeek, format, parseISO } from 'date-fns'

export const get_week = (week_shift=0, iso_center_day=null) => {
  let center_day
  if (iso_center_day !== null) center_day = parseISO(iso_center_day)
  else center_day = startOfToday()

  const shifted_center = addWeeks(center_day, week_shift)
  const first_week_day = startOfWeek(shifted_center, { weekStartsOn: 1 })
  const week = []
  for (let i = 0; i<7; i++){
    const day = addDays(first_week_day, i)
    week.push(get_isoformat(day))
  }
  return week
}

const get_isoformat = (date) => format(date, 'yyyy-MM-dd')

export const get_week_day = (isodate) => format(parseISO(isodate), 'EEE')

export const get_short_slash_date = (isodate) => isodate.split('-').slice(1).join('/')

export const today = () => get_isoformat(startOfToday())

export const get_date_string = (isodate) => format(parseISO(isodate), 'EEE, MMM dd')