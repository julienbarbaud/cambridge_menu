const shift_days = (date, days) => {
  const shifted = new Date(date)
  shifted.setDate(shifted.getDate() + days)
  return shifted
}

export const get_week = () => {
  const today = new Date()
  const first_day = shift_days(today, -today.getDay() + 1)
  const week = []
  for (let i = 0; i<7; i++){
    const day = shift_days(first_day, i)
    week.push(day)
  }
  return week
}

export const short_isoformat = (date) => {
  return date.toISOString().split('T')[0]
}