import curses

from eaters.app import App

screen = curses.initscr()

app = CursesApp(screen)
app.run()
