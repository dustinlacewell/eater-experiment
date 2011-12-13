import traceback
import curses


from eaters.app import CursesApp

screen = curses.initscr()

app = CursesApp(screen)
try:
    app.start()
except Exception, e:
    curses.nocbreak()
    curses.echo()
    curses.endwin()
    traceback.print_exc()
