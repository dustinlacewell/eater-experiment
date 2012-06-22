import pudb
import heapq, time, random, sys, cStringIO
import curses, _curses, urwid
from curses import ascii
from code import InteractiveConsole, InteractiveInterpreter
from cmd2 import Cmd

from urwid.display_common import UNPRINTABLE_TRANS_TABLE, AttrSpec
from urwid.main_loop import MainLoop
from urwid.curses_display import Screen
from urwid.compat import bytes, chr2, B, bytes3, PYTHON3
from urwid.util import move_next_char, move_prev_char


class EaterCommandController(Cmd):
    def __init__(self, app, *args, **kwargs):
        Cmd.__init__(self, *args, **kwargs)
        self.app = app
        
    def do_py(self, arg):  
        '''
        py <command>: Executes a Python command.
        py: Enters interactive Python mode.
        End with ``Ctrl-D`` (Unix) / ``Ctrl-Z`` (Windows), ``quit()``, '`exit()``.
        Non-python commands can be issued with ``cmd("your command")``.
        Run python code from external files with ``run("filename.py")``
        '''
        self.pystate['self'] = self
        arg = arg.parsed.raw[2:].strip()
        localvars = (self.locals_in_py and self.pystate) or {}
        interp = InteractiveConsole(locals=localvars)
        interp.runcode('import sys, os;sys.path.insert(0, os.getcwd())')
        if arg.strip():
            try:
                interp.runcode(arg)
            except Exception, e:
                self.stdout.write("Exception: %s\n" % e.message)


class BufferScreen(Screen):
    def __init__(self):
        super(BufferScreen, self).__init__()
        self.ch_bufs = dict() # character buffers
        self.co_bufs = dict() # color buffers
        self.dirty = True
        self.messy = True
        self.doclear = True

    def refresh(self):
        self.s.refresh()

    def clear_ch_bufs(self):
        for buffer in self.ch_bufs.values():
            buffer.clear()

    def clear_co_bufs(self):
        for buffer in self.co_bufs.values():
            buffer.clear()

    def clear_all_bufs(self):
        self.clear_ch_bufs()
        self.clear_co_bufs()

    def render_ch_buffer(self):
        buffer = dict()
        for buf in self.ch_bufs.values():
            if buf.keys():
                buffer.update(buf)
        return buffer

    def render_co_buffer(self):
        buffer = dict()
        for buf in self.co_bufs.values():
            if buf.keys():
                buffer.update(buf)
        return buffer

    def chbuf(self, name):
        if name in self.ch_bufs:
            return self.ch_bufs[name]
        else:
            newbuf = dict()
            self.ch_bufs[name] = newbuf
            return newbuf

    def cobuf(self, name):
        if name in self.co_bufs:
            return self.co_bufs[name]
        else:
            newbuf = dict()
            self.co_bufs[name] = newbuf
            return newbuf


    def start(self):
        super(BufferScreen, self).start()
        curses.init_pair(1, curses.COLOR_WHITE, -1)
        curses.init_pair(2, curses.COLOR_BLUE, -1)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_GREEN)
        curses.init_pair(4, curses.COLOR_GREEN, -1)

    def draw_buffer(self):
        cp = curses.color_pair(1)
        for coord, tile in self.ch_bufs['main'].items():
            y, x = coord
            self.s.addch(y, x, ord(tile.char), cp)
        self.clear_ch_bufs()

    def draw_colors(self):
        for coord, color in self.co_bufs['main'].items():
            y, x = coord
            self.s.chgat(y, x, 1, curses.color_pair(color))
        self.clear_co_bufs()

    def draw_screen(self, (cols, rows), r ):
        """Paint screen with rendered canvas."""
        assert self._started
        
        assert r.rows() == rows, "canvas size and passed size don't match"
    
        y = -1
        for row in r.content():
            y += 1
            try:
                self.s.move( y, 0 )
            except _curses.error:
                # terminal shrunk? 
                # move failed so stop rendering.
                return
            
            first = True
            lasta = None
            nr = 0
            for a, cs, seg in row:
                if not [char for char in seg if char != chr(0)]:
                    break
                # bail = False
                # for char in seg:
                #     if char == chr(0):
                #         break
                # if bail:
                #     break
                if cs != 'U':
                    seg = seg.translate(UNPRINTABLE_TRANS_TABLE)
                    assert isinstance(seg, bytes)

                if first or lasta != a:
                    self._setattr(a)
                    lasta = a
                try:
                    if cs in ("0", "U"):
                        for i in range(len(seg)):
                            self.s.addch( 0x400000 +
                                ord(seg[i]) )
                    else:
                        assert cs is None
                        if PYTHON3:
                            assert isinstance(seg, bytes)
                            self.s.addstr(seg.decode('utf-8'))
                        else:
                            self.s.addstr(seg)
                except _curses.error:
                    # it's ok to get out of the
                    # screen on the lower right
                    if (y == rows-1 and nr == len(row)-1):
                        pass
                    else:
                        # perhaps screen size changed
                        # quietly abort.
                        return
                nr += 1

        self.keep_cache_alive_link = r

    def draw_cursor(self, r):
        if r.cursor is not None:
            x,y = r.cursor
            self._curs_set(1)
            try:
                self.s.move(y,x)
            except _curses.error:
                pass
        else:
            self._curs_set(0)
            self.s.move(0,0)
        


class CursesBufferLoop(MainLoop):
    def __init__(self, *args, **kwargs):
        super(CursesBufferLoop, self).__init__(*args, **kwargs)

    def draw_screen(self):
        """
        Renter the widgets and paint the screen.  This function is
        called automatically from run() but may be called additional
        times if repainting is required without also processing input.
        """
        if not self.screen_size:
            self.screen_size = self.screen.get_cols_rows()

        canvas = self._topmost_widget.render(self.screen_size, focus=True)
        cy, cx = self.screen.s.getyx()
        if self.screen.dirty:
            self.screen.draw_screen(self.screen_size, canvas)
        if self.screen.messy:
            self.screen.draw_buffer()
            self.screen.draw_colors()
        self.screen.s.move(cy, cx)
        if self.screen.doclear:
            self.screen.s.clearok(1)
        self.screen.draw_cursor(canvas)
        self.screen.doclear = False
        self.screen.messy = False
        self.screen.dirty = False
        self.screen.refresh()

    def _run_screen_event_loop(self):
        """
        This method is used when the screen does not support using
        external event loops.

        The alarms stored in the SelectEventLoop in self.event_loop 
        are modified by this method.
        """
        next_alarm = None

        while True:
            self.draw_screen()

            if not next_alarm and self.event_loop._alarms:
                next_alarm = heapq.heappop(self.event_loop._alarms)

            keys = None
            while not keys:
                if next_alarm:
                    sec = max(0, next_alarm[0] - time.time())
                    self.screen.set_input_timeouts(sec)
                else:
                    self.screen.set_input_timeouts(None)
                keys, raw = self.screen.get_input(True)
                if not keys and next_alarm: 
                    sec = next_alarm[0] - time.time()
                    if sec <= 0:
                        break

            keys = self.input_filter(keys, raw)
            
            if keys:
                self.process_input(keys)
            
            while next_alarm:
                sec = next_alarm[0] - time.time()
                if sec > 0:
                    break
                tm, callback = next_alarm
                callback()
                
                if self.event_loop._alarms:
                    next_alarm = heapq.heappop(self.event_loop._alarms)
                else:
                    next_alarm = None
            
            if 'window resize' in keys:
                self.screen_size = None

class BufferFill(urwid.SolidFill):
    def render(self, size, focus=False):
        self.size = size
        maxcol, maxrow = size
        return urwid.SolidCanvas(self.fill_char, maxcol, maxrow)

class CommandEdit(urwid.Edit):
    def __init__(self, log, comcb, *args, **kwargs):
        self.log = log
        super(CommandEdit, self).__init__(*args, **kwargs)
        self.comcb = comcb
        self.history = []
        self.pointer = -1
        self.maxcol = 0

    def _get_input(self):
        self._invalidate()
        return self.get_edit_text()
    def _set_input(self, val):
        self._invalidate()
        return self.set_edit_text(val)
    input = property(_get_input, _set_input)

    def _invalidate(self):
        self.log.app.dirty()
        super(CommandEdit, self)._invalidate()

    def update_input(self, size):
        x, y = self.get_cursor_coords(size)
        if self.pointer >= 0:
            self.input = self.history[self.pointer]
        else:
            self.input = ''
        self.move_cursor_to_coords(size, 'right', y)

    def keypress(self, size, key):
        cx, cy = self.get_cursor_coords(size)
        if key=="enter" and self.input:
            i = self.input
            self.history.insert(0, self.input)
            self.input = ''
            self.pointer = -1
            self.comcb(i)
            self.log.app.dirty()
            self.log.app.clear()
        elif key in ('ctrl p',):
            if self.pointer <= len(self.history) - 2:
                self.pointer += 1
                self.pointer = min(len(self.history) - 1, self.pointer)
                self.update_input(size)
        elif key in ('ctrl n',):
            if self.pointer >= 0:
                self.pointer -= 1
                self.pointer = max(-1, self.pointer)
                self.update_input(size)
        elif key in ('ctrl e', 'end'):
            self.move_cursor_to_coords(size, 'right', cy)
        elif key in ('ctrl a', 'home'):
            self.move_cursor_to_coords(size, 'left', cy)
        elif key in ('ctrl f', 'right'):
            if self.edit_pos < len(self.input):
                p = move_next_char(self.input, self.edit_pos, len(self.input))
                self.set_edit_pos(p)
        elif key in ('ctrl b', 'right'):
            if self.edit_pos > 0:
                p = move_prev_char(self.input, 0, self.edit_pos)
                self.set_edit_pos(p)
        else:
            return super(CommandEdit, self).keypress(size, key)

class EaterListBox(urwid.ListBox):
    def __init__(self, app, *args, **kwargs):
        self.app = app
        super(EaterListBox, self).__init__(*args, **kwargs)

    def _invalidate(self):
        self.app.dirty()
        super(EaterListBox, self)._invalidate()


class EaterConsoleLogWidget(urwid.WidgetWrap):
    INTRO = "eater-experiment v0.1 loaded.\n"
    def __init__(self, app, intro=INTRO):
        self.app = app
        self._log = urwid.Text(' ')
        self._listwalker = urwid.SimpleListWalker([self._log])
        self._list = EaterListBox(app, self._listwalker)
        self.display = self._list
        urwid.WidgetWrap.__init__(self, self.display)
            
    def scroll_bottom(self):
        self._list.set_focus(len(self._listwalker) - 1)


    def render(self, size, *args, **kwargs):
        self._size = size
        return self.display.render(size)
        
class EaterConsoleWidget(urwid.WidgetWrap):
    def __init__(self, app):
        self.app = app
        self._log = EaterConsoleLogWidget(app)
        self._cmd = EaterCommandController(app, stdin=self, stdout=self)
        self._input = ('fixed', 1,
                       urwid.Filler(CommandEdit(self._log, self.on_cmd, ">")))
        self.display = urwid.Pile([self._log, self._input])
        urwid.WidgetWrap.__init__(self, self.display)

    def keypress(self, size, key):
        if key in ('page down', 'page up'):
            if key == 'page down':
                return self._log.scroll_bottom()
            elif key == 'page up':
                return self._log.scroll_top()
        return self.display.keypress(size, key)

    def on_cmd(self, line):
        oldin, oldout = sys.stdin, sys.stdout
        buf = cStringIO.StringIO()
        sys.stdin, sys.stdout = buf, buf
        self._cmd.onecmd_plus_hooks(line)
        sys.stdin, sys.stdout = oldin, oldout
        self.write(buf.getvalue())
        self._log._list.set_focus(len(self._log._listwalker) - 1)

    def write(self, string):
        string = string.strip()
        self._log._listwalker.append(urwid.Text(string))

class EaterScreenWidget(urwid.WidgetWrap):
    def __init__(self, app):
        self.buffer = BufferFill(chr(0))
        self.console = EaterConsoleWidget(app)
        self._status = urwid.Text('')
        self.panel = urwid.Columns([self.console,
                                                  urwid.Filler(self._status)])
        
        self.display_widget = urwid.Pile([self.buffer, 
                                     ('fixed', 12, urwid.LineBox(self.panel))])
        urwid.WidgetWrap.__init__(self, self.display_widget)

    def log(self, string):
        self.console.write(string + "\n")

    def status(self, string):
        self._status.set_text(string)

