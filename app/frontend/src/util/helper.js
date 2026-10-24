export const group_dishes_by = (key, dishes, debug=false) => {
  const groups = {}
  if (debug) console.log(`dishes in fun: ${dishes}`)
  for (const dish of dishes) {
    if (debug){
      console.log(`dish in fun: ${dish}`)
    }
    if (dish[key] in groups){
      groups[dish[key]].push(dish)
    }
    else {
      groups[dish[key]] = [dish]
    }
  }
  console.log(`groups: ${groups}`)
  return groups
}