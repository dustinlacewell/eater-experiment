import curses

from eaters.app import CursesApp

screen = curses.initscr()

app = CursesApp(screen)
app.run()
