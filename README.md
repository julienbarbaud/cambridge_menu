# Cambr'eats: a cambridge menu
*All the colleges buttery menus, in one place*


## Project structure:
- app (js webapp, hosted on Render)
  - backend (express)
  - frontend (React, served as static files of the backend on the Render server)
- scraper (python script to scrape menus from colleges and upload to mongodb, running on a schedule via github actions)

