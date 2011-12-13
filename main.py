import traceback
import curses


from eaters.app import CursesApp

screen = curses.initscr()
app = CursesApp(screen)
try:
    app.start()
except Exception, e:
    try:
        curses.nocbreak()
        curses.echo()
        curses.endwin()
    except:
        pass
    traceback.print_exc()
try:
    curses.nocbreak()
    curses.echo()
    curses.endwin()
except:
    pass

